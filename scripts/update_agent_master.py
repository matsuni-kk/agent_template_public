#!/usr/bin/env python3
"""
起点別（Claude / Codex / Cursor）に、skills/commands を他環境へ同期し、
マスターファイル（CLAUDE.md / AGENTS.md / master_rules.mdc）から派生マスター（GEMINI/KIRO等）へ波及するスクリプト

機能:
  1. 起点マスター → 他マスターへ波及（AGENTS.md、CLAUDE.md、.cursor/rules/master_rules.mdc、.gemini/GEMINI.md、.kiro/steering/KIRO.md など）
  2. 起点 skills/commands(prompts) → 他環境へ同期（非破壊上書き）
  3. （任意）Cursor起点時のみ .claude/agents を生成（master_rules）

使用例:
  python scripts/update_agent_master.py --source claude --force
  python scripts/update_agent_master.py --source codex --force
  python scripts/update_agent_master.py --source cursor --force
  python scripts/update_agent_master.py --source cursor --dry-run
"""

import os
import re
import platform
import argparse
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict

def replace_path_reference(content: str, target: str) -> str:
    """
    path_reference の値だけを指定値に統一する（内容の正規化・削除はしない）。

    Args:
        content: 対象テキスト
        target: 置換後（例: "CLAUDE.md", "AGENTS.md", "master_rules.mdc"）
    """
    # 互換: master_rules.mdc / 00_master_rules.mdc / pmbok_paths.mdc / 既に環境名になっているケースもまとめて置換
    return re.sub(
        r'path_reference:\s*"(?:(?:00_)?master_rules\.mdc|pmbok_paths\.mdc|CLAUDE\.md|AGENTS\.md|GEMINI\.md|KIRO\.md|copilot-instructions\.md)"',
        f'path_reference: "{target}"',
        content,
    )


def ensure_cursor_frontmatter(content: str) -> str:
    """
    master_rules.mdc 用のフロントマターを保証する。
    alwaysApply: true を必ず含める。

    Args:
        content: 対象テキスト（フロントマターあり/なしどちらも対応）

    Returns:
        alwaysApply: true を含むフロントマター付きコンテンツ
    """
    frontmatter_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
    match = frontmatter_pattern.match(content)

    if match:
        # 既存フロントマターがある場合
        fm_content = match.group(1)
        body = content[match.end():]

        # alwaysApply が既にあるかチェック
        if re.search(r'^alwaysApply\s*:', fm_content, re.MULTILINE):
            # 値を true に強制
            fm_content = re.sub(
                r'^(alwaysApply\s*:\s*).*$',
                r'\1true',
                fm_content,
                flags=re.MULTILINE
            )
        else:
            # alwaysApply がない場合は先頭に追加
            fm_content = f"alwaysApply: true\n{fm_content}"

        return f"---\n{fm_content}\n---\n{body}"
    else:
        # フロントマターがない場合は新規作成
        return f"---\nalwaysApply: true\ndescription:\nglobs:\n---\n{content}"


def _target_master_for_env(env: str) -> str:
    return "CLAUDE.md" if env == "claude" else "AGENTS.md"

def transform_skill_text(content: str, target_env: str) -> str:
    """
    skills配下のMarkdownを、指定環境の参照に揃える。
    - path_reference を環境別に差し替え
    - skill_resources 等の .{env}/skills/... を環境別に差し替え
    """
    content = replace_path_reference(content, _target_master_for_env(target_env))
    content = re.sub(r'\.(?:cursor|claude|codex)/skills/', f'.{target_env}/skills/', content)
    return content

def sync_skills_between_envs(
    project_root: Path,
    src_env: str,
    dst_env: str,
    dry_run: bool = False,
    mode: str = "merge",
) -> bool:
    """
    src_env の skills ディレクトリを dst_env に同期する。

    mode:
      - merge  : 既存のdstを消さず、同名ファイルのみ上書き（デフォルト）
      - replace: dstのスキルディレクトリを削除してからコピー（破壊的）

    env:
      - cursor: .cursor/skills
      - claude: .claude/skills
      - codex : .codex/skills
    """
    import shutil

    env_to_dir = {
        "cursor": project_root / ".cursor" / "skills",
        "claude": project_root / ".claude" / "skills",
        "codex": project_root / ".codex" / "skills",
    }

    src_dir = env_to_dir.get(src_env)
    dst_dir = env_to_dir.get(dst_env)
    if src_dir is None or dst_dir is None:
        raise ValueError(f"Unknown env: src={src_env}, dst={dst_env}")

    if not src_dir.exists():
        print(f"⚠️ skills同期スキップ: {src_dir} が見つかりません")
        return False
    if mode not in {"merge", "replace"}:
        raise ValueError(f"Unknown skills sync mode: {mode}")

    # 破壊的操作（dstの全削除）の前に、srcに同期可能なファイルがあるか検証
    # srcが空のときにdstだけ消してしまう事故を防ぐ。
    src_files = [p for p in src_dir.rglob("*") if p.is_file()]
    if len(src_files) == 0:
        print(f"❌ skills同期失敗: {src_dir} にファイルがありません（dst={dst_env} は変更しません）")
        return False

    if not dry_run:
        dst_dir.mkdir(parents=True, exist_ok=True)
        if mode == "replace":
            deleted_count = 0
            for skill_subdir in dst_dir.iterdir():
                if skill_subdir.is_dir():
                    shutil.rmtree(skill_subdir)
                    deleted_count += 1
            if deleted_count:
                print(f"🧹 skillsリフレッシュ ({dst_env}): {deleted_count}個削除")

    copied_files = 0
    for src_path in src_files:
        if not src_path.is_file():
            continue
        rel = src_path.relative_to(src_dir)
        dst_path = dst_dir / rel

        if dry_run:
            print(f"🔍 [DRY-RUN] skills同期予定: {src_env} → {dst_env}: {rel}")
            copied_files += 1
            continue

        dst_path.parent.mkdir(parents=True, exist_ok=True)
        if src_path.suffix.lower() in {".md", ".mdc"}:
            text = src_path.read_text(encoding="utf-8")
            dst_path.write_text(transform_skill_text(text, dst_env), encoding="utf-8")
        else:
            shutil.copy2(src_path, dst_path)
        copied_files += 1

    print(f"🎯 skills同期完了: {src_env} → {dst_env} ({mode}): {copied_files}ファイル")
    return copied_files > 0

def sync_skills_group(
    project_root: Path,
    origin: str,
    dry_run: bool = False,
    mode: str = "merge",
) -> bool:
    """
    3グループ（cursor/claude/codex）のskillsを、origin起点で他2つへ同期する。
    """
    if origin not in {"cursor", "claude", "codex"}:
        raise ValueError(f"Unknown skills origin: {origin}")
    if mode not in {"merge", "replace"}:
        raise ValueError(f"Unknown skills sync mode: {mode}")

    ok = True
    for dst in ["cursor", "claude", "codex"]:
        if dst == origin:
            continue
        ok = sync_skills_between_envs(project_root, origin, dst, dry_run, mode=mode) and ok
    return ok

def sync_embedded_skill_scripts(
    project_root: Path,
    dry_run: bool = False,
    envs: list[str] | None = None,
) -> bool:
    """
    scripts/ と commons_scripts/ を大元（single source of truth）として、
    skills配下に埋め込まれた scripts/ の同名ファイルを更新する。

    - 対象: .{claude,codex,cursor}/skills/*/scripts/*
    - ルール: ファイル名（basename）が一致する場合のみ上書き（新規作成はしない）
    - 優先順位: scripts/ > commons_scripts/
    """
    import shutil

    root_scripts_dir = project_root / "scripts"
    root_common_scripts_dir = project_root / "commons_scripts"

    if envs is None:
        envs = ["claude", "codex", "cursor"]

    sources_by_name = {}
    conflict_names = set()

    def index_sources(src_dir: Path, label: str) -> None:
        if not src_dir.exists():
            return
        for p in src_dir.iterdir():
            if not p.is_file():
                continue
            if p.name.startswith("."):
                continue
            existing = sources_by_name.get(p.name)
            if existing is None:
                sources_by_name[p.name] = (p, label)
                continue
            conflict_names.add(p.name)

    # 優先: scripts/ を先に登録し、次に commons_scripts/ を登録（同名は conflict 扱い）
    index_sources(root_scripts_dir, "scripts")
    index_sources(root_common_scripts_dir, "commons_scripts")

    if conflict_names:
        # 競合時は scripts/ を優先しつつ、警告を出す（自動で別名解決はしない）
        print(f"⚠️  埋め込みスクリプト同期: 同名競合が検出されました（scripts優先）: {sorted(conflict_names)}")

    updated = 0
    skipped = 0

    for env in envs:
        skills_dir = project_root / f".{env}" / "skills"
        if not skills_dir.exists():
            continue
        for embedded in skills_dir.glob("*/scripts/*"):
            if not embedded.is_file():
                continue
            source_entry = sources_by_name.get(embedded.name)
            if source_entry is None:
                skipped += 1
                continue
            source_path, source_label = source_entry

            if dry_run:
                print(f"🔍 [DRY-RUN] 埋め込みスクリプト更新予定: {embedded} <= {source_label}/{source_path.name}")
                updated += 1
                continue

            embedded.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(source_path, embedded)
                updated += 1
            except PermissionError as e:
                print(f"⚠️  埋め込みスクリプト同期: 権限不足でスキップ: {embedded} ({e})")
                skipped += 1
            except OSError as e:
                print(f"⚠️  埋め込みスクリプト同期: 書き込み失敗でスキップ: {embedded} ({e})")
                skipped += 1

    if updated == 0 and skipped == 0:
        print("ℹ️  埋め込みスクリプト同期: 対象が見つかりませんでした")
        return True

    print(f"🧩 埋め込みスクリプト同期完了: 更新={updated} / 対象外={skipped}")
    return True

def remove_empty_directories(project_root: Path, target_dir: Path, dry_run: bool = False) -> int:
    """
    target_dir 配下の空ディレクトリを再帰的に削除する（ボトムアップ）。
    - スクリプトの同期/変換で残る空フォルダの掃除用。
    - ファイルが1つでもあれば削除しない。
    """
    if not target_dir.exists() or not target_dir.is_dir():
        return 0

    removed = 0

    # 深い階層から順に処理（子→親）
    dirs = [p for p in target_dir.rglob("*") if p.is_dir()]
    dirs.sort(key=lambda p: len(p.parts), reverse=True)

    ignorable_files = {".gitkeep", ".DS_Store"}

    for d in dirs:
        try:
            entries = list(d.iterdir())
        except Exception:
            continue

        # 空、または「意味のない保持ファイルだけ」のディレクトリを削除対象にする
        meaningful = [e for e in entries if e.name not in ignorable_files]
        if meaningful:
            continue

        if dry_run:
            try:
                rel = d.relative_to(project_root)
            except ValueError:
                rel = d
            print(f"🔍 [DRY-RUN] 空ディレクトリ削除予定: {rel}")
            removed += 1
            continue

        # .gitkeep 等のみがある場合は先に削除してから rmdir
        for e in entries:
            try:
                if e.is_file() and e.name in ignorable_files:
                    e.unlink()
            except Exception:
                pass
        try:
            d.rmdir()
            removed += 1
        except Exception:
            continue

    return removed

