#!/usr/bin/env python3
"""
双方向エージェント変換・マスターファイル更新スクリプト
.cursor/rules/*.mdc ⇔ .claude/agents/*.md の双方向変換、および
マスターとなる .mdc ファイル群の内容を抽出し、結合して AGENTS.md、CLAUDE.md、.gemini/GEMINI.md、.kiro/steering/KIRO.md に書き込みます。

使用例:
python scripts/update_agent_master.py                    # デフォルト（cursor→agents + マスター更新）
python scripts/update_agent_master.py --source cursor    # cursor→agents + マスター更新
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
    """
    # 00またはpathを含むファイルはalwaysApply: true、それ以外はfalse
    always_apply = "true" if ("00" in name or "path" in name.lower()) else "false"
    
    return f"""---
description: {description}
globs: 
alwaysApply: {always_apply}
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
    """
    project_root = get_root_directory()
    rules_dir = project_root / ".cursor" / "rules"
    agents_dir = project_root / ".claude" / "agents"
    
    # エージェントディレクトリを作成
    agents_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 エージェントディレクトリ準備完了: {agents_dir}")
    
    # 既存のエージェントファイルを削除（.mdと.mdcの両方）
    for agent_file in agents_dir.glob("*"):
        if agent_file.suffix in ['.md', '.mdc']:
            try:
                agent_file.unlink()
                print(f"🗑️  削除: {agent_file.name}")
            except Exception as e:
                print(f"⚠️  削除失敗: {agent_file.name}: {e}")
    
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
            success_count += 1
            
        except Exception as e:
            print(f"❌ 変換失敗 {mdc_file.name}: {e}")
    
    print(f"🎯 エージェント作成完了: {success_count}/{len(mdc_files)}")
    return success_count > 0

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
    
    for file_path in target_files:
        try:
            relative_path = file_path.relative_to(project_root)
            print(f"📖 読み込み中: {relative_path}")
        except ValueError:
            print(f"📖 読み込み中: {file_path}")
        
        filename, content = read_file_content(file_path)
        
        if filename and content:
            collected_content.append(content)
            # 最後のファイル以外は区切りとして改行を追加
            if file_path != target_files[-1]:
                collected_content.append("\n\n")
            print(f"✅ 読み込み完了: {filename} ({len(content)} 文字)")
        else:
            print(f"⚠️  スキップ: {file_path.name}")
    
    if not collected_content:
        print("❌ 処理対象のファイルから内容を読み込めませんでした。")
        return False
    
    # 警告メッセージを作成
    warning_message = "# ⚠️ 重要: このファイルは自動生成されています\n"
    warning_message += "# ルールを修正する場合は .cursor/rules ディレクトリ内の .mdc ファイルを編集してください\n"
    warning_message += "# 直接このファイルを編集しないでください - 変更は上書きされます\n\n"
    
    # 収集したコンテンツをエージェントパスに変換
    processed_content = []
    for content in collected_content:
        # call XXX.mdc パターンを .claude/agents/XXX.md に変換
        processed_content.append(convert_mdc_paths_to_agent_paths(content))
    
    # 警告メッセージと収集したコンテンツを結合
    full_content = warning_message + "".join(processed_content)
    
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
        elif args.source == 'agents':
            # agents→cursor変換
            print(f"\n📤 .claude/agents/*.md → .cursor/rules/*.mdc 変換開始")
            conversion_success = convert_agents_to_cursor(project_root, args.dry_run)
        
        # どちらの起点でもマスターファイル更新を実行
        print(f"\n📋 マスターファイル更新開始")
        master_success = update_master_files_only(project_root, args.dry_run)
        
        success = conversion_success and master_success
        
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
