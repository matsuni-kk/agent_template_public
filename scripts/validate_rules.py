#!/usr/bin/env python3
"""Validate .mdc rule files for front matter, path comments, and master_triggers."""

from __future__ import annotations

import re
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

# master_triggers の必須フィールド（3フィールドのみ）
REQUIRED_MASTER_TRIGGER_FIELDS = {"trigger", "rule", "description"}

# 可読性のための区切り線（AGENTS.md / CLAUDE.md で要求）
MASTER_PHASE_SEPARATOR = "#============================"
MASTER_GROUP_SEPARATOR = "#--------------------------------------------"


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


def check_master_triggers_format(path: Path, content: str) -> List[str]:
    """00_master_rules.mdc の master_triggers が trigger/rule/description の3フィールド形式かをチェック"""
    if path.name != "00_master_rules.mdc":
        return []

    errors: List[str] = []
    lines = content.splitlines()
    try:
        start_idx = next(i for i, line in enumerate(lines) if line.strip() == "master_triggers:")
    except StopIteration:
        return [
            f"{path}: master_triggers セクションが見つかりません。\n"
            f"  【修正方法】00_master_rules.mdc に master_triggers: を追加し、3フィールド形式で記述してください:\n"
            f"  - trigger: \"(例|... )\"\n"
            f"    rule: \".cursor/rules/01_xxx.mdc\"\n"
            f"    description: \"説明\""
        ]

    # `master_triggers:` 以降、コードフェンスが出たらそこまでを対象にする（例示のYAMLが混在する場合の誤検知回避）
    end_idx = len(lines)
    for i in range(start_idx + 1, len(lines)):
        if lines[i].lstrip().startswith("```"):
            end_idx = i
            break

    def parse_value(line: str) -> str:
        raw = line.split(":", 1)[1].strip()
        if raw.startswith(("'", '"')) and raw.endswith(("'", '"')) and len(raw) >= 2:
            return raw[1:-1]
        return raw

    item_count = 0
    i = start_idx + 1
    while i < end_idx:
        line = lines[i]
        if re.match(r"^\s*-\s+trigger:\s*", line):
            item_count += 1
            keys = {"trigger"}
            rule_value = ""
            description_value = ""

            i += 1
            while i < end_idx and not re.match(r"^\s*-\s+trigger:\s*", lines[i]):
                cur = lines[i]
                if not cur.strip() or cur.lstrip().startswith("#"):
                    i += 1
                    continue

                key_match = re.match(r"^\s+([A-Za-z_][A-Za-z0-9_]*):\s*", cur)
                if key_match:
                    key = key_match.group(1)
                    keys.add(key)
                    if key == "rule":
                        rule_value = parse_value(cur)
                    if key == "description":
                        description_value = parse_value(cur)
                i += 1

            missing = REQUIRED_MASTER_TRIGGER_FIELDS - keys
            extra = keys - REQUIRED_MASTER_TRIGGER_FIELDS
            if missing:
                errors.append(
                    f"{path}: master_triggers の項目に必須フィールドが不足しています: {sorted(missing)}\n"
                    f"  【修正方法】各項目は trigger/rule/description の3フィールドのみで記述してください。"
                )
            if extra:
                errors.append(
                    f"{path}: master_triggers の項目に不要フィールドがあります: {sorted(extra)}\n"
                    f"  【修正方法】priority/steps などは廃止されているため削除してください。"
                )
            if rule_value and (not rule_value.startswith(".cursor/rules/") or not rule_value.endswith(".mdc")):
                errors.append(
                    f"{path}: master_triggers の rule が不正です。現在値: {rule_value}\n"
                    f"  【修正方法】.cursor/rules/*.mdc 形式にしてください。"
                )
            if not description_value.strip():
                errors.append(
                    f"{path}: master_triggers の description が空です。\n"
                    f"  【修正方法】処理内容の簡潔な説明を記載してください。"
                )
            continue

        i += 1

    if item_count == 0:
        errors.append(
            f"{path}: master_triggers のトリガー定義が見つかりません。\n"
            f"  【修正方法】trigger/rule/description の3フィールド形式で1つ以上定義してください。"
        )

    return errors


