#!/usr/bin/env python3
"""
双方向エージェント変換・マスターファイル更新・コマンド同期スクリプト

機能:
  1. .cursor/rules/*.mdc ⇔ .claude/agents/*.md の双方向変換
  2. マスターファイル更新（AGENTS.md、CLAUDE.md、.gemini/GEMINI.md、.kiro/steering/KIRO.md）
  3. コマンド同期: .cursor/commands → .codex/prompts, .claude/commands

使用例:
  python scripts/update_agent_master.py                    # デフォルト（変換 + マスター更新 + コマンド同期）
  python scripts/update_agent_master.py --source cursor    # cursor→agents + マスター更新 + コマンド同期
  python scripts/update_agent_master.py --source agents    # agents→cursor のみ
  python scripts/update_agent_master.py --dry-run          # ドライラン（変更なし）
"""

import os
import re
import platform
import argparse
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict

def get_root_directory():
    """
    スクリプトの場所に基づいてプロジェクトのルートディレクトリを取得します。
    このスクリプトが 'scripts' サブディレクトリにあることを前提としています。

    Returns:
        Path: プロジェクトのルートディレクトリのパス。
    """
    # このファイルの絶対パスを取得し、'scripts'ディレクトリの親を取得します
    project_root = Path(__file__).resolve().parent.parent
    print(f"📂 プロジェクトルートを特定: {project_root}")
    return project_root

def parse_frontmatter(content: str) -> Tuple[Dict[str, str], str]:
    """
    フロントマターをパースして辞書と本文を返す
    
    Args:
        content: ファイルの全内容
        
    Returns:
        (フロントマター辞書, 本文)
    """
    frontmatter_pattern = r'^\s*---\s*\n(.*?)\n---\s*\n(.*)'
    match = re.match(frontmatter_pattern, content, re.DOTALL)
    
    if not match:
        return {}, content
    
    frontmatter_content = match.group(1)
    body_content = match.group(2)
    
    # フロントマターをパース
    frontmatter = {}
    for line in frontmatter_content.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"\'')
            frontmatter[key] = value
    
    return frontmatter, body_content

def remove_frontmatter(content):
    """
    Markdown/MDCファイルからYAMLフロントマターを除去します。

    Args:
        content (str): ファイルの全内容。

    Returns:
        str: フロントマターが除去された内容。
    """
    # ファイル先頭の '---' で囲まれたブロックを検索
    frontmatter_pattern = r'^\s*---\s*\n.*?\n---\s*\n'
    cleaned_content = re.sub(frontmatter_pattern, '', content, flags=re.DOTALL)
    
    # 先頭の余分な空白や改行を削除
    return cleaned_content.lstrip()

def create_cursor_frontmatter(name: str, description: str) -> str:
    """
    .cursor/rules形式のフロントマターを作成
    00またはpathを含むファイルは alwaysApply: true を含む3フィールド
    それ以外は description と globs のみの2フィールド
    """
    # 00またはpathを含むファイルはalwaysApply: trueを含める
    if "00" in name or "path" in name.lower():
        return f"""---
description: {description}
globs:
alwaysApply: true
---

"""
    else:
        # 通常のファイルは alwaysApply を含めない
        return f"""---
description: {description}
globs:
---

"""

def create_agent_frontmatter(name: str, description: str) -> str:
    """
    .claude/agents形式のフロントマターを作成
    """
    return f"""---
name: {name}
description: {description}
---

"""

def find_path_reference(master_content):
    """
    マスターファイルの内容から `path_reference` を抽出します。
    ※この関数は現在使用されていませんが、後方互換性のため残しています。

    Args:
        master_content (str): マスターファイルの(フロントマター除去後の)内容。

    Returns:
        str or None: 見つかったパス参照のファイル名。見つからない場合はNone。
    """
    # 'path_reference:' で始まる行を検索し、ファイル名部分を抽出
    match = re.search(r'^path_reference:\s*"?([^"\n]+)"?', master_content, re.MULTILINE)
    if match:
        path_ref = match.group(1).strip()
        print(f"🔗 パス定義ファイルを発見: {path_ref}")
        return path_ref
    return None

