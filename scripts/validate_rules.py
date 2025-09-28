#!/usr/bin/env python3
"""Validate .mdc rule files for front matter and path comments."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path.cwd()
RULE_DIR = ROOT / ".cursor" / "rules"

TRIPLE = "---"
PATH_COMMENT_LINES = (
    "<!-- NOTE: 環境に合わせてパスを調整し、必要に応じて記述方法を変更してください -->",
    "# ・{{ }} 内は動的に置換するプレースホルダ変数",
    "# ・`templates.root_dir` に自身のワークスペースパスを設定し、root を派生エージェント用に展開します",
    "# ----",
    "# 0. ルートディレクトリ",
    "# ----",
)


def parse_front_matter(content: str) -> Tuple[Dict[str, str], str]:
    if not content.startswith(TRIPLE):
        raise ValueError("missing leading front matter delimiter")
    parts = content.split(TRIPLE, 2)
    if len(parts) < 3:
        raise ValueError("incomplete front matter block")
    fm_block = parts[1].strip().splitlines()
    body = parts[2]
    fm: Dict[str, str] = {}
    current_key = None
    for line in fm_block:
        if not line.strip():
            continue
        if line.endswith(":") and not line.strip().startswith("#"):
            current_key = line.rstrip(":").strip()
            fm[current_key] = None
        elif ":" in line:
            key, value = line.split(":", 1)
            fm[key.strip()] = value.strip()
            current_key = None
        elif current_key:
            # yaml style continuation (indent)
            fm[current_key] = (fm[current_key] or "") + "\n" + line
        else:
            raise ValueError(f"unexpected line in front matter: {line}")
    return fm, body


def expected_always_true(path: Path) -> bool:
    name = path.name
    return name.startswith("00_") or name.endswith("_paths.mdc")


def check_front_matter(path: Path, content: str) -> List[str]:
    errors: List[str] = []
    try:
        fm, _ = parse_front_matter(content)
    except ValueError as exc:
        errors.append(f"{path}: front matter error → {exc}")
        return errors

    if "description" not in fm:
        errors.append(f"{path}: front matter missing description")
    if "globs" not in fm:
        errors.append(f"{path}: front matter missing globs block")
        return errors

    always_line = fm.get("alwaysApply") or fm.get("alwaysapply")
    if always_line is None:
        errors.append(f"{path}: globs block missing alwaysApply")
    else:
        value = always_line.replace('"', '').strip().lower()
        expected = "true" if expected_always_true(path) else "false"
        if value != expected:
            errors.append(
                f"{path}: alwaysApply should be {expected} but was {always_line.strip()}"
            )
    return errors


def check_path_comments(path: Path, content: str) -> List[str]:
    if not path.name.endswith("_paths.mdc"):
        return []
    missing = [line for line in PATH_COMMENT_LINES if line not in content]
    if missing:
        return [f"{path}: missing required path comment line: {missing[0]!r}"]

    # ensure root line present and concrete
    for line in content.splitlines():
        if line.strip().startswith("root:"):
            root_value = line.split(":", 1)[1].strip().strip('"')
            if "{{" in root_value or root_value in {"", "/"}:
                return [f"{path}: root should be an absolute path, found {root_value!r}"]
            return []
    return [f"{path}: missing root definition under path comment block"]
    return []


def iter_rule_files() -> List[Path]:
    if not RULE_DIR.exists():
        return []
    return sorted(RULE_DIR.glob("*.mdc"))


def validate() -> int:
    errors: List[str] = []
    files = iter_rule_files()
    if not files:
        print("No .cursor/rules/*.mdc files found. Run this script inside an agent directory.")
        return 1

    for file_path in files:
        text = file_path.read_text(encoding="utf-8")
        rel = file_path.relative_to(ROOT)
        errors.extend(check_front_matter(rel, text))
        errors.extend(check_path_comments(rel, text))
    if errors:
        print("Validation failed:\n", "\n".join(errors))
        return 1
    print("All rule files passed validation.")
    return 0


if __name__ == "__main__":
    sys.exit(validate())
