#!/usr/bin/env python3
"""
Skill構造のLint & エラーチェック
SKILL.md のフォーマット、フォルダ構造、必須セクションを検証する

対象:
  - .cursor/skills/
  - .claude/skills/
  - .codex/skills/
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Iterable, Any

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

# ===========================================
# 定数定義
# ===========================================

# SKILL.md フロントマター検出用
FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# 必須フロントマターキー
REQUIRED_FRONTMATTER = ["name", "description"]

# 必須セクション（SKILL.md本文）
REQUIRED_SECTIONS = ["Instructions", "Resources", "Next Action"]

# 必須フォルダ
REQUIRED_FOLDERS = ["assets", "evaluation", "triggers"]

# 環境別のSkillsディレクトリ
SKILL_DIRS = [".cursor/skills", ".claude/skills", ".codex/skills"]


class LintError:
    def __init__(self, file: str, line: int, message: str, severity: str = "error"):
        self.file = file
        self.line = line
        self.message = message
        self.severity = severity

    def __str__(self):
        icon = "❌" if self.severity == "error" else "⚠️"
        if self.line > 0:
            return f"{icon} {self.file}:{self.line}: {self.message}"
        return f"{icon} {self.file}: {self.message}"


# ===========================================
# ユーティリティ関数
# ===========================================

def iter_skill_dirs(roots: Iterable[Path]) -> List[Path]:
    """Skillディレクトリを検索（SKILL.mdを含むディレクトリ）"""
    dirs: List[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for skill_md in sorted(root.glob("*/SKILL.md")):
            dirs.append(skill_md.parent)
    return dirs


def extract_front_matter(content: str) -> Optional[str]:
    """YAMLフロントマターを抽出"""
    match = FRONT_MATTER_RE.match(content)
    if not match:
        return None
    return match.group(1)


def _yaml_error_hint(front_matter: str, exc: Exception) -> Optional[str]:
    """YAMLエラーのヒントを生成"""
    message = str(exc)
    if "mapping values are not allowed" in message:
        return (
            "YAMLの値に `: `（コロン+スペース）が含まれている可能性があります。"
            "該当する値をダブルクォートで囲むか、複数行なら `|` を使ってください。"
        )
    if "could not find expected ':'" in message:
        return (
            "YAMLフロントマターの行が `key: value` 形式になっているか確認してください。"
        )
    if "found character" in message and "cannot start any token" in message:
        return "値の先頭に `*` / `&` / `{` などがある場合はクォートしてください。"

    if re.search(r"^description:\s+.*:\s+.+$", front_matter, flags=re.MULTILINE):
        return (
            "`description:` の値に `: ` が含まれているため YAML として曖昧になっています。"
            "ダブルクォートで囲んでください。"
        )
    return None


# ===========================================
# 検証関数
# ===========================================

def check_frontmatter(skill_dir: Path, content: str) -> List[LintError]:
    """フロントマターを検証"""
    errors: List[LintError] = []
    skill_md = skill_dir / "SKILL.md"

    front_matter = extract_front_matter(content)
    if front_matter is None:
        errors.append(LintError(
            str(skill_md), 1,
            "YAMLフロントマター（先頭の `--- ... ---`）が見つかりません。"
        ))
        return errors

    if yaml is None:
        errors.append(LintError(
            str(skill_md), 0,
            "PyYAML が見つからないため検証できません。`pip install pyyaml` を実行してください。",
            "warning"
        ))
        return errors

    # descriptionにコロンが含まれるがクォートされていない場合を事前検出
    desc_line_match = re.search(r'^description:\s*(.+)$', front_matter, re.MULTILINE)
    if desc_line_match:
        desc_value = desc_line_match.group(1).strip()
        if desc_value and not desc_value.startswith('"') and not desc_value.startswith("'"):
            if ': ' in desc_value or desc_value.endswith(':'):
                errors.append(LintError(
                    str(skill_md), 0,
                    f"description にコロン(`:`)が含まれていますがクォートされていません。"
                    f"→ description: \"{desc_value}\" のようにダブルクォートで囲んでください。"
                ))
                return errors

    try:
        data: Any = yaml.safe_load(front_matter)
    except Exception as exc:
        errors.append(LintError(str(skill_md), 0, f"invalid YAML frontmatter: {exc}"))
        hint = _yaml_error_hint(front_matter, exc)
        if hint:
            errors.append(LintError(str(skill_md), 0, f"ヒント: {hint}", "warning"))
        return errors

    if not isinstance(data, dict):
        errors.append(LintError(
            str(skill_md), 0,
            f"frontmatter が辞書ではありません（type={type(data).__name__}）。"
        ))
        return errors

    # 必須キーの検証
    for key in REQUIRED_FRONTMATTER:
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(LintError(
                str(skill_md), 0,
                f"frontmatter の `{key}` が不正です（空または文字列ではありません）。"
            ))

    return errors


def check_required_sections(skill_dir: Path, content: str) -> List[LintError]:
    """必須セクションの存在を検証"""
    errors: List[LintError] = []
    skill_md = skill_dir / "SKILL.md"

    for section in REQUIRED_SECTIONS:
        # ## Section または # Section の形式を検索
        pattern = rf"^##?\s+{re.escape(section)}\s*$"
        if not re.search(pattern, content, re.MULTILINE):
            errors.append(LintError(
                str(skill_md), 0,
                f"必須セクション `## {section}` が見つかりません。"
            ))

    return errors


def check_required_folders(skill_dir: Path) -> List[LintError]:
    """必須フォルダの存在を検証"""
    errors: List[LintError] = []

    for folder in REQUIRED_FOLDERS:
        folder_path = skill_dir / folder
        if not folder_path.exists():
            errors.append(LintError(
                str(skill_dir), 0,
                f"必須フォルダ `{folder}/` が存在しません。"
            ))
        elif not folder_path.is_dir():
            errors.append(LintError(
                str(skill_dir), 0,
                f"`{folder}` がディレクトリではありません。"
            ))
        elif not any(folder_path.iterdir()):
            errors.append(LintError(
                str(skill_dir), 0,
                f"`{folder}/` が空です。少なくとも1つのファイルが必要です。",
                "warning"
            ))

    return errors


def check_resources_references(skill_dir: Path, content: str) -> List[LintError]:
    """Resourcesセクションの参照整合性を検証"""
    errors: List[LintError] = []
    skill_md = skill_dir / "SKILL.md"

    # Resourcesセクションを抽出
    resources_match = re.search(
        r"^##?\s+Resources\s*\n(.*?)(?=^##?\s+|\Z)",
        content,
        re.MULTILINE | re.DOTALL
    )
    if not resources_match:
        return errors

    resources_content = resources_match.group(1)

    # 相対パス参照を抽出（./assets/xxx.md, ./questions/xxx.md 等）
    path_refs = re.findall(r"\./([^\s\)]+)", resources_content)

    for ref in path_refs:
        ref_path = skill_dir / ref
        if not ref_path.exists():
            # ディレクトリ参照（./scripts/ など）の場合はディレクトリ存在チェック
            if ref.endswith("/"):
                dir_path = skill_dir / ref.rstrip("/")
                if not dir_path.exists():
                    errors.append(LintError(
                        str(skill_md), 0,
                        f"Resources参照 `./{ref}` が存在しません。",
                        "warning"
                    ))
            else:
                errors.append(LintError(
                    str(skill_md), 0,
                    f"Resources参照 `./{ref}` が存在しません。",
                    "warning"
                ))

    return errors


def check_next_action_triggers(skill_dir: Path, content: str) -> List[LintError]:
    """Next Action triggers の整合性を検証"""
    errors: List[LintError] = []
    skill_md = skill_dir / "SKILL.md"

    triggers_file = skill_dir / "triggers" / "next_action_triggers.md"
    if not triggers_file.exists():
        errors.append(LintError(
            str(skill_md), 0,
            "`triggers/next_action_triggers.md` が存在しません。"
        ))
        return errors

    # SKILL.md の Next Action が triggers 参照形式か
    next_action_match = re.search(
        r"^##?\s+Next Action\s*\n(.*?)(?=^##?\s+|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if not next_action_match:
        return errors

    next_action_content = next_action_match.group(1)
    if "triggers: ./triggers/next_action_triggers.md" not in next_action_content:
        errors.append(LintError(
            str(skill_md), 0,
            "Next Action に `- triggers: ./triggers/next_action_triggers.md` がありません。"
        ))

    # Resources から triggers が参照されているか（推奨だが必須扱い）
    resources_match = re.search(
        r"^##?\s+Resources\s*\n(.*?)(?=^##?\s+|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if resources_match:
        resources_content = resources_match.group(1)
        if "triggers: ./triggers/next_action_triggers.md" not in resources_content:
            errors.append(LintError(
                str(skill_md), 0,
                "Resources に `- triggers: ./triggers/next_action_triggers.md` がありません。"
            ))

    return errors


def lint_skill(skill_dir: Path) -> List[LintError]:
    """1つのSkillディレクトリを検証"""
    errors: List[LintError] = []
    skill_md = skill_dir / "SKILL.md"

    # SKILL.mdの存在確認
    if not skill_md.exists():
        errors.append(LintError(
            str(skill_dir), 0,
            "SKILL.md が存在しません。"
        ))
        return errors

    # SKILL.mdの読み込み
    try:
        content = skill_md.read_text(encoding="utf-8")
    except Exception as e:
        errors.append(LintError(
            str(skill_md), 0,
            f"ファイル読み込みエラー: {e}"
        ))
        return errors

    # 各種検証
    errors.extend(check_frontmatter(skill_dir, content))
    errors.extend(check_required_sections(skill_dir, content))
    errors.extend(check_required_folders(skill_dir))
    errors.extend(check_resources_references(skill_dir, content))
    errors.extend(check_next_action_triggers(skill_dir, content))

    return errors


def find_skill_roots(base_path: Path) -> List[Path]:
    """プロジェクトルートからSkillsディレクトリを検索"""
    roots: List[Path] = []
    for skill_dir in SKILL_DIRS:
        full_path = base_path / skill_dir
        if full_path.exists():
            roots.append(full_path)
    return roots


def main():
    parser = argparse.ArgumentParser(description="Skill構造のLint & エラーチェック")
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="チェック対象のパス（プロジェクトルートまたはSkillディレクトリ）"
    )
    parser.add_argument(
        "--warnings",
        action="store_true",
        default=True,
        help="警告も表示（デフォルト有効）"
    )
    parser.add_argument(
        "--no-warnings",
        action="store_true",
        help="警告を非表示"
    )
    args = parser.parse_args()

    if args.no_warnings:
        args.warnings = False

    target = Path(args.path).resolve()

    # Skillディレクトリを検索
    skill_dirs: List[Path] = []

    if (target / "SKILL.md").exists():
        # 単一のSkillディレクトリが指定された場合
        skill_dirs = [target]
    else:
        # プロジェクトルートが指定された場合
        roots = find_skill_roots(target)
        if not roots:
            print("Skills ディレクトリが見つかりません（.cursor/skills, .claude/skills, .codex/skills）")
            sys.exit(0)
        for root in roots:
            skill_dirs.extend(iter_skill_dirs([root]))

    if not skill_dirs:
        print("チェック対象の Skill が見つかりません")
        sys.exit(0)

    # 検証実行
    all_errors: List[LintError] = []
    for skill_dir in skill_dirs:
        errors = lint_skill(skill_dir)
        all_errors.extend(errors)

    # 結果表示
    error_count = sum(1 for e in all_errors if e.severity == "error")
    warning_count = sum(1 for e in all_errors if e.severity == "warning")

    for error in all_errors:
        if error.severity == "error" or args.warnings:
            print(error)

    print()
    print(f"📊 結果: {len(skill_dirs)} Skills, {error_count} エラー, {warning_count} 警告")

    if error_count > 0:
        print("\n📋 必須要素一覧:")
        print(f"  - フロントマター: {', '.join(REQUIRED_FRONTMATTER)}")
        print(f"  - セクション: {', '.join(REQUIRED_SECTIONS)}")
        print(f"  - フォルダ: {', '.join(REQUIRED_FOLDERS)}")

    sys.exit(1 if error_count > 0 else 0)


if __name__ == "__main__":
    main()