def read_file_content(file_path):
    """
    指定されたファイルの内容を読み込み、フロントマターを除去します。

    Args:
        file_path (Path): 読み込むファイルのパス。

    Returns:
        tuple: (ファイル名, フロントマター除去後の内容)。読み込み失敗時は (None, None)。
    """
    try:
        if not file_path.exists():
            print(f"⚠️  ファイルが見つかりません（スキップ）: {file_path}")
            return None, None
            
        content = file_path.read_text(encoding='utf-8')
        cleaned_content = remove_frontmatter(content)
        
        return file_path.name, cleaned_content
    
    except Exception as e:
        print(f"❌ ファイル読み込みエラー {file_path}: {e}")
        return None, None

def create_output_file_if_not_exists(file_path):
    """
    出力ファイルが存在しない場合は、親ディレクトリごと作成します。

    Args:
        file_path (Path): 出力ファイルのパス。
    """
    try:
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.touch()
            print(f"📝 新規ファイル作成: {file_path}")
        else:
            print(f"📄 既存ファイル更新: {file_path}")
            
    except Exception as e:
        print(f"❌ ファイル作成エラー {file_path}: {e}")
        raise

def create_agents_from_mdc():
    """
    mdcファイルを.claude/agentsにコピーしてエージェントファイルとして変換する
    00とpathを含むファイルは.mdcのままフロントマター変更なしでコピー
    さらに、.cursor/commands/agents_commands、.codex/prompts、.claude/commandsにも
    フロントマターを削除したMD形式でコピーする
    """
    project_root = get_root_directory()
    rules_dir = project_root / ".cursor" / "rules"
    agents_dir = project_root / ".claude" / "agents"
    commands_agents_dir = project_root / ".cursor" / "commands" / "agents_commands"
    
    # エージェントディレクトリを作成
    agents_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 エージェントディレクトリ準備完了: {agents_dir}")
    
    # コマンドエージェントディレクトリを作成
    commands_agents_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 コマンドエージェントディレクトリ準備完了: {commands_agents_dir}")
    
    # 既存のエージェントファイルを削除（.mdと.mdcの両方）
    for agent_file in agents_dir.glob("*"):
        if agent_file.suffix in ['.md', '.mdc']:
            try:
                agent_file.unlink()
                print(f"🗑️  削除: {agent_file.name}")
            except Exception as e:
                print(f"⚠️  削除失敗: {agent_file.name}: {e}")
    
    # 既存のコマンドエージェントファイルを削除
    if commands_agents_dir.exists():
        for cmd_file in commands_agents_dir.glob("*.md"):
            try:
                cmd_file.unlink()
                print(f"🗑️  コマンド削除: {cmd_file.name}")
            except Exception as e:
                print(f"⚠️  コマンド削除失敗: {cmd_file.name}: {e}")
    
    # mdcファイルを取得
    mdc_files = list(rules_dir.glob("*.mdc"))
    if not mdc_files:
        print("❌ .mdcファイルが見つかりません")
        return False
    
    print(f"📋 {len(mdc_files)}個の.mdcファイルを発見")
    
    success_count = 0
    for mdc_file in sorted(mdc_files):
        try:
            # ファイル名を処理（拡張子を除去）
            agent_name = mdc_file.stem
            filename = mdc_file.name
            
            # mdcファイルの内容を読み込み
            content = mdc_file.read_text(encoding='utf-8')
            
            # 00、path、pathsを含むファイルは.mdcのままコピー
            if ("00" in filename or "path" in filename.lower()):
                # .mdcファイルとしてそのままコピー
                agent_file = agents_dir / filename  # 拡張子も含めてそのまま
                agent_file.write_text(content, encoding='utf-8')
                print(f"📋 マスターファイルコピー: {filename} (.mdcのまま)")
                success_count += 1
                # コマンドディレクトリにはコピーしない（マスターファイルは除外）
                continue
            
            # 通常のエージェントファイルは.mdに変換
            # フロントマターからdescriptionを抽出
            description = extract_description_from_frontmatter(content)
            
            # フロントマターを除去
            content_without_frontmatter = remove_frontmatter(content)
            
            # 新しいフロントマターを作成
            new_frontmatter = f"""---
name: {agent_name}
description: {description}
---

"""
            
            # 最終的なエージェントファイル内容
            agent_content = new_frontmatter + content_without_frontmatter
            
            # エージェントファイルのパス
            agent_file = agents_dir / f"{agent_name}.md"
            
            # エージェントファイルを書き込み
            agent_file.write_text(agent_content, encoding='utf-8')
            
            print(f"✅ エージェント作成: {agent_name}")
            
            # .cursor/commands/agents_commands にもコピー（フロントマターなし、MD形式）
            cmd_file = commands_agents_dir / f"{agent_name}.md"
            cmd_file.write_text(content_without_frontmatter, encoding='utf-8')
            print(f"📝 コマンド作成 (.cursor/commands/agents_commands): {agent_name}")
            
            success_count += 1
            
        except Exception as e:
            print(f"❌ 変換失敗 {mdc_file.name}: {e}")
    
    print(f"🎯 エージェント作成完了: {success_count}/{len(mdc_files)}")
    return success_count > 0