def cleanup_empty_dirs_after_run(project_root: Path, dry_run: bool = False) -> int:
    """
    本スクリプトが触りうる主要ディレクトリ配下の空ディレクトリをまとめて削除する。
    """
    targets = [
        project_root / ".codex" / "skills",
        project_root / ".claude" / "skills",
        project_root / ".cursor" / "skills",
        project_root / ".opencode" / "agent",
        project_root / ".codex" / "prompts",
        project_root / ".claude" / "commands",
        project_root / ".cursor" / "commands",
        project_root / ".opencode" / "command",
        project_root / ".claude" / "agents",
        project_root / ".cursor" / "rules",
    ]

    total = 0
    for t in targets:
        total += remove_empty_directories(project_root, t, dry_run=dry_run)

    if total and not dry_run:
        print(f"🧹 空ディレクトリ掃除: {total}個")
    return total

def get_root_directory():
    """
    カレントワーキングディレクトリをプロジェクトのルートディレクトリとして取得します。
    スクリプトは任意のリポジトリから実行できます。

    Returns:
        Path: プロジェクトのルートディレクトリのパス。
    """
    # カレントワーキングディレクトリを使用（実行時のリポジトリを対象にする）
    project_root = Path.cwd()
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
    CursorのMasterrule（master_rules）のみ alwaysApply: true を含める。
    それ以外は description と globs のみ。
    """
    # CursorのMasterruleのみ alwaysApply: true
    # （他のルール/パス辞書等に alwaysApply を波及させない）
    if name in {"master_rules", "00_master_rules"}:
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

def create_agents_from_mdc(preserve_content: bool = True):
    """
    mdcファイルを.claude/agentsにコピーしてエージェントファイルとして変換する
    00とpathを含むファイルは.mdcのままフロントマター変更なしでコピー
    通常ファイルは.claude/agentsに.mdとして出力する。
    ※ Commands（.cursor/.claude/.codex）への「自動生成コマンド」出力は行わない。
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
                agent_file.write_text(replace_path_reference(content, "CLAUDE.md"), encoding='utf-8')
                print(f"📋 マスターファイルコピー: {filename} (.mdcのまま)")
                success_count += 1
                # コマンドディレクトリにはコピーしない（マスターファイルは除外）
                continue
            
            # 通常のエージェントファイルは.mdに変換
            # フロントマターからdescriptionを抽出
            description = extract_description_from_frontmatter(content)

            # フロントマターを除去（Cursor側のルール本文として扱う）
            content_without_frontmatter_original = remove_frontmatter(content)

            if preserve_content:
                # 機能優先（互換）:
                # - 内容はできるだけ同一のまま保つ
                # - 置換するのは path_reference のみ（Claude側は CLAUDE.md）
                content_without_frontmatter = replace_path_reference(
                    content_without_frontmatter_original,
                    "CLAUDE.md",
                )
            else:
                # 旧挙動（変換・削除・正規化を実施）
                content_without_frontmatter_original = normalize_yaml_fields(content_without_frontmatter_original)
                content_without_frontmatter_original = remove_unnecessary_sections(content_without_frontmatter_original)
                # パス変換（.cursor/rules/*.mdc → .claude/agents/*.md 等）
                content_without_frontmatter = convert_mdc_paths_to_agent_paths(content_without_frontmatter_original)

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

def organize_manual_commands(project_root: Path, dry_run: bool = False) -> int:
    """
    .cursor/commands の手動コマンドを commands/ に整理する（01/02分割は廃止）。
    - commands/: 手動作成コマンド（このスクリプト外で管理）
    互換:
    - 既存の 01_commands は commands に統合する
    - 既存の 02_commands は不要なので削除する
    """
    source_dir = project_root / ".cursor" / "commands"
    commands_dir = source_dir / "commands"
    legacy_manual_dir = source_dir / "01_commands"
    legacy_auto_dir = source_dir / "02_commands"

    if not source_dir.exists():
        return 0

    # 既存の 02_commands は不要なので削除
    if legacy_auto_dir.exists():
        if dry_run:
            print(f"🔍 [DRY-RUN] 旧02_commands削除予定: {legacy_auto_dir}")
        else:
            import shutil
            shutil.rmtree(legacy_auto_dir)
            print(f"🗑️ 旧02_commands削除: {legacy_auto_dir}")

    # 既存の 01_commands は commands に統合
    if legacy_manual_dir.exists():
        if dry_run:
            print(f"🔍 [DRY-RUN] 旧01_commands統合予定: {legacy_manual_dir} → {commands_dir}")
        else:
            commands_dir.mkdir(parents=True, exist_ok=True)
            import shutil
            for p in legacy_manual_dir.rglob("*"):
                if p.is_file():
                    rel = p.relative_to(legacy_manual_dir)
                    dst = commands_dir / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(p), str(dst))
            # 空になったら削除（空判定はcleanupでも最終掃除されるが、ここでも試す）
            try:
                legacy_manual_dir.rmdir()
            except Exception:
                pass

    # commands ディレクトリを作成
    if not dry_run:
        commands_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 コマンドディレクトリ準備完了: {commands_dir}")

    moved_count = 0
    # .cursor/commands 直下の .md ファイルのみを対象（サブディレクトリは除外）
    for source_file in source_dir.glob("*.md"):
        if source_file.is_file():
            target_file = commands_dir / source_file.name
            if dry_run:
                print(f"🔍 [DRY-RUN] 移動予定: {source_file.name} → commands/")
            else:
                import shutil
                shutil.move(str(source_file), str(target_file))
                print(f"📦 移動完了: {source_file.name} → commands/")
            moved_count += 1

    if moved_count > 0:
        print(f"🎯 {'[DRY-RUN] ' if dry_run else ''}手動コマンド整理{'予定' if dry_run else '完了'}: {moved_count}ファイル")
    return moved_count