def check_master_triggers_structure(path: Path, content: str) -> List[str]:
    """00_master_rules.mdc の master_triggers に可読性用セクション区切りがあるかをチェック"""
    if path.name != "00_master_rules.mdc":
        return []

    errors: List[str] = []
    lines = content.splitlines()
    try:
        start_idx = next(i for i, line in enumerate(lines) if line.strip() == "master_triggers:")
    except StopIteration:
        return []

    # `master_triggers:` 以降、コードフェンスが出たらそこまでを対象にする（例示のYAMLが混在する場合の誤検知回避）
    end_idx = len(lines)
    for i in range(start_idx + 1, len(lines)):
        if lines[i].lstrip().startswith("```"):
            end_idx = i
            break

    seen_phase = False
    current_group_name = None
    current_group_has_trigger = False
    phase_header_count = 0
    group_header_count = 0
    trigger_count = 0

    def next_nonempty_index(from_idx: int):
        j = from_idx
        while j < end_idx and not lines[j].strip():
            j += 1
        return j if j < end_idx else None

    i = start_idx + 1
    while i < end_idx:
        line = lines[i].strip()

        if line == MASTER_PHASE_SEPARATOR:
            phase_header_count += 1
            name_idx = next_nonempty_index(i + 1)
            if name_idx is None or not lines[name_idx].lstrip().startswith("#"):
                errors.append(
                    f"{path}: master_triggers のフェーズ見出しが不正です。\n"
                    f"  【修正方法】以下の3行構造にしてください:\n"
                    f"  {MASTER_PHASE_SEPARATOR}\n"
                    f"  # フェーズ名\n"
                    f"  {MASTER_PHASE_SEPARATOR}"
                )
                break

            close_idx = next_nonempty_index(name_idx + 1)
            if close_idx is None or lines[close_idx].strip() != MASTER_PHASE_SEPARATOR:
                errors.append(
                    f"{path}: master_triggers のフェーズ見出しが閉じられていません。\n"
                    f"  【修正方法】フェーズ名行の直後に `{MASTER_PHASE_SEPARATOR}` を置いてください。"
                )
                break

            phase_name = lines[name_idx].lstrip("#").strip()
            if not phase_name:
                errors.append(
                    f"{path}: master_triggers のフェーズ名が空です。\n"
                    f"  【修正方法】`# フェーズ1: ...` のように記載してください。"
                )

            if current_group_name and not current_group_has_trigger:
                errors.append(
                    f"{path}: master_triggers の機能グループ '{current_group_name}' にトリガー定義がありません。\n"
                    f"  【修正方法】グループ見出しの直後に - trigger: を1つ以上配置してください。"
                )
            current_group_name = None
            current_group_has_trigger = False
            seen_phase = True
            i = close_idx + 1
            continue

        if line == MASTER_GROUP_SEPARATOR:
            group_header_count += 1
            name_idx = next_nonempty_index(i + 1)
            if name_idx is None or not lines[name_idx].lstrip().startswith("#"):
                errors.append(
                    f"{path}: master_triggers の機能グループ見出しが不正です。\n"
                    f"  【修正方法】以下の3行構造にしてください:\n"
                    f"  {MASTER_GROUP_SEPARATOR}\n"
                    f"  # 機能名\n"
                    f"  {MASTER_GROUP_SEPARATOR}"
                )
                break

            close_idx = next_nonempty_index(name_idx + 1)
            if close_idx is None or lines[close_idx].strip() != MASTER_GROUP_SEPARATOR:
                errors.append(
                    f"{path}: master_triggers の機能グループ見出しが閉じられていません。\n"
                    f"  【修正方法】機能名行の直後に `{MASTER_GROUP_SEPARATOR}` を置いてください。"
                )
                break

            group_name = lines[name_idx].lstrip("#").strip()
            if not group_name:
                errors.append(
                    f"{path}: master_triggers の機能グループ名が空です。\n"
                    f"  【修正方法】`# インポート / 再インポート` のように記載してください。"
                )

            if current_group_name and not current_group_has_trigger:
                errors.append(
                    f"{path}: master_triggers の機能グループ '{current_group_name}' にトリガー定義がありません。\n"
                    f"  【修正方法】グループ見出しの直後に - trigger: を1つ以上配置してください。"
                )

            current_group_name = group_name
            current_group_has_trigger = False
            i = close_idx + 1
            continue

        if re.match(r"^\s*-\s+trigger:\s*", lines[i]):
            trigger_count += 1
            if not seen_phase:
                errors.append(
                    f"{path}: master_triggers にフェーズ見出し（{MASTER_PHASE_SEPARATOR}）がありません。\n"
                    f"  【修正方法】最初のトリガー定義の前にフェーズ見出しを追加してください。"
                )
            if not current_group_name:
                errors.append(
                    f"{path}: master_triggers に機能グループ見出し（{MASTER_GROUP_SEPARATOR}）がありません。\n"
                    f"  【修正方法】各トリガー定義の前に機能グループ見出しを追加してください。"
                )
            current_group_has_trigger = True

        i += 1

    if current_group_name and not current_group_has_trigger:
        errors.append(
            f"{path}: master_triggers の機能グループ '{current_group_name}' にトリガー定義がありません。\n"
            f"  【修正方法】グループ見出しの直後に - trigger: を1つ以上配置してください。"
        )

    if trigger_count > 0 and phase_header_count == 0:
        errors.append(
            f"{path}: master_triggers のフェーズ見出しが見つかりません。\n"
            f"  【修正方法】{MASTER_PHASE_SEPARATOR} で囲んだフェーズ見出しを追加してください。"
        )
    if trigger_count > 0 and group_header_count == 0:
        errors.append(
            f"{path}: master_triggers の機能グループ区切りが見つかりません。\n"
            f"  【修正方法】{MASTER_GROUP_SEPARATOR} で囲んだ機能グループ見出しを追加してください。"
        )

    return errors


def check_master_triggers(path: Path, content: str) -> List[str]:
    errors: List[str] = []
    errors.extend(check_master_triggers_format(path, content))
    errors.extend(check_master_triggers_structure(path, content))
    return errors


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
        errors.extend(check_master_triggers(rel, text))

    if errors:
        print("Validation failed:")
        for e in errors:
            print(f"  {e}")
        return 1

    print("All rule files passed validation.")
    return 0


if __name__ == "__main__":
    sys.exit(validate())