def sync_commands_to_codex_and_claude(project_root: Path, dry_run: bool = False) -> bool:
    """
    .cursor/commands 全体を .codex/prompts と .claude/commands にコピーする
    """
    source_dir = project_root / ".cursor" / "commands"
    codex_prompts_dir = project_root / ".codex" / "prompts"
    claude_commands_dir = project_root / ".claude" / "commands"
    
    if not source_dir.exists():
        print(f"⚠️  ソースディレクトリが見つかりません: {source_dir}")
        return False
    
    # コピー先ディレクトリを作成
    if not dry_run:
        codex_prompts_dir.mkdir(parents=True, exist_ok=True)
        claude_commands_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Codexプロンプトディレクトリ準備完了: {codex_prompts_dir}")
        print(f"📁 Claudeコマンドディレクトリ準備完了: {claude_commands_dir}")
    
    # コピー先の既存ファイルを削除
    target_dirs = [
        (codex_prompts_dir, ".codex/prompts"),
        (claude_commands_dir, ".claude/commands")
    ]
    
    for target_dir, dir_name in target_dirs:
        if not dry_run and target_dir.exists():
            for existing_file in target_dir.rglob("*"):
                if existing_file.is_file():
                    try:
                        existing_file.unlink()
                        print(f"🗑️  削除 ({dir_name}): {existing_file.relative_to(target_dir)}")
                    except Exception as e:
                        print(f"⚠️  削除失敗 ({dir_name}): {existing_file.name}: {e}")
    
    # .cursor/commands 内のすべてのファイルを再帰的にコピー
    copied_count = 0
    for source_file in source_dir.rglob("*"):
        if source_file.is_file():
            try:
                # ソースファイルの相対パスを取得
                relative_path = source_file.relative_to(source_dir)
                
                # 各コピー先にコピー
                for target_dir, dir_name in target_dirs:
                    target_file = target_dir / relative_path
                    
                    if dry_run:
                        print(f"🔍 [DRY-RUN] コピー予定 ({dir_name}): {relative_path}")
                    else:
                        # 親ディレクトリを作成
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        # ファイルをコピー
                        import shutil
                        shutil.copy2(source_file, target_file)
                        print(f"📋 コピー完了 ({dir_name}): {relative_path}")
                
                copied_count += 1
                
            except Exception as e:
                print(f"❌ コピー失敗 {source_file.name}: {e}")
    
    print(f"🎯 {'[DRY-RUN] ' if dry_run else ''}コマンド同期{'予定' if dry_run else '完了'}: {copied_count}ファイル")
    return copied_count > 0

def extract_description_from_frontmatter(content):
    """
    ファイル内容からフロントマターのdescriptionを抽出
    """
    try:
        frontmatter, _ = parse_frontmatter(content)
        return frontmatter.get('description', 'Agent for handling specific presentation tasks')
    except Exception as e:
        print(f"⚠️  Description抽出エラー: {e}")
        return "Agent for handling specific presentation tasks"