def sync_commands_to_codex_and_claude(project_root: Path, dry_run: bool = False) -> bool:
    """
    .cursor/commands の手動コマンドを .codex/prompts と .claude/commands に同期する。
    - すべてのファイルをフラット配置（サブディレクトリ構造は作成しない）。
    - .codex/prompts/*.md と .claude/commands/*.md に直接配置。
    """
    import shutil

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

    # コピー先の既存ファイルを削除（直下のファイルのみ、サブディレクトリは削除）
    target_dirs = [
        (codex_prompts_dir, ".codex/prompts"),
        (claude_commands_dir, ".claude/commands")
    ]

    for target_dir, dir_name in target_dirs:
        if not dry_run and target_dir.exists():
            # サブディレクトリを削除
            for item in target_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                    print(f"🗑️  削除 ({dir_name}): {item.name}/")
            # ファイルを削除
            for existing_file in target_dir.iterdir():
                if existing_file.is_file():
                    try:
                        existing_file.unlink()
                        print(f"🗑️  削除 ({dir_name}): {existing_file.name}")
                    except Exception as e:
                        print(f"⚠️  削除失敗 ({dir_name}): {existing_file.name}: {e}")

    # ソースディレクトリ直下のファイルをフラットにコピー
    copied_count = 0
    for source_file in source_dir.iterdir():
        if source_file.is_file():
            # ソースファイルの内容を読み込み
            try:
                source_content = source_file.read_text(encoding='utf-8')
            except Exception as e:
                print(f"❌ コピー失敗（read） {source_file.name}: {e}")
                continue

            # 最終更新行を削除（# ・最終更新: などのパターン）
            source_content = re.sub(r'^#\s*・?最終更新.*\n', '', source_content, flags=re.MULTILINE)

            # 各コピー先にコピー（環境別にpath_referenceを変換）
            per_file_success = False
            for target_dir, dir_name in target_dirs:
                target_file = target_dir / source_file.name

                # 環境別にpath_referenceを変換
                if dir_name == ".codex/prompts":
                    target_content = replace_path_reference(source_content, "AGENTS.md")
                else:
                    target_content = replace_path_reference(source_content, "CLAUDE.md")

                if dry_run:
                    print(f"🔍 [DRY-RUN] コピー予定 ({dir_name}): {source_file.name}")
                    per_file_success = True
                    continue

                try:
                    target_file.write_text(target_content, encoding='utf-8')
                    print(f"📋 コピー完了 ({dir_name}): {source_file.name}")
                    per_file_success = True
                except PermissionError as e:
                    # Codex側が保護されている等で失敗しても、Claude側のコピーは継続したい
                    print(f"⚠️  コピー失敗（権限） ({dir_name}): {source_file.name}: {e}")
                except Exception as e:
                    print(f"❌ コピー失敗 ({dir_name}): {source_file.name}: {e}")

            if per_file_success:
                copied_count += 1

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

    対応形式:
    1. 旧形式: action: "call ファイル名.mdc => ..."
    2. v2形式: rule: ".cursor/rules/XX.mdc"
    """
    # 1. 旧形式: action: "call ファイル名.mdc パターン
    def replace_call_path(match):
        prefix = match.group(1)
        mdc_filename = match.group(2)

        if mdc_filename.endswith('.mdc'):
            agent_filename = mdc_filename.replace('.mdc', '.md')
            return f'{prefix}.claude/agents/{agent_filename}'

        return match.group(0)

    pattern_old = r'(action:\s*"call\s+)([^"\s=>]+\.mdc)'
    converted_content = re.sub(pattern_old, replace_call_path, content)

    # 2. v2形式: rule: ".cursor/rules/XX.mdc" パターン
    def replace_rule_path(match):
        prefix = match.group(1)  # 'rule: "'
        mdc_path = match.group(2)  # '.cursor/rules/XX.mdc' or similar

        # パスからファイル名を抽出
        if '/' in mdc_path:
            filename = mdc_path.split('/')[-1]
        else:
            filename = mdc_path

        # .mdc を .md に変更
        if filename.endswith('.mdc'):
            agent_filename = filename.replace('.mdc', '.md')
            return f'{prefix}.claude/agents/{agent_filename}"'

        return match.group(0)

    # rule: ".cursor/rules/XX.mdc" または rule: "XX.mdc" パターン
    pattern_v2 = r'(rule:\s*")([^"]+\.mdc)"'
    converted_content = re.sub(pattern_v2, replace_rule_path, converted_content)

    # 3. path_reference の変換（互換: 00_master_rules / pmbok_paths 等も吸収）
    converted_content = replace_path_reference(converted_content, "CLAUDE.md")

    # 4. .cursor/rules/ → .claude/agents/ （一般的なパス参照）
    converted_content = re.sub(r'\.cursor/rules/', '.claude/agents/', converted_content)

    # 5. .cursor/commands/ → .claude/commands/ （コマンドパス参照）
    converted_content = re.sub(r'\.cursor/commands/', '.claude/commands/', converted_content)

    return converted_content


def normalize_yaml_fields(content: str) -> str:
    """
    YAMLフィールド名を標準スキーマに変換

    変換マッピング（2025-12更新: AI-first最小スキーマ対応）:
    - name → label (ワークフロー項目)
    - step → label (ステップ名)
    - prompt → question (質問項目)
    - action: "execute_shell" + command: "..." → action: "shell: ..."（統合）
    - placeholder, help → 削除（AIが文脈から推論）
    - mandatory → 削除（AIが文脈から推論）
    - message → 削除（冗長、descriptionで代替）

    保持フィールド（削除しない）:
    - key: 質問の識別子
    - label: ワークフローのラベル
    - description: ワークフローの説明
    - question: 質問テキスト
    - action: アクション
    """
    lines = content.splitlines()
    result = []
    pending_shell_action = None  # action: "execute_shell" 行を保持
    pending_shell_indent = 0

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        # action: "execute_shell" パターンを検出
        if re.match(r'^(\s*)action:\s*["\']?execute_shell["\']?\s*$', line):
            pending_shell_action = line
            pending_shell_indent = indent
            continue  # 次のcommand行を待つ

        # command: 行を検出（直前がexecute_shellの場合、統合）
        if pending_shell_action and re.match(r'^\s*command:\s*', stripped):
            # command値を抽出
            command_match = re.match(r'^\s*command:\s*["\']?(.+?)["\']?\s*$', stripped)
            if command_match:
                command_value = command_match.group(1)
                # 統合された action: "shell: ..." 行を生成
                merged_line = ' ' * pending_shell_indent + f'action: "shell: {command_value}"'
                result.append(merged_line)
                pending_shell_action = None
                continue

        # pending_shell_actionがあるのにcommandが来なかった場合はそのまま追加
        if pending_shell_action:
            result.append(pending_shell_action)
            pending_shell_action = None

        # フィールド名の変換
        if ':' in stripped:
            # name: → label: (ワークフロー項目)
            line = re.sub(r'^(\s*-?\s*)name:', r'\1label:', line)
            # step: → label: (ステップ名)
            line = re.sub(r'^(\s*-?\s*)step:', r'\1label:', line)
            # prompt: → question:
            line = re.sub(r'^(\s*-?\s*)prompt:', r'\1question:', line)

            # 削除対象フィールド（不要な冗長フィールド）
            if re.match(r'^\s*-?\s*placeholder:', line):
                continue  # 削除
            if re.match(r'^\s*-?\s*help:', line):
                continue  # 削除
            if re.match(r'^\s*-?\s*mandatory:', line):
                continue  # 削除
            if re.match(r'^\s*-?\s*message:', line):
                continue  # 削除

        result.append(line)

    # 最後にpending_shell_actionが残っていたら追加
    if pending_shell_action:
        result.append(pending_shell_action)

    return '\n'.join(result)


def remove_unnecessary_sections(content: str) -> str:
    """
    不要なセクションを削除する

    削除対象セクション（skills_conversion_spec.md Section 12より）:
    - success_metrics: 計測する仕組みがない（ただし success_metrics_questions は残す）
    - quality_assurance: CLAUDE.mdのprompt_fact_qc_checklistと重複（ただし quality_assurance_questions は残す）
    - xxx_settings: どこからも参照されていない（例: initiating_settings, discovery_settings）
    - integration_points: next_phasesに置換（別途変換が必要だが、まずは削除）
    """
    lines = content.splitlines()
    result = []
    skip_section = False
    skip_indent = 0

    # 削除対象のセクション名パターン
    # _questions や _template で終わるものは除外
    deletion_patterns = [
        r'^(\s*)success_metrics:\s*',          # success_metrics (success_metrics_questions は別)
        r'^(\s*)quality_assurance:\s*',        # quality_assurance (quality_assurance_questions は別)
        r'^(\s*)\w+_settings:\s*',             # xxx_settings (initiating_settings, etc.)
        r'^(\s*)integration_points:\s*',       # integration_points
    ]

    # 除外パターン（削除しない）
    exclude_patterns = [
        r'_questions:',      # xxx_questions は残す
        r'_template:',       # xxx_template は残す
        r'_workflow:',       # xxx_workflow は残す
    ]

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        current_indent = len(line) - len(stripped)

        # スキップ中の場合
        if skip_section:
            # 同じかより浅いインデントで新しいセクションが始まったらスキップ終了
            if stripped and not stripped.startswith('#') and current_indent <= skip_indent:
                # これが新しいセクション（YAMLキー）かどうかチェック
                if re.match(r'^[a-z_]+:', stripped):
                    skip_section = False
                    # この行は次のセクションなので処理を継続
                else:
                    # まだスキップ中
                    continue
            else:
                # まだ削除対象セクションの中
                continue

        # 除外パターンに該当するかチェック（先にチェック）
        is_excluded = False
        for exclude_pattern in exclude_patterns:
            if re.search(exclude_pattern, stripped):
                is_excluded = True
                break

        if is_excluded:
            result.append(line)
            continue

        # 削除対象パターンに該当するかチェック
        is_deletion_target = False
        for pattern in deletion_patterns:
            match = re.match(pattern, line)
            if match:
                is_deletion_target = True
                skip_section = True
                skip_indent = len(match.group(1))  # インデントレベルを記録
                break

        if is_deletion_target:
            continue  # この行を削除

        result.append(line)

    # 連続する空行を2行以下に正規化
    final_result = []
    empty_count = 0
    for line in result:
        if line.strip() == '':
            empty_count += 1
            if empty_count <= 2:
                final_result.append(line)
        else:
            empty_count = 0
            final_result.append(line)

    return '\n'.join(final_result)


def convert_agent_paths_to_mdc_paths(content: str) -> str:
    """
    コンテンツ内の .claude/agents/*.md 参照を .cursor/rules/*.mdc に変換（逆変換）

    対応形式:
    1. rule: ".claude/agents/XX.md" → rule: ".cursor/rules/XX.mdc"
    2. action: "call .claude/agents/XX.md => ..." → action: "call XX.mdc => ..."
    3. path_reference: "CLAUDE.md" → path_reference: "pmbok_paths.mdc"
    4. .claude/skills/xxx/ → .cursor/rules/xxx.mdc
    5. .codex/prompts/ → .cursor/commands/
    6. .codex/skills/ → .cursor/rules/
    """
    converted_content = content

    # 1. rule: ".claude/agents/XX.md" → rule: ".cursor/rules/XX.mdc"
    def replace_agent_rule_path(match):
        prefix = match.group(1)  # 'rule: "'
        agent_path = match.group(2)  # '.claude/agents/XX.md' or similar

        # パスからファイル名を抽出
        if '/' in agent_path:
            filename = agent_path.split('/')[-1]
        else:
            filename = agent_path

        # .md を .mdc に変更
        if filename.endswith('.md'):
            mdc_filename = filename.replace('.md', '.mdc')
            return f'{prefix}.cursor/rules/{mdc_filename}"'

        return match.group(0)

    pattern_agent_rule = r'(rule:\s*")([^"]+\.md)"'
    converted_content = re.sub(pattern_agent_rule, replace_agent_rule_path, converted_content)

    # 2. action: "call .claude/agents/XX.md パターン → action: "call XX.mdc
    def replace_agent_call_path(match):
        prefix = match.group(1)
        agent_path = match.group(2)

        # パスからファイル名を抽出
        if '/' in agent_path:
            filename = agent_path.split('/')[-1]
        else:
            filename = agent_path

        if filename.endswith('.md'):
            mdc_filename = filename.replace('.md', '.mdc')
            return f'{prefix}{mdc_filename}'

        return match.group(0)

    pattern_agent_call = r'(action:\s*"call\s+)([^"\s=>]+\.md)'
    converted_content = re.sub(pattern_agent_call, replace_agent_call_path, converted_content)

    # 3. path_reference: 各環境の値 → Cursor用 "00_master_rules.mdc"
    converted_content = replace_path_reference(converted_content, "00_master_rules.mdc")

    # 4. .claude/skills/xxx-yyy/ パターン → .cursor/rules/XX_xxx_yyy.mdc
    #    （スキル名からルール名への変換は複雑なため、汎用パターンで対応）
    def replace_skills_path(match):
        full_path = match.group(0)
        # .claude/skills/skill-name/... → .cursor/rules/skill-name.mdc
        skill_match = re.search(r'\.claude/skills/([^/]+)', full_path)
        if skill_match:
            skill_name = skill_match.group(1)
            # ハイフンをアンダースコアに変換
            rule_name = skill_name.replace('-', '_')
            return f'.cursor/rules/{rule_name}.mdc'
        return full_path

    converted_content = re.sub(r'\.claude/skills/[^"\s]+', replace_skills_path, converted_content)

    # 5. .codex/prompts/ → .cursor/commands/
    converted_content = re.sub(r'\.codex/prompts/', '.cursor/commands/', converted_content)

    # 6. .codex/skills/ → .cursor/rules/（スキル参照）
    converted_content = re.sub(r'\.codex/skills/', '.cursor/rules/', converted_content)

    # 7. .claude/commands/ → .cursor/commands/
    converted_content = re.sub(r'\.claude/commands/', '.cursor/commands/', converted_content)

    # 8. .claude/agents/xxx.md → .cursor/rules/xxx.mdc （一般的なパス参照）
    def replace_agent_path_general(match):
        full_path = match.group(0)
        # .claude/agents/xxx.md → .cursor/rules/xxx.mdc
        agent_match = re.search(r'\.claude/agents/([^/\s"]+)\.md', full_path)
        if agent_match:
            filename = agent_match.group(1)
            return f'.cursor/rules/{filename}.mdc'
        return full_path

    converted_content = re.sub(r'\.claude/agents/[^\s"]+\.md', replace_agent_path_general, converted_content)

    return converted_content

def convert_agents_to_cursor(project_root: Path, dry_run: bool = False) -> bool:
    """
    .claude/agents/*.md → .cursor/rules/*.mdc 変換
    パス参照も逆変換する
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

            # パス参照を逆変換
            content = convert_agent_paths_to_mdc_paths(content)

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

                # bodyにもパス変換を適用
                body = convert_agent_paths_to_mdc_paths(body)

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


def convert_skills_to_cursor(project_root: Path, dry_run: bool = False) -> bool:
    """
    .claude/skills/*/SKILL.md → .cursor/rules/*.mdc 変換（逆変換）

    機能:
    1. SKILL.md + questions/*.md + assets/*.md を統合して単一の .mdc ファイルに変換
    2. スクリプトを scripts/ または commons_scripts/ にコピー（上書き）
    3. パス参照を .cursor/rules 形式に変換

    Args:
        project_root: プロジェクトルートパス
        dry_run: ドライラン（実際には書き込まない）
    """
    import shutil

    claude_skills_dir = project_root / ".claude" / "skills"
    rules_dir = project_root / ".cursor" / "rules"
    scripts_dir = project_root / "scripts"
    commons_scripts_dir = project_root / "commons_scripts"

    if not claude_skills_dir.exists():
        print(f"⚠️ .claude/skillsディレクトリが見つかりません: {claude_skills_dir}")
        return False

    # スキルディレクトリ一覧を取得
    skill_dirs = [d for d in claude_skills_dir.iterdir() if d.is_dir()]
    if not skill_dirs:
        print("⚠️ スキルディレクトリが見つかりません")
        return False

    print(f"📋 {len(skill_dirs)}個のスキルディレクトリを発見")

    if not dry_run:
        rules_dir.mkdir(parents=True, exist_ok=True)
        scripts_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    script_copy_count = 0

    for skill_dir in sorted(skill_dirs):
        try:
            skill_name = skill_dir.name  # 例: pmbok-executing
            skill_file = skill_dir / "SKILL.md"

            if not skill_file.exists():
                print(f"⚠️ SKILL.mdが見つかりません: {skill_dir.name}")
                continue

            # スキル名からルール名を生成（ハイフン→アンダースコア）
            # 番号プレフィックスの復元を試みる
            rule_name = skill_name.replace('-', '_')

            # 既存のルールファイルから番号プレフィックスを検出
            existing_rules = list(rules_dir.glob(f"*_{rule_name}.mdc")) if rules_dir.exists() else []
            if existing_rules:
                # 既存の番号を使用
                rule_name = existing_rules[0].stem
            else:
                # 番号なしで作成（後でマニュアル調整が必要）
                pass

            # SKILL.md を読み込み
            skill_content = skill_file.read_text(encoding='utf-8')
            frontmatter, body = parse_frontmatter(skill_content)
            description = frontmatter.get('description', f'Rule for {skill_name}')

            # 統合コンテンツを構築
            combined_sections = []
            combined_sections.append(body)

            # questions/*.md を統合
            questions_dir = skill_dir / "questions"
            if questions_dir.exists():
                for q_file in sorted(questions_dir.glob("*.md")):
                    q_content = q_file.read_text(encoding='utf-8')
                    # ヘッダー行を削除（# skill-name - question_name）
                    q_lines = q_content.splitlines()
                    if q_lines and q_lines[0].startswith('#'):
                        q_content = '\n'.join(q_lines[1:]).strip()
                    combined_sections.append(f"\n{q_content}")

            # assets/*.md を統合
            assets_dir = skill_dir / "assets"
            if assets_dir.exists():
                for t_file in sorted(assets_dir.glob("*.md")):
                    t_content = t_file.read_text(encoding='utf-8')
                    # ヘッダー行を削除
                    t_lines = t_content.splitlines()
                    if t_lines and t_lines[0].startswith('#'):
                        t_content = '\n'.join(t_lines[1:]).strip()
                    combined_sections.append(f"\n{t_content}")

            # コンテンツを結合
            combined_content = '\n\n'.join(combined_sections)

            # パス参照を逆変換
            combined_content = convert_agent_paths_to_mdc_paths(combined_content)

            # skill_resources セクションを削除（逆変換時は不要）
            combined_content = re.sub(
                r'# ======== 関連リソース ========\nskill_resources:.*?(?=\n[a-z#]|\Z)',
                '',
                combined_content,
                flags=re.DOTALL
            )

            # 新しいフロントマターを作成
            new_frontmatter = create_cursor_frontmatter(rule_name, description)
            rule_content = new_frontmatter + combined_content.strip()

            rule_file = rules_dir / f"{rule_name}.mdc"

            if dry_run:
                print(f"🔍 [DRY-RUN] ルール作成予定: {rule_name} (from {skill_name})")
            else:
                rule_file.write_text(rule_content, encoding='utf-8')
                print(f"✅ ルール作成: {rule_name} (from {skill_name})")

            success_count += 1

            # scripts/ 内のスクリプトをコピー（上書き）
            skill_scripts_dir = skill_dir / "scripts"
            if skill_scripts_dir.exists():
                for script_file in skill_scripts_dir.glob("*"):
                    if script_file.is_file():
                        # コピー先を決定（commons_scripts に同名ファイルがあればそちら優先）
                        target_in_commons = commons_scripts_dir / script_file.name
                        target_in_scripts = scripts_dir / script_file.name

                        if target_in_commons.exists() or script_file.name.startswith("manage_"):
                            target_file = target_in_commons
                            target_name = f"commons_scripts/{script_file.name}"
                        else:
                            target_file = target_in_scripts
                            target_name = f"scripts/{script_file.name}"

                        if dry_run:
                            print(f"  🔍 [DRY-RUN] スクリプト上書き予定: {target_name}")
                        else:
                            target_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(script_file, target_file)
                            print(f"  📜 スクリプト上書き: {target_name}")
                        script_copy_count += 1

        except Exception as e:
            print(f"❌ スキル変換失敗 {skill_dir.name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"🎯 {'[DRY-RUN] ' if dry_run else ''}スキル→ルール変換{'予定' if dry_run else '完了'}: {success_count}/{len(skill_dirs)}")
    if script_copy_count > 0:
        print(f"📜 {'[DRY-RUN] ' if dry_run else ''}スクリプトコピー{'予定' if dry_run else '完了'}: {script_copy_count}ファイル")

    return success_count > 0


def sync_commands_from_claude_to_cursor(project_root: Path, dry_run: bool = False) -> bool:
    """
    .claude/commands/commands → .cursor/commands/commands 逆同期
    - 01/02分割は廃止（02_commandsは扱わない）
    """
    import shutil

    claude_commands_dir = project_root / ".claude" / "commands"
    cursor_commands_dir = project_root / ".cursor" / "commands"
    src_commands_dir = claude_commands_dir / "commands"
    legacy_src_dir = claude_commands_dir / "01_commands"
    dst_commands_dir = cursor_commands_dir / "commands"

    if not cursor_commands_dir.exists():
        cursor_commands_dir.mkdir(parents=True, exist_ok=True)

    copied_count = 0

    # 互換: 旧 01_commands があればそれを読む
    if not src_commands_dir.exists() and legacy_src_dir.exists():
        src_commands_dir = legacy_src_dir

    # Claude commands → Cursor commands（commands配下のみ）
    if src_commands_dir.exists():
        print(f"\n📥 {src_commands_dir} → {dst_commands_dir} 逆同期開始")
        for source_file in src_commands_dir.rglob("*"):
            if source_file.is_file():
                try:
                    relative_path = source_file.relative_to(src_commands_dir)
                    target_file = dst_commands_dir / relative_path

                    if dry_run:
                        print(f"🔍 [DRY-RUN] 逆同期予定: {relative_path}")
                    else:
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source_file, target_file)
                        print(f"📋 逆同期完了: {relative_path}")

                    copied_count += 1
                except Exception as e:
                    print(f"❌ 逆同期失敗 {source_file.name}: {e}")

    # Cursor側の構造を整える（02_commands削除/commands集約）
    organize_manual_commands(project_root, dry_run)

    print(f"🎯 {'[DRY-RUN] ' if dry_run else ''}コマンド逆同期{'予定' if dry_run else '完了'}: {copied_count}ファイル")
    return copied_count > 0


def convert_codex_skills_to_cursor(project_root: Path, dry_run: bool = False) -> bool:
    """
    .codex/skills/*/SKILL.md → .cursor/rules/*.mdc 変換（逆変換）

    機能:
    1. SKILL.md + questions/*.md + assets/*.md を統合して単一の .mdc ファイルに変換
    2. スクリプトを scripts/ または commons_scripts/ にコピー（上書き）
    3. パス参照を .cursor/rules 形式に変換

    Args:
        project_root: プロジェクトルートパス
        dry_run: ドライラン（実際には書き込まない）
    """
    import shutil

    codex_skills_dir = project_root / ".codex" / "skills"
    rules_dir = project_root / ".cursor" / "rules"
    scripts_dir = project_root / "scripts"
    commons_scripts_dir = project_root / "commons_scripts"

    if not codex_skills_dir.exists():
        print(f"⚠️ .codex/skillsディレクトリが見つかりません: {codex_skills_dir}")
        return False

    # スキルディレクトリ一覧を取得
    skill_dirs = [d for d in codex_skills_dir.iterdir() if d.is_dir()]
    if not skill_dirs:
        print("⚠️ スキルディレクトリが見つかりません")
        return False

    print(f"📋 {len(skill_dirs)}個のCodexスキルディレクトリを発見")

    if not dry_run:
        rules_dir.mkdir(parents=True, exist_ok=True)
        scripts_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    script_copy_count = 0

    for skill_dir in sorted(skill_dirs):
        try:
            skill_name = skill_dir.name  # 例: pmbok-executing
            skill_file = skill_dir / "SKILL.md"

            if not skill_file.exists():
                print(f"⚠️ SKILL.mdが見つかりません: {skill_dir.name}")
                continue

            # スキル名からルール名を生成（ハイフン→アンダースコア）
            rule_name = skill_name.replace('-', '_')

            # 既存のルールファイルから番号プレフィックスを検出
            existing_rules = list(rules_dir.glob(f"*_{rule_name}.mdc")) if rules_dir.exists() else []
            if existing_rules:
                rule_name = existing_rules[0].stem

            # SKILL.md を読み込み
            skill_content = skill_file.read_text(encoding='utf-8')
            frontmatter, body = parse_frontmatter(skill_content)
            description = frontmatter.get('description', f'Rule for {skill_name}')

            # 統合コンテンツを構築
            combined_sections = []
            combined_sections.append(body)

            # questions/*.md を統合
            questions_dir = skill_dir / "questions"
            if questions_dir.exists():
                for q_file in sorted(questions_dir.glob("*.md")):
                    q_content = q_file.read_text(encoding='utf-8')
                    q_lines = q_content.splitlines()
                    if q_lines and q_lines[0].startswith('#'):
                        q_content = '\n'.join(q_lines[1:]).strip()
                    combined_sections.append(f"\n{q_content}")

            # assets/*.md を統合
            assets_dir = skill_dir / "assets"
            if assets_dir.exists():
                for t_file in sorted(assets_dir.glob("*.md")):
                    t_content = t_file.read_text(encoding='utf-8')
                    t_lines = t_content.splitlines()
                    if t_lines and t_lines[0].startswith('#'):
                        t_content = '\n'.join(t_lines[1:]).strip()
                    combined_sections.append(f"\n{t_content}")

            # コンテンツを結合
            combined_content = '\n\n'.join(combined_sections)

            # パス参照を逆変換
            combined_content = convert_agent_paths_to_mdc_paths(combined_content)

            # skill_resources セクションを削除
            combined_content = re.sub(
                r'# ======== 関連リソース ========\nskill_resources:.*?(?=\n[a-z#]|\Z)',
                '',
                combined_content,
                flags=re.DOTALL
            )

            # 新しいフロントマターを作成
            new_frontmatter = create_cursor_frontmatter(rule_name, description)
            rule_content = new_frontmatter + combined_content.strip()

            rule_file = rules_dir / f"{rule_name}.mdc"

            if dry_run:
                print(f"🔍 [DRY-RUN] ルール作成予定: {rule_name} (from codex/{skill_name})")
            else:
                rule_file.write_text(rule_content, encoding='utf-8')
                print(f"✅ ルール作成: {rule_name} (from codex/{skill_name})")

            success_count += 1

            # scripts/ 内のスクリプトをコピー（上書き）
            skill_scripts_dir = skill_dir / "scripts"
            if skill_scripts_dir.exists():
                for script_file in skill_scripts_dir.glob("*"):
                    if script_file.is_file():
                        target_in_commons = commons_scripts_dir / script_file.name
                        target_in_scripts = scripts_dir / script_file.name

                        if target_in_commons.exists() or script_file.name.startswith("manage_"):
                            target_file = target_in_commons
                            target_name = f"commons_scripts/{script_file.name}"
                        else:
                            target_file = target_in_scripts
                            target_name = f"scripts/{script_file.name}"

                        if dry_run:
                            print(f"  🔍 [DRY-RUN] スクリプト上書き予定: {target_name}")
                        else:
                            target_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(script_file, target_file)
                            print(f"  📜 スクリプト上書き: {target_name}")
                        script_copy_count += 1

        except Exception as e:
            print(f"❌ Codexスキル変換失敗 {skill_dir.name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"🎯 {'[DRY-RUN] ' if dry_run else ''}Codexスキル→ルール変換{'予定' if dry_run else '完了'}: {success_count}/{len(skill_dirs)}")
    if script_copy_count > 0:
        print(f"📜 {'[DRY-RUN] ' if dry_run else ''}スクリプトコピー{'予定' if dry_run else '完了'}: {script_copy_count}ファイル")

    return success_count > 0


def sync_codex_prompts_to_cursor(project_root: Path, dry_run: bool = False) -> bool:
    """
    .codex/prompts/commands → .cursor/commands/commands 逆同期
    - 01/02分割は廃止（02_commandsは扱わない）
    """
    import shutil

    codex_prompts_dir = project_root / ".codex" / "prompts"
    cursor_commands_dir = project_root / ".cursor" / "commands"
    src_commands_dir = codex_prompts_dir / "commands"
    legacy_src_dir = codex_prompts_dir / "01_commands"
    dst_commands_dir = cursor_commands_dir / "commands"

    if not codex_prompts_dir.exists():
        print(f"⚠️ .codex/promptsディレクトリが見つかりません: {codex_prompts_dir}")
        return False

    if not cursor_commands_dir.exists():
        cursor_commands_dir.mkdir(parents=True, exist_ok=True)

    copied_count = 0

    # 互換: 旧 01_commands があればそれを読む
    if not src_commands_dir.exists() and legacy_src_dir.exists():
        src_commands_dir = legacy_src_dir

    if not src_commands_dir.exists():
        print(f"⚠️ commandsディレクトリが見つかりません（逆同期スキップ）: {src_commands_dir}")
        return False

    print(f"\n📥 {src_commands_dir} → {dst_commands_dir} 逆同期開始")
    for source_file in src_commands_dir.rglob("*"):
        if source_file.is_file():
            try:
                relative_path = source_file.relative_to(src_commands_dir)
                target_file = dst_commands_dir / relative_path

                if dry_run:
                    print(f"🔍 [DRY-RUN] 逆同期予定: {relative_path}")
                else:
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_file, target_file)
                    print(f"📋 逆同期完了: {relative_path}")

                copied_count += 1
            except Exception as e:
                print(f"❌ 逆同期失敗 {source_file.name}: {e}")

    # Cursor側の構造を整える（02_commands削除/commands集約）
    organize_manual_commands(project_root, dry_run)

    print(f"🎯 {'[DRY-RUN] ' if dry_run else ''}Codexプロンプト逆同期{'予定' if dry_run else '完了'}: {copied_count}ファイル")
    return copied_count > 0

def extract_yaml_sections(content: str) -> Dict[str, Dict]:
    """
    YAML形式のセクション（xxx_template:, xxx_questions: 等）を抽出

    template/questions以外のセクションは「コメント行を含む連続したブロック」として抽出する。
    これにより、ビジュアルヘッダー（# ======== ... ========）やサブヘッダー（# ---- ... ----）、
    コマンド定義（xxx:）などがまとまって保持される。

    マーカーに依存せず、コンテンツのみで判定する。
    セクション名のパターン:
    - xxx_template: → type: template (個別抽出)
    - xxx_questions: → type: questions (個別抽出)
    - その他のトップレベルYAMLキー: → type: default (コメント含めてブロック抽出)

    Args:
        content: MDCファイルの本文

    Returns:
        Dict[section_name, {"content": str, "type": str}]
    """
    sections = {}

    # YAML形式のトップレベルセクションを検出
    # パターン: 行頭の identifier: (値がある場合は | で始まるか、次行にインデント)
    yaml_section_pattern = re.compile(r'^([a-z][a-z0-9_]*):[ \t]*(\|)?[ \t]*$', re.MULTILINE)

    lines = content.splitlines()
    current_section = None
    current_type = "default"
    current_lines = []
    current_indent = None
    # default typeのセクション間のコメント行を蓄積
    pending_comments = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # YAMLセクション開始をチェック
        yaml_match = yaml_section_pattern.match(line)
        if yaml_match:
            # 前のセクションを保存
            if current_section and current_lines:
                sections[current_section] = {
                    "content": "\n".join(current_lines).strip(),
                    "type": current_type
                }

            # 新しいセクション開始
            section_name = yaml_match.group(1)
            has_pipe = yaml_match.group(2) == '|'

            # セクションタイプを判定
            # 注: prompt_で始まるセクションは常にdefault（SKILL.mdに残す）
            # prompt_why_questions, prompt_why_templates等はquestionsやtemplateに分類しない
            if section_name.startswith('prompt_'):
                current_type = "default"
            elif section_name.endswith('_template') or section_name == 'templates':
                current_type = "template"
            elif section_name.endswith('_questions') or section_name == 'questions':
                current_type = "questions"
            else:
                current_type = "default"

            current_section = section_name

            # pending_commentsをセクションの先頭に含める（全type共通）
            # これにより、# ======== 質問 ======== などのヘッダーは
            # questions/templates に含まれ、SKILL.md には残らない
            if pending_comments:
                current_lines = pending_comments + [line]  # YAMLキー行も含める
                pending_comments = []
            else:
                current_lines = [line]

            current_indent = None
            i += 1
            continue

        # 現在セクション内かチェック
        if current_section:
            # インデントされた行またはパイプ後のリテラルブロック
            stripped = line.lstrip()
            indent = len(line) - len(stripped)

            if indent > 0 or line == '':
                # インデントされた行 or 空行は現在のセクションに追加
                if current_indent is None and indent > 0:
                    current_indent = indent
                current_lines.append(line)
            elif stripped == '':
                # 空行はセクション継続
                current_lines.append(line)
            else:
                # 新しいトップレベル要素 → セクション終了
                # このセクションを保存して、行を再処理
                if current_lines:
                    sections[current_section] = {
                        "content": "\n".join(current_lines).strip(),
                        "type": current_type
                    }
                current_section = None
                current_lines = []
                current_indent = None
                continue  # この行を再処理
        else:
            # セクション外のコメント行やビジュアルヘッダーを蓄積
            # 次のdefault typeセクションに含める
            if line.startswith('#') or line.strip() == '':
                pending_comments.append(line)
            else:
                # コメントでない非YAMLな行はクリア
                pending_comments = []

        i += 1

    # 最後のセクションを保存
    if current_section and current_lines:
        sections[current_section] = {
            "content": "\n".join(current_lines).strip(),
            "type": current_type
        }

    return sections


def extract_sections_v2(content: str) -> Dict[str, Dict]:
    """
    セクションを抽出（YAML形式のみ）

    YAML形式（xxx_template:, xxx_questions:等）でセクションを検出。
    ビジュアルヘッダー（# ======== xxx ========）は保持する。

    Args:
        content: MDCファイルの本文（フロントマター除去後）

    Returns:
        Dict[section_name, {"content": str, "type": str}]
        type: "default" | "questions" | "template" | "guide"
    """
    # YAML形式のセクションを抽出
    sections = extract_yaml_sections(content)

    # 有効なセクションのみをフィルタリング
    valid_sections = {}
    for name, data in sections.items():
        if is_valid_section_content(data["content"]):
            valid_sections[name] = data

    return valid_sections


def is_valid_section_name(name: str) -> bool:
    """
    セクション名が有効かどうかを判定

    無効なケース:
    - 空文字列
    - "section_" のみ（マーカー抽出失敗）
    - "section_" + 数字のみ（例: section_8, section__1）
    - アンダースコアのみで構成
    - 極端に短い名前（意味のない抽出）
    - 汎用的すぎる名前（templates, questions等）
    """
    if not name:
        return False
    if name == "section_":
        return False
    # section_ で始まり、残りが数字やアンダースコアのみ
    if name.startswith("section_"):
        rest = name[8:]  # "section_" の後
        if not rest or rest.replace("_", "").replace(" ", "").isdigit() or rest.replace("_", "") == "":
            return False
    if name.replace("_", "") == "":
        return False
    if len(name) < 3 and name != "_preamble":
        return False
    # 数字のみの名前も無効
    if name.replace("_", "").isdigit():
        return False
    # 注: 名前での判定は行わない（templates等も有効なコンテンツがあれば生成する）
    # コンテンツの文字数で判定は is_valid_section_content() で行う
    return True


def is_valid_section_content(content: str) -> bool:
    """
    セクションコンテンツが有効（実質的な内容がある）かどうかを判定

    無効なケース:
    - 空または空白のみ
    - ビジュアルヘッダー行のみ（# ======== ... ========）
    - 行数が3行未満で実質コンテンツなし
    """
    if not content:
        return False

    stripped = content.strip()
    if not stripped:
        return False

    lines = stripped.splitlines()

    # 実質的なコンテンツ行をカウント（ヘッダー行・空行を除く）
    content_lines = []
    for line in lines:
        line_stripped = line.strip()
        # 空行をスキップ
        if not line_stripped:
            continue
        # ビジュアルヘッダー行をスキップ（# ======== ... ========）
        if re.match(r'^#\s*=+.*=+\s*$', line_stripped):
            continue
        content_lines.append(line_stripped)

    # 実質的なコンテンツが1行以上必要
    if len(content_lines) < 1:
        return False

    # 合計文字数も確認（最低10文字）
    # 短いYAMLセクション（command: "xxx", description: "yyy"）も有効とする
    total_chars = sum(len(line) for line in content_lines)
    if total_chars < 10:
        return False

    return True


def split_sections_by_type(sections: Dict[str, Dict]) -> Dict[str, Dict[str, str]]:
    """
    セクションを type に基づいて分割

    Args:
        sections: extract_sections_v2 の出力

    Returns:
        {
            "skill": {section_name: content, ...},  # default + guide をSKILL.mdに統合
            "questions": {section_name: content, ...},
            "template": {section_name: content, ...},
        }
    """
    result = {
        "skill": {},
        "questions": {},
        "template": {},
    }

    for name, data in sections.items():
        # 無効なセクション名をスキップ
        if not is_valid_section_name(name):
            continue

        section_type = data["type"]
        content = data["content"]

        # コンテンツが実質空かどうかを検証
        if not is_valid_section_content(content):
            continue

        if section_type == "questions":
            result["questions"][name] = content
        elif section_type == "template":
            result["template"][name] = content
        elif section_type == "guide":
            # guide セクションも SKILL.md に統合
            result["skill"][name] = content
        else:
            result["skill"][name] = content

    return result


def build_skill_md(skill_name: str, description: str, sections: Dict[str, str], target_env: str = "claude",
                   has_questions: bool = False, has_templates: bool = False, has_scripts: bool = False,
                   question_files: list = None, template_files: list = None, script_files: list = None) -> str:
    """
    SKILL.md ファイルの内容を構築

    Args:
        skill_name: スキル名
        description: 説明文
        sections: スキルセクション（default/guide以外）
        target_env: 対象環境 ("claude" | "codex" | "cursor")
        has_questions: questions/ディレクトリが存在するか
        has_templates: templates/ディレクトリが存在するか
        has_scripts: scripts/ディレクトリが存在するか
        question_files: questionsファイル名リスト
        template_files: templatesファイル名リスト
        script_files: scriptsファイル名リスト

    Returns:
        SKILL.md の内容
    """
    lines = []

    # フロントマター（descriptionはコロンを含む可能性があるためクォート必須）
    lines.append("---")
    lines.append(f"name: {skill_name}")
    # descriptionに含まれる " を \" にエスケープしてダブルクォートで囲む
    escaped_desc = description.replace('"', '\\"')
    lines.append(f'description: "{escaped_desc}"')
    lines.append("---")
    lines.append("")

    # 環境別のpath_reference
    if target_env == "claude":
        lines.append('path_reference: "CLAUDE.md"')
    else:  # codex / cursor
        lines.append('path_reference: "AGENTS.md"')
    lines.append("")

    # 関連リソースのパス参照を追加（フルパス形式）
    # 例: .claude/skills/pmbok-closing/questions/project_closure_questions.md
    skill_base_path = f".{target_env}/skills/{skill_name}"
    if has_questions or has_templates or has_scripts:
        lines.append("# ======== 関連リソース ========")
        lines.append("skill_resources:")
        if has_questions and question_files:
            lines.append("  questions:")
            for qf in question_files:
                lines.append(f'    - "{skill_base_path}/questions/{qf}"')
        if has_templates and template_files:
            lines.append("  assets:")
            for tf in template_files:
                lines.append(f'    - "{skill_base_path}/assets/{tf}"')
        if has_scripts and script_files:
            lines.append("  scripts:")
            for sf in script_files:
                lines.append(f'    - "{skill_base_path}/scripts/{sf}"')
        lines.append("")

    # セクション内容（順序を保持）
    for name, content in sections.items():
        if name == "_preamble":
            # preamble内のpath_reference行を削除してから追加
            cleaned_content = re.sub(r'^path_reference:.*\n?', '', content, flags=re.MULTILINE).strip()
            if cleaned_content:
                lines.append(cleaned_content)
                lines.append("")
        else:
            # YAMLセクション名をキーとして追加
            # contentがインデントされたYAML値の場合、セクション名: を先頭に付ける
            content_stripped = content.strip()
            if content_stripped:
                # contentが既にセクション名（YAMLキー行）を含んでいるかチェック
                # コメント行で始まる場合も、中にYAMLキー行があれば既に含まれている
                yaml_key_pattern = re.compile(rf'^{re.escape(name)}:\s*(\|)?', re.MULTILINE)
                has_yaml_key = yaml_key_pattern.search(content_stripped)

                if has_yaml_key:
                    # 既にYAMLキー行を含んでいる → そのまま出力
                    lines.append(content_stripped)
                else:
                    # YAMLキー行がない → セクション名をYAMLキーとして追加
                    lines.append(f"{name}:")
                    # インデントを追加（各行に2スペース）
                    for line in content_stripped.split('\n'):
                        if line.strip():
                            # 既存のインデントを維持しつつ、最低2スペースを確保
                            if line.startswith('  '):
                                lines.append(line)
                            else:
                                lines.append(f"  {line}")
                        else:
                            lines.append("")
                lines.append("")

    return "\n".join(lines)


def build_single_question_md(skill_name: str, question_name: str, content: str) -> str:
    """
    個別の質問ファイルの内容を構築
    questions/{question_name}.md
    """
    lines = []
    lines.append(f"# {skill_name} - {question_name}")
    lines.append("")
    lines.append(content)
    return "\n".join(lines)


def build_single_template_md(skill_name: str, template_name: str, content: str) -> str:
    """
    個別のテンプレートファイルの内容を構築
    assets/{template_name}.md
    """
    lines = []
    lines.append(f"# {skill_name} - {template_name}")
    lines.append("")
    lines.append(content)
    return "\n".join(lines)


def create_skills_from_mdc(
    project_root: Path,
    dry_run: bool = False,
    target_rule: str = None,
    preserve_content: bool = True,
) -> bool:
    """
    .cursor/rules/*.mdc → .claude/skills/<skill-name>/ 変換（YAML形式検出）
                       → .codex/skills/<skill-name>/ 変換

    機能:
    1. YAML形式セクション（xxx_template:, xxx_questions:等）による抽出
    2. タイプ別ファイル分割（SKILL.md, questions/*.md, assets/*.md）
    3. 使用スクリプトの検出・同梱
    4. .claude/skills と .codex/skills の両方に転記

    Args:
        project_root: プロジェクトルートパス
        dry_run: ドライラン（実際には書き込まない）
        target_rule: 特定ルールのみ変換（例: "07_pmbok_executing"）
    """
    import shutil

    rules_dir = project_root / ".cursor" / "rules"
    cursor_skills_dir = project_root / ".cursor" / "skills"
    claude_skills_dir = project_root / ".claude" / "skills"
    codex_skills_dir = project_root / ".codex" / "skills"
    scripts_origin_dir = project_root / "scripts"

    # 転記先ディレクトリのリスト
    skills_dirs = [
        (cursor_skills_dir, ".cursor/skills"),
        (claude_skills_dir, ".claude/skills"),
        (codex_skills_dir, ".codex/skills"),
    ]

    if not rules_dir.exists():
        print(f"❌ .cursor/rulesディレクトリが見つかりません: {rules_dir}")
        return False

    mdc_files = list(rules_dir.glob("*.mdc"))
    if not mdc_files:
        print("❌ .mdcファイルが見つかりません")
        return False

    # 特定ルールのみ対象にする場合
    if target_rule:
        mdc_files = [f for f in mdc_files if target_rule in f.stem]
        if not mdc_files:
            print(f"❌ 指定ルール '{target_rule}' が見つかりません")
            return False

    print(f"📋 {len(mdc_files)}個の.mdcファイルをスキルへ変換開始（V2: YAML形式検出）")
    print(f"📁 転記先: {', '.join([name for _, name in skills_dirs])}")

    # 既存のスキルディレクトリを全削除（リフレッシュ）
    # スキルは「生成物」扱いとし、毎回の同期で完全一致させる（残骸を残さない）。
    if not dry_run and not target_rule:  # 特定ルール指定時は削除しない
        for skills_dir, dir_name in skills_dirs:
            if skills_dir.exists():
                deleted_count = 0
                for skill_subdir in skills_dir.iterdir():
                    if skill_subdir.is_dir():
                        try:
                            shutil.rmtree(skill_subdir)
                            print(f"🗑️  スキル削除 ({dir_name}): {skill_subdir.name}")
                            deleted_count += 1
                        except Exception as e:
                            print(f"⚠️  スキル削除失敗 ({dir_name}): {skill_subdir.name}: {e}")
                if deleted_count > 0:
                    print(f"🧹 {dir_name} リフレッシュ完了: {deleted_count}個削除")

    success_count = 0
    section_stats = {"total_sections": 0, "questions": 0, "template": 0, "skill": 0}

    for mdc_file in sorted(mdc_files):
        try:
            filename = mdc_file.name
            stem = mdc_file.stem

            # パスファイル自体はスキル化しない
            if "paths" in filename.lower():
                continue

            # 00_master_rules はスキル化しない
            if "00" in filename:
                continue

            # スキル名の決定
            clean_name = re.sub(r'^\d+_', '', stem)
            skill_name = clean_name.replace('_', '-').lower()

            # コンテンツ読み込み
            content = mdc_file.read_text(encoding='utf-8')
            frontmatter_dict, body = parse_frontmatter(content)
            description = frontmatter_dict.get('description', f'{skill_name} skill')
            if not description:
                description = f"Skill for {skill_name}"


            # path_reference 行を環境別に書き換え（後でディレクトリごとに適用）
            # ここでは一旦削除し、各ディレクトリ処理時に追加

            # # @section マーカーでセクション抽出
            sections = extract_sections_v2(body)

            if not sections:
                print(f"⚠️ セクションマーカーなし: {filename}（旧形式として処理）")
                # マーカーがない場合は全体を_preambleとして扱う
                sections = {"_preamble": {"content": body.strip(), "type": "default"}}

            for sec_name in sections:
                content = sections[sec_name]["content"]
                if preserve_content:
                    # 現行のスキル生成では「スキルが読めること（実用）」を優先し、
                    # 正規化・不要セクション削除・パス変換を適用する。
                    # ※ここでの preserve_content は、生成物の構造（分割/統合）を保つ意味で使う。
                    content = convert_mdc_paths_to_agent_paths(content)
                    content = normalize_yaml_fields(content)
                    content = remove_unnecessary_sections(content)
                else:
                    # 旧挙動（同じ）
                    content = convert_mdc_paths_to_agent_paths(content)
                    content = normalize_yaml_fields(content)
                    content = remove_unnecessary_sections(content)
                sections[sec_name]["content"] = content

            # セクション統計
            section_stats["total_sections"] += len(sections)

            # タイプ別に分割
            split_result = split_sections_by_type(sections)

            for sec_type in ["questions", "template", "skill"]:
                section_stats[sec_type] += len(split_result[sec_type])

            # スクリプト検索ディレクトリ（複数）
            scripts_search_dirs = [
                project_root / "scripts",
                project_root / "commons_scripts",
            ]

            # スクリプトをskillフォルダにコピー（パス表記は変えない）
            def copy_referenced_scripts(text: str, target_skill_dir: Path) -> None:
                """テキスト内で参照されているスクリプトをコピー"""
                # scripts/ と commons_scripts/ 両方のパターンをマッチ
                script_pattern = r'(?:scripts|commons_scripts)/([\w\-]+\.(?:py|sh|ps1))'
                matches = re.findall(script_pattern, text)

                for script_name in set(matches):
                    # 複数のディレクトリから検索
                    for search_dir in scripts_search_dirs:
                        src_script = search_dir / script_name
                        if src_script.exists():
                            skill_scripts_dir = target_skill_dir / "scripts"
                            if not dry_run:
                                skill_scripts_dir.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(src_script, skill_scripts_dir / script_name)
                            break

            # --- 各転記先ディレクトリに対して処理 ---
            for skills_dir, dir_name in skills_dirs:
                skill_dir = skills_dir / skill_name

                if not dry_run:
                    skill_dir.mkdir(parents=True, exist_ok=True)

                # 1. 参照されているスクリプトをコピー（パス表記は変えない）
                copied_scripts = []
                for sec_type in split_result:
                    for sec_name in split_result[sec_type]:
                        copy_referenced_scripts(split_result[sec_type][sec_name], skill_dir)

                # コピーされたスクリプトファイル名を取得
                scripts_dir_path = skill_dir / "scripts"
                if scripts_dir_path.exists():
                    copied_scripts = [f.name for f in scripts_dir_path.glob("*") if f.is_file()]

                # 2. ファイルリストを事前に準備
                question_files = [f"{q_name}.md" for q_name in split_result["questions"].keys()]
                template_files = [f"{t_name}.md" for t_name in split_result["template"].keys()]

                # 3. SKILL.md 生成（環境に応じたpath_referenceを設定、リソースパスも追加）
                if dir_name == ".cursor/skills":
                    target_env = "cursor"
                elif dir_name == ".claude/skills":
                    target_env = "claude"
                else:
                    target_env = "codex"
                skill_content = build_skill_md(
                    skill_name, description, split_result["skill"], target_env,
                    has_questions=bool(split_result["questions"]),
                    has_templates=bool(split_result["template"]),
                    has_scripts=bool(copied_scripts),
                    question_files=question_files,
                    template_files=template_files,
                    script_files=copied_scripts
                )
                skill_file = skill_dir / "SKILL.md"

                if dry_run:
                    print(f"  🔍 [DRY-RUN] ({dir_name}) SKILL.md: {len(split_result['skill'])}セクション")
                else:
                    skill_file.write_text(skill_content, encoding='utf-8')

                # 4. questions/*.md 生成（質問セクションがあれば、個別ファイルに分割）
                if split_result["questions"]:
                    questions_dir = skill_dir / "questions"
                    if not dry_run:
                        questions_dir.mkdir(parents=True, exist_ok=True)

                    for q_name, q_content in split_result["questions"].items():
                        q_file_content = build_single_question_md(skill_name, q_name, q_content)
                        q_file = questions_dir / f"{q_name}.md"

                        if dry_run:
                            print(f"  🔍 [DRY-RUN] ({dir_name}) questions/{q_name}.md")
                        else:
                            q_file.write_text(q_file_content, encoding='utf-8')

                # 5. assets/*.md 生成（テンプレートセクションがあれば、個別ファイルに分割）
                if split_result["template"]:
                    assets_dir = skill_dir / "assets"
                    if not dry_run:
                        assets_dir.mkdir(parents=True, exist_ok=True)

                    for t_name, t_content in split_result["template"].items():
                        t_file_content = build_single_template_md(skill_name, t_name, t_content)
                        t_file = assets_dir / f"{t_name}.md"

                        if dry_run:
                            print(f"  🔍 [DRY-RUN] ({dir_name}) assets/{t_name}.md")
                        else:
                            t_file.write_text(t_file_content, encoding='utf-8')

                # 6. 古い paths.md があれば削除（旧バージョンの残骸対応）
                old_paths_md = skill_dir / "paths.md"
                if old_paths_md.exists() and not dry_run:
                    old_paths_md.unlink()
                    print(f"  🗑️  ({dir_name}) 旧paths.md削除: {skill_name}")

            # 成功メッセージ
            files_created = ["SKILL.md"]
            if split_result["questions"]:
                files_created.append(f"questions/({len(split_result['questions'])})")
            if split_result["template"]:
                files_created.append(f"assets/({len(split_result['template'])})")

            if dry_run:
                print(f"✅ [DRY-RUN] {skill_name}: {', '.join(files_created)}")
            else:
                print(f"✅ {skill_name}: {', '.join(files_created)}")

            success_count += 1

        except Exception as e:
            print(f"❌ スキル変換失敗 {mdc_file.name}: {e}")
            import traceback
            traceback.print_exc()

    # サマリー出力
    print(f"\n📊 セクション統計:")
    print(f"   総セクション数: {section_stats['total_sections']}")
    print(f"   - skill (default+guide): {section_stats['skill']}")
    print(f"   - questions: {section_stats['questions']}")
    print(f"   - template: {section_stats['template']}")

    print(f"\n🎯 {'[DRY-RUN] ' if dry_run else ''}スキル作成{'予定' if dry_run else '完了'}: {success_count}（各{len(skills_dirs)}箇所へ転記）")
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

def update_master_files_only(
    project_root: Path,
    dry_run: bool = False,
    preserve_content: bool = True,
    preferred_source_name: str | None = None,
    sync_after_master: bool = True,
) -> bool:
    """
    マスターファイル（CLAUDE.md、AGENTS.md等）の更新のみを実行
    """

    # 最新のルールディレクトリパス
    rules_dir = project_root / ".cursor" / "rules"
    if not rules_dir.exists():
        print(f"❌ ルールディレクトリが見つかりません: .cursor/rules が存在しません。")
        return False

    # すべてのマスターファイル候補を定義
    all_master_files = {
        "AGENTS.md": project_root / "AGENTS.md",
        "CLAUDE.md": project_root / "CLAUDE.md",
        "master_rules.mdc": rules_dir / "master_rules.mdc",
        "GEMINI.md": project_root / ".gemini" / "GEMINI.md",
        "KIRO.md": project_root / ".kiro" / "steering" / "KIRO.md",
        "copilot-instructions.md": project_root / ".github" / "copilot-instructions.md",
    }

    def _pick_master_source(preferred: str | None = None) -> tuple[Path | None, str | None]:
        """
        マスター起点を決める。
        - preferred が指定され、存在すればそれを優先
        - それ以外は、候補（AGENTS/master_rules/CLAUDE）のうち「最終更新が新しい」ものを採用
          ※同率の場合は安定化のための優先順で決定
        """
        candidates = ["AGENTS.md", "master_rules.mdc", "CLAUDE.md"]
        if preferred in candidates:
            p = all_master_files.get(preferred)
            if p and p.exists():
                return p, preferred

        existing = []
        for name in candidates:
            p = all_master_files.get(name)
            if not p or not p.exists():
                continue
            try:
                mtime = p.stat().st_mtime
            except Exception:
                mtime = 0
            existing.append((mtime, name, p))

        if not existing:
            return None, None

        # mtime desc（新しいほど優先）→ 同率なら優先順（AGENTS > master_rules > CLAUDE）
        tie_break_order = {"AGENTS.md": 0, "master_rules.mdc": 1, "CLAUDE.md": 2}
        existing.sort(key=lambda t: (-t[0], tie_break_order.get(t[1], 999)))
        _, name, p = existing[0]
        return p, name

    # 起点ファイルを特定（基本は最終更新が新しいもの、必要なら preferred で強制）
    source_file, source_name = _pick_master_source(preferred=preferred_source_name)
    if source_name:
        print(f"🎯 起点ファイル決定: {source_name}")

    if not source_file:
        print("❌ 起点ファイル（AGENTS.md、master_rules.mdc、CLAUDE.md）が見つかりません")
        return True

    # CursorのMasterruleだけは常に alwaysApply: true を保証（起点ファイルがそれ自身でも適用）
    if source_name == "master_rules.mdc" and not dry_run:
        try:
            original = source_file.read_text(encoding="utf-8")
            ensured = ensure_cursor_frontmatter(original)
            if ensured != original:
                source_file.write_text(ensured, encoding="utf-8")
                print("✅ master_rules.mdc: alwaysApply: true を保証しました")
        except Exception as e:
            print(f"⚠️ master_rules.mdcのalwaysApply保証に失敗: {e}")

    # 起点ファイル以外を出力先とする
    output_files = []
    for name, path in all_master_files.items():
        if name != source_name:  # 起点は除外
            output_files.append(path)
            print(f"📤 出力先: {name}")

    # 起点ファイルをtarget_filesに設定
    target_files = [source_file]

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

    if preserve_content:
        # 互換（機能優先）:
        # - ここでは参照パス（.cursor/.claude/.codex）の大規模書き換えを行わず、
        #   path_reference のみを出力ファイルに合わせて差し替える。
        full_content = "".join(collected_content)
    else:
        # 旧挙動: .mdc参照を .claude/agents/*.md に寄せた上でマスターを生成
        processed_content = []
        for content in collected_content:
            processed_content.append(convert_mdc_paths_to_agent_paths(content))
        full_content = "".join(processed_content)
    
    success_count = 0
    # 出力ファイルごとの path_reference マッピング
    # - CLAUDE.md → "CLAUDE.md"
    # 各ファイルは自分自身を path_reference として持つ
    path_reference_map = {
        "CLAUDE.md": "CLAUDE.md",
        "master_rules.mdc": "master_rules.mdc",
        "GEMINI.md": "GEMINI.md",
        "KIRO.md": "KIRO.md",
        "copilot-instructions.md": "copilot-instructions.md",
    }

    for output_file in output_files:
        try:
            # 各マスターファイルに適切なpath_referenceを設定
            file_content = full_content
            output_name = output_file.name

            # ファイル名に応じて path_reference を適切な参照先に変換
            target_ref = path_reference_map.get(output_name, "AGENTS.md")
            file_content = replace_path_reference(file_content, target_ref)

            # master_rules.mdc の場合は alwaysApply: true を必ず付与
            if output_name == "master_rules.mdc":
                file_content = ensure_cursor_frontmatter(file_content)

            if dry_run:
                print(f"🔍 [DRY-RUN] 更新予定: {output_file.name}")
            else:
                create_output_file_if_not_exists(output_file)
                output_file.write_text(file_content, encoding='utf-8')
                
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

    # 起点プラットフォームに基づき、skills と commands を同期
    # GEMINI/KIRO は対象外（skills/commands を持たない）
    if sync_after_master and source_name in ["CLAUDE.md", "master_rules.mdc", "AGENTS.md"] and not dry_run:
        print(f"\n🔄 {source_name}起点: スキル/コマンドの同期を実行")
        sync_skills_and_commands(project_root, source_name)

    return success_count > 0


def sync_skills_and_commands(project_root: Path, source_platform: str):
    """
    起点プラットフォームから他プラットフォームへ skills と commands を同期する。

    プラットフォーム別ディレクトリマッピング:
    - skills: .claude/skills ↔ .cursor/skills ↔ .codex/skills
    - commands: .claude/commands ↔ .cursor/commands ↔ .codex/prompts
                                                       ↑ codex は "prompts" という名前

    Args:
        project_root: プロジェクトルート
        source_platform: 起点プラットフォーム ("claude", "cursor", "codex")
    """
    import shutil

    # プラットフォーム別ディレクトリマッピング
    # skills/commands は cursor/claude/codex/github 間で同期
    # opencode は別途 agents 同期で処理（.claude/agents → .opencode/agent）
    platform_dirs = {
        "claude": {
            "skills": project_root / ".claude" / "skills",
            "commands": project_root / ".claude" / "commands",
        },
        "cursor": {
            "skills": project_root / ".cursor" / "skills",
            "commands": project_root / ".cursor" / "commands",
        },
        "codex": {
            "skills": project_root / ".codex" / "skills",
            "commands": project_root / ".codex" / "prompts",  # codex は prompts
        },
        "github": {
            "skills": project_root / ".github" / "skills",
            "commands": project_root / ".github" / "prompts",  # github は prompts
        },
    }

    # 起点プラットフォームを特定
    source_name_map = {
        "CLAUDE.md": "claude",
        "master_rules.mdc": "cursor",
        "AGENTS.md": "cursor",  # AGENTS.md は Cursor 系として扱う
    }

    platform = source_name_map.get(source_platform, source_platform)

    if platform not in platform_dirs:
        print(f"⚠️ 不明なプラットフォーム: {platform}、スキル/コマンド同期をスキップ")
        return

    source_dirs = platform_dirs[platform]
    target_platforms = [p for p in platform_dirs.keys() if p != platform]

    print(f"\n📦 スキル/コマンド同期開始 (起点: {platform})")

    # skills 同期
    _sync_directory(
        source_dir=source_dirs["skills"],
        targets=[platform_dirs[tp]["skills"] for tp in target_platforms],
        target_names=[f".{tp}/skills" for tp in target_platforms],
        target_envs=target_platforms,
        source_name=f".{platform}/skills",
        project_root=project_root,
    )

    # commands 同期 (codex/github は prompts へ変換)
    # flat_copy=True: 直下のファイルのみコピー（サブディレクトリは無視）
    _sync_directory(
        source_dir=source_dirs["commands"],
        targets=[platform_dirs[tp]["commands"] for tp in target_platforms],
        target_names=[f".{tp}/{'prompts' if tp in ('codex', 'github') else 'commands'}" for tp in target_platforms],
        target_envs=target_platforms,
        source_name=f".{platform}/{'prompts' if platform in ('codex', 'github') else 'commands'}",
        project_root=project_root,
        flat_copy=True,
    )

    # opencode 同期: .claude/agents → .opencode/agent, .claude/commands → .opencode/command
    # opencode は skills ではなく agents（Subagent定義）を同期する
    claude_agents_dir = project_root / ".claude" / "agents"
    claude_commands_dir = project_root / ".claude" / "commands"
    opencode_agent_dir = project_root / ".opencode" / "agent"
    opencode_command_dir = project_root / ".opencode" / "command"

    # .claude/agents → .opencode/agent
    if claude_agents_dir.exists():
        _sync_directory(
            source_dir=claude_agents_dir,
            targets=[opencode_agent_dir],
            target_names=[".opencode/agent"],
            target_envs=["opencode"],
            source_name=".claude/agents",
            project_root=project_root,
            flat_copy=True,
        )

    # .claude/commands → .opencode/command
    if claude_commands_dir.exists():
        _sync_directory(
            source_dir=claude_commands_dir,
            targets=[opencode_command_dir],
            target_names=[".opencode/command"],
            target_envs=["opencode"],
            source_name=".claude/commands",
            project_root=project_root,
            flat_copy=True,
        )


def _sync_directory(
    source_dir: Path,
    targets: list,
    target_names: list,
    target_envs: list,
    source_name: str,
    project_root: Path,
    flat_copy: bool = False,
):
    """
    単一ディレクトリの同期を実行する内部関数。
    ファイル内の path_reference やスキルパス参照も環境別に変換する。

    Args:
        source_dir: 起点ディレクトリ
        targets: 同期先ディレクトリのリスト
        target_names: 表示用の同期先名のリスト
        target_envs: 同期先の環境名リスト ("claude", "cursor", "codex")
        source_name: 表示用の起点名
        project_root: プロジェクトルート
        flat_copy: Trueの場合、直下のファイルのみコピー（サブディレクトリ無視）
    """
    import shutil

    if not source_dir.exists():
        print(f"  ⚠️ {source_name} が存在しないためスキップ")
        return

    # ソースのファイル一覧を取得
    if flat_copy:
        # 直下のファイルのみ（サブディレクトリは無視）
        source_files = [f for f in source_dir.iterdir() if f.is_file()]
    else:
        # サブディレクトリ含む全ファイル
        source_files = [f for f in source_dir.rglob("*") if f.is_file()]

    file_count = len(source_files)

    if file_count == 0:
        print(f"  ⚠️ {source_name} にファイルがないためスキップ")
        return

    print(f"  📁 {source_name} ({file_count} ファイル)")

    for target_dir, target_name, target_env in zip(targets, target_names, target_envs):
        try:
            # ターゲットディレクトリを完全リフレッシュ（既存を削除してから作成）
            if target_dir.exists():
                import shutil
                shutil.rmtree(target_dir)
                print(f"    🧹 {target_name} をリフレッシュ")
            target_dir.mkdir(parents=True, exist_ok=True)

            # ソースからターゲットへコピー（パス参照を変換）
            copied_count = 0
            for item in source_files:
                if flat_copy:
                    # フラットコピー: ファイル名のみ使用
                    dest = target_dir / item.name
                else:
                    # 構造維持コピー: 相対パスを保持
                    relative = item.relative_to(source_dir)
                    dest = target_dir / relative
                    dest.parent.mkdir(parents=True, exist_ok=True)

                # テキストファイルの場合はパス参照を変換
                if item.suffix in ['.md', '.mdc', '.yaml', '.yml', '.txt']:
                    try:
                        content = item.read_text(encoding='utf-8')
                        # 環境別にパス参照を変換
                        content = transform_skill_text(content, target_env)
                        dest.write_text(content, encoding='utf-8')
                    except Exception:
                        # 読み取りエラーの場合はバイナリコピー
                        shutil.copy2(item, dest)
                else:
                    shutil.copy2(item, dest)
                copied_count += 1

            print(f"    ✅ → {target_name} ({copied_count} ファイル)")
        except Exception as e:
            print(f"    ❌ → {target_name} エラー: {e}")

def main():
    """
    スクリプトのエントリーポイント
    """
    parser = argparse.ArgumentParser(description='起点別の単方向同期 + マスター波及スクリプト')
    parser.add_argument(
        '--source',
        choices=['cursor', 'claude', 'codex'],
        default='claude',
        help='''同期の起点を指定（デフォルト: claude）:
  claude  : .claude/{skills,commands} → .cursor/.codex + マスター波及（CLAUDE.md起点）
  codex   : .codex/{skills,prompts}  → .cursor/.claude + マスター波及（AGENTS.md起点）
  cursor  : .cursor/{skills,commands}→ .claude/.codex + マスター波及（master_rules.mdc起点）''',
    )
    parser.add_argument('--dry-run', action='store_true',
                        help='実際の変換を行わず、処理内容を表示のみ')
    parser.add_argument('--force', action='store_true',
                        help='確認なしで実行')
    parser.add_argument(
        '--legacy-transform',
        action='store_true',
        help='旧来の正規化/不要セクション削除/パス書き換えを有効化（互換より変換優先）',
    )
    # 互換（過去の変換仕様）: 現状は preserve_content のみ切替に使用

    args = parser.parse_args()

    # --source が未指定の場合は選択を促す
    if args.source is None:
        print("\n⚠️  起点（--source）が指定されていません。")
        print("現在編集しているファイル群を起点として指定してください:\n")
        print("  --source cursor : Cursor (.cursor/) を起点に他環境へ同期")
        print("  --source claude : Claude (.claude/) を起点に他環境へ同期")
        print("  --source codex  : Codex (.codex/) を起点に他環境へ同期")
        print("\n例: python scripts/update_agent_master.py --source cursor --force")
        return 1

    try:
        project_root = get_root_directory()

        if not project_root.exists():
            print(f"❌ プロジェクトルートディレクトリが存在しません: {project_root}")
            return 1

        print(f"\n🔄 起点別の同期・マスター波及スクリプト開始")
        print(f"🖥️  プラットフォーム: {platform.system()}")
        print(f"📍 変換方向: {args.source}")
        print(f"🔍 ドライラン: {args.dry_run}")
        preserve_content = not args.legacy_transform

        if not args.force and not args.dry_run:
            print(f"\n⚠️  既存ファイルが上書きされます。続行しますか？ (y/N): ", end="")
            if input().lower() != 'y':
                print("処理を中止しました。")
                return 0

        success = False

        def run_simple(origin: str) -> bool:
            """
            Claude / Codex / Cursor を起点に、他環境へ同期する。
            - 先にマスター波及（起点マスターを明示）
            - 次に skills/commands(prompts) を同期（非破壊上書き）
            - 最後に埋め込みスクリプトを更新（codexは権限事情で除外）
            """
            preferred_master = {
                "claude": "CLAUDE.md",
                "codex": "AGENTS.md",
                "cursor": "master_rules.mdc",
            }[origin]

            print(f"\n📋 マスターファイル更新（起点: {preferred_master}）")
            master_ok = update_master_files_only(
                project_root,
                args.dry_run,
                preserve_content=preserve_content,
                preferred_source_name=preferred_master,
                sync_after_master=False,
            )

            if args.dry_run:
                print(f"\n🔍 [DRY-RUN] {origin}起点: スキル/コマンドの同期予定")
                sync_ok = True
            else:
                sync_skills_and_commands(project_root, origin)
                sync_ok = True

            agents_ok = True
            if origin == "cursor":
                # Cursor起点の場合のみ、Claude側の agents（master_rules）を生成して揃える
                if args.dry_run:
                    print("\n🤖 [DRY-RUN] Cursor起点: .cursor/rules → .claude/agents 同期予定")
                else:
                    agents_ok = create_agents_from_mdc(preserve_content=preserve_content)

            print(f"\n🧩 埋め込みスクリプト同期開始（scripts/ + commons_scripts/ → skills/*/scripts）")
            embedded_ok = sync_embedded_skill_scripts(project_root, args.dry_run, envs=["claude", "cursor"])

            return master_ok and sync_ok and agents_ok and embedded_ok

        if args.source == 'claude':
            print(f"\n📥 Claude起点: .claude/commands, .claude/skills → .cursor/.codex")
            success = run_simple("claude")
        elif args.source == 'codex':
            print(f"\n📥 Codex起点: .codex/prompts, .codex/skills → .cursor/.claude")
            success = run_simple("codex")
        elif args.source == 'cursor':
            print(f"\n📥 Cursor起点: .cursor/commands, .cursor/skills → .claude/.codex")
            success = run_simple("cursor")

        if success:
            if args.dry_run:
                print(f"\n🎉 変換処理の確認が完了しました（ドライラン）。")
            else:
                print(f"\n🎉 変換処理が正常に完了しました。")
            print(f"\n🧹 空ディレクトリ掃除開始")
            cleanup_empty_dirs_after_run(project_root, dry_run=args.dry_run)
        else:
            print(f"\n💥 変換処理中にエラーが発生しました。")
            return 1

    except KeyboardInterrupt:
        print("\n⚠️  処理が中断されました。")
        return 1
    except Exception as e:
        print(f"\n💥 予期しないエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