def convert_mdc_paths_to_agent_paths(content):
    """
    コンテンツ内の .mdc ファイル参照を .claude/agents/*.md に変換
    """
    def replace_call_path(match):
        # match.group(1) は action: "call の部分
        # match.group(2) は ファイル名.mdc の部分  
        prefix = match.group(1)
        mdc_filename = match.group(2)
        
        # .mdc を .md に変更し、パスを追加
        if mdc_filename.endswith('.mdc'):
            agent_filename = mdc_filename.replace('.mdc', '.md')
            return f'{prefix}.claude/agents/{agent_filename}'
        
        return match.group(0)
    
    # action: "call ファイル名.mdc パターンを検索・置換
    pattern = r'(action:\s*"call\s+)([^"\s=>]+\.mdc)'
    converted_content = re.sub(pattern, replace_call_path, content)
    
    return converted_content

def convert_agents_to_cursor(project_root: Path, dry_run: bool = False) -> bool:
    """
    .claude/agents/*.md → .cursor/rules/*.mdc 変換
    """
    agents_dir = project_root / ".claude" / "agents"
    rules_dir = project_root / ".cursor" / "rules"
    
    if not agents_dir.exists():
        print(f"❌ .claude/agentsディレクトリが見つかりません: {agents_dir}")
        return False
    
    # ルールディレクトリを作成
    if not dry_run:
        rules_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 ルールディレクトリ準備完了: {rules_dir}")
        
        # 既存の全.mdcファイルを削除（リフレッシュ）
        deleted_count = 0
        for rule_file in rules_dir.glob("*.mdc"):
            try:
                rule_file.unlink()
                print(f"🗑️  削除: {rule_file.name}")
                deleted_count += 1
            except Exception as e:
                print(f"⚠️  削除失敗: {rule_file.name}: {e}")
        
        if deleted_count > 0:
            print(f"🧹 全mdcファイルをリフレッシュ: {deleted_count}個削除")
    
    # .mdファイルと.mdcファイルを取得
    agent_files = list(agents_dir.glob("*.md")) + list(agents_dir.glob("*.mdc"))
    if not agent_files:
        print("❌ .mdまたは.mdcファイルが見つかりません")
        return False
    
    print(f"📋 {len(agent_files)}個のファイルを発見")
    
    success_count = 0
    for agent_file in sorted(agent_files):
        try:
            rule_name = agent_file.stem
            filename = agent_file.name
            
            # ファイル内容を読み込み
            content = agent_file.read_text(encoding='utf-8')
            
            # 00・pathを含むファイル（.mdc）はそのままコピー
            if ("00" in filename or "path" in filename.lower()) and agent_file.suffix == '.mdc':
                rule_file = rules_dir / filename  # 拡張子も含めてそのまま
                
                if dry_run:
                    print(f"🔍 [DRY-RUN] マスターファイルコピー予定: {filename} (.mdcのまま)")
                else:
                    rule_file.write_text(content, encoding='utf-8')
                    print(f"📋 マスターファイルコピー: {filename} (.mdcのまま)")
                success_count += 1
                continue
            
            # 通常の.mdファイルは.mdcに変換
            if agent_file.suffix == '.md':
                frontmatter, body = parse_frontmatter(content)
                description = frontmatter.get('description', 'Rule for handling specific tasks')
                
                # 新しいフロントマターを作成
                new_frontmatter = create_cursor_frontmatter(rule_name, description)
                rule_content = new_frontmatter + body
                
                rule_file = rules_dir / f"{rule_name}.mdc"
                
                if dry_run:
                    print(f"🔍 [DRY-RUN] ルール作成予定: {rule_name}")
                else:
                    rule_file.write_text(rule_content, encoding='utf-8')
                    print(f"✅ ルール作成: {rule_name}")
                success_count += 1
            
        except Exception as e:
            print(f"❌ 変換失敗 {agent_file.name}: {e}")
    
    print(f"🎯 {'[DRY-RUN] ' if dry_run else ''}ルール作成{'予定' if dry_run else '完了'}: {success_count}/{len(agent_files)}")
    return success_count > 0

def create_skills_from_mdc(project_root: Path, dry_run: bool = False) -> bool:
    """
    .cursor/rules/*.mdc → .claude/skills/<skill-name>/SKILL.md 変換
    機能:
    1. フォルダ作成
    2. paths.md の同梱（フロントマター除去）
    3. 使用スクリプトの検出・同梱・パス書き換え
    4. path_reference の書き換え
    """
    import shutil
    
    rules_dir = project_root / ".cursor" / "rules"
    skills_dir = project_root / ".claude" / "skills"
    scripts_origin_dir = project_root / "scripts"
    
    if not rules_dir.exists():
        print(f"❌ .cursor/rulesディレクトリが見つかりません: {rules_dir}")
        return False
    
    # パスファイルを特定 (pmbok_paths.mdcを想定)
    paths_source_file = next(rules_dir.glob("*paths.mdc"), None)
    paths_content = ""
    if paths_source_file:
        paths_content = remove_frontmatter(paths_source_file.read_text(encoding='utf-8'))
    
    mdc_files = list(rules_dir.glob("*.mdc"))
    if not mdc_files:
        print("❌ .mdcファイルが見つかりません")
        return False
        
    print(f"📋 {len(mdc_files)}個の.mdcファイルをスキルへ変換開始")
    
    success_count = 0
    for mdc_file in sorted(mdc_files):
        try:
            filename = mdc_file.name
            stem = mdc_file.stem
            
            # パスファイル自体はスキル化しない（各スキルに同梱されるため）
            if "paths" in filename.lower():
                continue

            # スキル名の決定
            clean_name = re.sub(r'^\d+_', '', stem)
            skill_name = clean_name.replace('_', '-').lower()
            
            # 特別なファイル名の処理
            if "00" in filename:
                # 00_master_rules はスキル化しない
                continue
            
            skill_dir = skills_dir / skill_name
            
            if not dry_run:
                skill_dir.mkdir(parents=True, exist_ok=True)
            
            # --- 1. paths.md の同梱 ---
            if paths_source_file:
                dest_paths = skill_dir / "paths.md"
                if dry_run:
                    print(f"🔍 [DRY-RUN] ({skill_name}) paths.md を同梱")
                else:
                    dest_paths.write_text(paths_content, encoding='utf-8')

            # --- 2. コンテンツの準備 ---
            content = mdc_file.read_text(encoding='utf-8')
            frontmatter_dict, body = parse_frontmatter(content)
            description = frontmatter_dict.get('description', f'{skill_name} skill')
            if not description:
                description = f"Skill for {skill_name}"

            # --- 3. パス参照の書き換え ---
            # path_reference: "pmbok_paths.mdc" -> path_reference: "paths.md"
            body = re.sub(r'path_reference:\s*"?[^"\n]*paths\.mdc"?', 'path_reference: "paths.md"', body)

            # --- 4. スクリプトの検出・同梱・書き換え ---
            # パターン: {{root}}/scripts/xxx.py または scripts/xxx.py
            # 拡張子: .py, .sh, .ps1
            def replace_script_path(match):
                full_match = match.group(0) # マッチ全体 (例: {{root}}/scripts/tasks.py)
                script_name = match.group(1) # ファイル名 (例: tasks.py)
                
                src_script = scripts_origin_dir / script_name
                
                if src_script.exists():
                    # スクリプトをスキル内 scripts/ にコピー
                    skill_scripts_dir = skill_dir / "scripts"
                    if not dry_run:
                        skill_scripts_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_script, skill_scripts_dir / script_name)
                        # print(f"📦 ({skill_name}) スクリプト同梱: {script_name}")
                    else:
                        print(f"🔍 [DRY-RUN] ({skill_name}) スクリプト同梱: {script_name}")
                    
                    # 本文中のパスを相対パスに書き換え
                    return f"scripts/{script_name}"
                else:
                    return full_match

            # 正規表現: ({{root}}/)?scripts/(ファイル名)
            script_pattern = r'(?:\{\{root\}\}/)?scripts/([\w\-]+\.(?:py|sh|ps1))'
            body = re.sub(script_pattern, replace_script_path, body)

            # --- 5. SKILL.md 生成 ---
            new_frontmatter = f"""---
name: {skill_name}
description: {description}
---

"""
            skill_content = new_frontmatter + body
            skill_file = skill_dir / "SKILL.md"
            
            if dry_run:
                print(f"🔍 [DRY-RUN] スキル作成: {skill_name}")
            else:
                skill_file.write_text(skill_content, encoding='utf-8')
                print(f"✅ スキル作成: {skill_name}")
            
            success_count += 1
            
        except Exception as e:
            print(f"❌ スキル変換失敗 {mdc_file.name}: {e}")
            
    print(f"🎯 {'[DRY-RUN] ' if dry_run else ''}スキル作成{'予定' if dry_run else '完了'}: {success_count}")
    return success_count > 0

def strip_always_apply_from_frontmatter(content: str) -> str:
    """
    フロントマターから alwaysApply フィールドを削除
    マスターファイル生成時に使用
    """
    import re

    # フロントマターを検出
    frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.match(frontmatter_pattern, content, re.DOTALL)

    if not match:
        return content

    frontmatter_content = match.group(1)
    body_content = content[match.end():]

    # alwaysApply行を削除
    frontmatter_lines = frontmatter_content.split('\n')
    filtered_lines = [line for line in frontmatter_lines if 'alwaysApply' not in line]

    # 新しいフロントマターを構築
    new_frontmatter = '---\n' + '\n'.join(filtered_lines) + '\n---\n'

    return new_frontmatter + body_content

def update_master_files_only(project_root: Path, dry_run: bool = False) -> bool:
    """
    マスターファイル（CLAUDE.md、AGENTS.md等）の更新のみを実行
    """

    # 最新のルールディレクトリパス
    rules_dir = project_root / ".cursor" / "rules"
    if not rules_dir.exists():
        print(f"❌ ルールディレクトリが見つかりません: .cursor/rules が存在しません。")
        return False

    # 00を含む.mdcファイルとpathを含む.mdcファイルを順序指定で検索
    target_files = []

    # 1. まず00を含むファイルを追加（ルール定義）
    for mdc_file in rules_dir.glob("*.mdc"):
        filename = mdc_file.name
        if "00" in filename:
            target_files.append(mdc_file)
            print(f"🎯 対象ファイル発見（ルール定義）: {filename}")

    # 2. 次にpathを含むファイルを追加（パス定義）
    for mdc_file in rules_dir.glob("*.mdc"):
        filename = mdc_file.name
        if "path" in filename and mdc_file not in target_files:
            target_files.append(mdc_file)
            print(f"🎯 対象ファイル発見（パス定義）: {filename}")

    if not target_files:
        print("❌ 対象ファイル（00を含む.mdcまたはpathを含む.mdc）が見つかりません")
        return agent_success  # エージェント作成が成功していれば部分的成功とする

    output_files = [
        project_root / "CLAUDE.md",
        project_root / "AGENTS.md",
        project_root / ".gemini" / "GEMINI.md",
        project_root / ".kiro" / "steering" / "KIRO.md",
        project_root / ".github" / "copilot-instructions.md"
    ]

    print("\n🔄 エージェントマスターファイル更新スクリプト開始")
    print(f"🖥️  プラットフォーム: {platform.system()}")

    collected_content = []

    for idx, file_path in enumerate(target_files):
        try:
            relative_path = file_path.relative_to(project_root)
            print(f"📖 読み込み中: {relative_path}")
        except ValueError:
            print(f"📖 読み込み中: {file_path}")

        # 最初のファイル（00_master_rules.mdc）はフロントマターを保持するが、alwaysApplyを削除
        if idx == 0:
            try:
                content = file_path.read_text(encoding='utf-8')
                # alwaysApplyを削除
                content = strip_always_apply_from_frontmatter(content)
                filename = file_path.name
                print(f"✅ 読み込み完了（フロントマター保持・alwaysApply削除）: {filename} ({len(content)} 文字)")
                collected_content.append(content)
            except Exception as e:
                print(f"❌ ファイル読み込みエラー {file_path}: {e}")
                continue
        else:
            # それ以外のファイルはフロントマターを削除
            filename, content = read_file_content(file_path)
            if filename and content:
                collected_content.append(content)
                print(f"✅ 読み込み完了: {filename} ({len(content)} 文字)")
            else:
                print(f"⚠️  スキップ: {file_path.name}")
                continue

        # 最後のファイル以外は区切りとして改行を追加
        if file_path != target_files[-1]:
            collected_content.append("\n\n")
    
    if not collected_content:
        print("❌ 処理対象のファイルから内容を読み込めませんでした。")
        return False

    # 収集したコンテンツをエージェントパスに変換
    processed_content = []
    for content in collected_content:
        # call XXX.mdc パターンを .claude/agents/XXX.md に変換
        processed_content.append(convert_mdc_paths_to_agent_paths(content))

    # 収集したコンテンツを結合
    full_content = "".join(processed_content)
    
    success_count = 0
    for output_file in output_files:
        try:
            if dry_run:
                print(f"🔍 [DRY-RUN] 更新予定: {output_file.name}")
            else:
                create_output_file_if_not_exists(output_file)
                output_file.write_text(full_content, encoding='utf-8')
                
                try:
                    relative_path = output_file.relative_to(project_root)
                    print(f"✅ 更新完了: {relative_path}")
                except ValueError:
                    print(f"✅ 更新完了: {output_file}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ {output_file.name}書き込みエラー: {e}")
    
    if success_count > 0:
        print(f"\n📊 総文字数: {len(full_content):,} 文字")
        print(f"📄 処理ファイル数: {len(target_files)}")
        print(f"📝 出力ファイル数: {success_count}/{len(output_files)}")
        master_success = True
    else:
        master_success = False
    
    return success_count > 0

def main():
    """
    スクリプトのエントリーポイント
    """
    parser = argparse.ArgumentParser(description='双方向エージェント変換・マスターファイル更新スクリプト')
    parser.add_argument('--source', choices=['cursor', 'agents'], default='cursor',
                        help='変換方向を指定: cursor (.cursor/rules→.claude/agents + マスター更新) または agents (.claude/agents→.cursor/rules)')
    parser.add_argument('--dry-run', action='store_true',
                        help='実際の変換を行わず、処理内容を表示のみ')
    parser.add_argument('--force', action='store_true',
                        help='確認なしで実行')
    
    args = parser.parse_args()
    
    try:
        project_root = get_root_directory()
        
        if not project_root.exists():
            print(f"❌ プロジェクトルートディレクトリが存在しません: {project_root}")
            return 1
        
        print(f"\n🔄 双方向エージェント変換・マスターファイル更新スクリプト開始")
        print(f"🖥️  プラットフォーム: {platform.system()}")
        print(f"📍 変換方向: {args.source}")
        print(f"🔍 ドライラン: {args.dry_run}")
        
        if not args.force and not args.dry_run:
            print(f"\n⚠️  既存ファイルが上書きされます。続行しますか？ (y/N): ", end="")
            if input().lower() != 'y':
                print("処理を中止しました。")
                return 0
        
        success = False
        
        conversion_success = False
        
        if args.source == 'cursor':
            # cursor→agents変換
            print(f"\n📤 .cursor/rules/*.mdc → .claude/agents/*.md 変換開始")
            if not args.dry_run:
                conversion_success = create_agents_from_mdc()
            else:
                print("🤖 [DRY-RUN] エージェントファイル作成予定")
                conversion_success = True
            
            # cursor→skills変換 (追加機能)
            print(f"\n📤 .cursor/rules/*.mdc → .claude/skills/*/SKILL.md 変換開始")
            skills_success = create_skills_from_mdc(project_root, args.dry_run)
            if not skills_success:
                print("⚠️ スキル変換に失敗したか、ファイルがありませんでした")

        elif args.source == 'agents':
            # agents→cursor変換
            print(f"\n📤 .claude/agents/*.md → .cursor/rules/*.mdc 変換開始")
            conversion_success = convert_agents_to_cursor(project_root, args.dry_run)
        
        # どちらの起点でもマスターファイル更新を実行
        print(f"\n📋 マスターファイル更新開始")
        master_success = update_master_files_only(project_root, args.dry_run)
        
        # コマンド同期: .cursor/commands → .codex/prompts, .claude/commands
        print(f"\n📋 コマンド同期開始")
        command_sync_success = sync_commands_to_codex_and_claude(project_root, args.dry_run)
        
        success = conversion_success and master_success and command_sync_success
        
        if success:
            if args.dry_run:
                print(f"\n🎉 変換処理の確認が完了しました（ドライラン）。")
            else:
                print(f"\n🎉 変換処理が正常に完了しました。")
        else:
            print(f"\n💥 変換処理中にエラーが発生しました。")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  処理が中断されました。")
        return 1
    except Exception as e:
        print(f"\n💥 予期しないエラーが発生しました: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
