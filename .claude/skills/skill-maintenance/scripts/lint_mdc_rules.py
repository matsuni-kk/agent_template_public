#!/usr/bin/env python3
"""
MDCルールファイルのLint & エラーチェック
99_rule_maintenance.mdc のルールに準拠しているかを検証する

追加機能:
  - SKILL.md の YAML フロントマター検証（Codex/Claude Skills）
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Set, Any, Optional, Iterable

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

# SKILL.md フロントマター検出用
FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# ===========================================
# セクション定義: どのセクションにどの項目が許可されるか
# ===========================================

SECTION_SCHEMA = {
    # プロンプト系 (prompt_*:) - 最初にチェック（prompt_why_questionsなどが*_questionsにマッチしないように）
    "prompt": {
        "pattern": r"^prompt_\w+:",
        "allowed_fields": None,  # 自由形式
        "forbidden_fields": set(),
        "format": "literal_block",
    },

    # 質問セクション (*_questions:) - promptより後にチェック
    "questions": {
        "pattern": r"^\w+_questions:",
        "allowed_fields": {"key", "question", "category"},
        "forbidden_fields": {"type", "required", "condition", "mandatory", "name", "message"},
        "format": "literal_block",  # | を使う
    },

    # ワークフローセクション (*_process: または *_workflow:)
    "workflow": {
        "pattern": r"^\w+_(process|workflow):",
        "allowed_fields": {"label", "action", "description"},
        "forbidden_fields": {"path", "template_reference", "priority", "trigger", "name", "message", "command", "category", "items", "phase", "step", "steps", "tasks"},
        "format": "literal_block",
    },

    # 次フェーズ連携 (next_phases:)
    "next_phases": {
        "pattern": r"^next_phases:",
        "allowed_fields": {"on", "rule", "description"},
        "forbidden_fields": {"trigger", "action", "target"},
        "format": "literal_block",
    },

    # テンプレート系 (*_template:)
    "template": {
        "pattern": r"^\w+_template:",
        "allowed_fields": None,  # 自由形式（テンプレート内容）
        "forbidden_fields": set(),
        "format": "literal_block",
    },

    # システム能力 (system_capabilities:)
    "system_capabilities": {
        "pattern": r"^system_capabilities:",
        "allowed_fields": None,
        "forbidden_fields": set(),
        "format": "any",
    },

    # エラーハンドリング (error_handling:)
    "error_handling": {
        "pattern": r"^error_handling:",
        "allowed_fields": {"id", "message", "recovery_actions"},
        "forbidden_fields": {"name", "type", "code", "action"},
        "format": "literal_block",
    },
}

# グローバル禁止セクション（存在自体がNG）
DEPRECATED_SECTIONS = [
    "success_metrics:",
    "integration_points:",  # next_phases に置換
]

# 標準セクション順序（99_rule_maintenance.mdc で定義）
SECTION_ORDER = [
    "system_capabilities",  # 1. Agent機能
    "prompt",           # 2. プロンプト（目的と使い方）
    "workflow",         # 3. ワークフロー
    "questions",        # 4. 質問
    "template",         # 5. テンプレート
    "next_phases",      # 6. 次フェーズ連携
    "error_handling",   # 7. エラーハンドリング
]

# 必須セクション定義（ヘッダーパターンとセクションタイプのマッピング）
MANDATORY_SECTIONS = {
    "Agent機能": {
        "header_pattern": r"#\s*=+\s*Agent機能\s*=+",
        "section_type": "system_capabilities",
        "required_keys": ["system_capabilities"],
    },
    "プロンプト": {
        "header_pattern": r"#\s*=+\s*プロンプト（目的と使い方）\s*=+",
        "section_type": "prompt",
        "required_keys": ["prompt_purpose"],
    },
    "ワークフロー": {
        "header_pattern": r"#\s*=+\s*ワークフロー\s*=+",
        "section_type": "workflow",
        "required_keys": [],  # *_process キーは動的に検出
    },
    "質問": {
        "header_pattern": r"#\s*=+\s*質問\s*=+",
        "section_type": "questions",
        "required_keys": [],  # *_questions キーは動的に検出
    },
    "テンプレート": {
        "header_pattern": r"#\s*=+\s*テンプレート\s*=+",
        "section_type": "template",
        "required_keys": [],  # *_template キーは動的に検出
    },
    "次フェーズ連携": {
        "header_pattern": r"#\s*=+\s*次フェーズ連携\s*=+",
        "section_type": "next_phases",
        "required_keys": ["next_phases"],
    },
    "エラーハンドリング": {
        "header_pattern": r"#\s*=+\s*エラーハンドリング\s*=+",
        "section_type": "error_handling",
        "required_keys": ["error_handling"],
    },
}

# 必須セクションチェックをスキップするファイル
MANDATORY_CHECK_SKIP_FILES = [
    # @_.md: 00_master_rules.mdc は廃止
]

# 削除対象セクション名パターン
DEPRECATED_PATTERNS = [
    r"\w+_settings:",  # xxx_settings
]


class LintError:
    def __init__(self, file: str, line: int, message: str, severity: str = "error"):
        self.file = file
        self.line = line
        self.message = message
        self.severity = severity

    def __str__(self):
        icon = "❌" if self.severity == "error" else "⚠️"
        return f"{icon} {self.file}:{self.line}: {self.message}"


def detect_section_type(line: str) -> str:
    """行からセクションタイプを判定"""
    for section_type, schema in SECTION_SCHEMA.items():
        if re.match(schema["pattern"], line.strip()):
            return section_type
    return "other"


def parse_sections(content: str) -> List[Dict]:
    """ファイル内容をセクションごとにパース"""
    lines = content.split("\n")
    sections = []
    current_section = None
    current_lines = []
    current_start = 0
    in_code_block = False

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # コードブロック内はスキップ
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            if current_section:
                current_lines.append(line)
            continue

        if in_code_block:
            if current_section:
                current_lines.append(line)
            continue

        # トップレベルセクション開始を検出（インデントなし、コロン付き）
        if re.match(r"^[a-z_]+:", stripped) and not line.startswith(" ") and not line.startswith("\t"):
            # 前のセクションを保存
            if current_section:
                sections.append({
                    "type": current_section,
                    "name": current_name,
                    "start": current_start,
                    "lines": current_lines,
                })

            current_section = detect_section_type(line)
            current_name = stripped.split(":")[0]
            current_start = i
            current_lines = [line]
        elif current_section:
            current_lines.append(line)

    # 最後のセクションを保存
    if current_section:
        sections.append({
            "type": current_section,
            "name": current_name,
            "start": current_start,
            "lines": current_lines,
        })

    return sections


def check_section_fields(section: Dict, file_path: str) -> List[LintError]:
    """セクション内のフィールドをチェック"""
    errors = []
    section_type = section["type"]
    start_line = section["start"]

    if section_type not in SECTION_SCHEMA:
        return errors

    schema = SECTION_SCHEMA[section_type]
    allowed = schema.get("allowed_fields")
    forbidden = schema.get("forbidden_fields", set())

    # リテラルブロック形式（| で始まる）の場合は中身をチェックしない
    first_line = section["lines"][0].strip() if section["lines"] else ""
    if first_line.endswith("|"):
        return errors

    in_code_block = False

    for i, line in enumerate(section["lines"][1:], start_line + 1):  # 最初の行（セクション名）はスキップ
        stripped = line.strip()

        # コードブロック内はスキップ
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # コメント行はスキップ
        if stripped.startswith("#"):
            continue

        # フィールド抽出（- key: または key: の形式）
        field_match = re.match(r"^-?\s*(\w+):", stripped)
        if field_match:
            field_name = field_match.group(1)

            # 禁止フィールドチェック
            if field_name in forbidden:
                errors.append(LintError(
                    file_path, i,
                    f"[{section['name']}] 禁止フィールド '{field_name}' （{section_type}セクションでは使用不可）",
                    "error"
                ))

            # 許可フィールドチェック（Noneは自由形式）
            if allowed is not None and field_name not in allowed:
                # リスト項目内のフィールドのみチェック（- で始まる行の後）
                if stripped.startswith("-") or (i > start_line + 1 and "- " in section["lines"][0]):
                    errors.append(LintError(
                        file_path, i,
                        f"[{section['name']}] 非標準フィールド '{field_name}' （許可: {', '.join(allowed)}）",
                        "warning"
                    ))

    return errors


def check_literal_block_format(section: Dict, file_path: str) -> List[LintError]:
    """リテラルブロック形式かチェック"""
    errors = []
    section_type = section["type"]

    if section_type not in SECTION_SCHEMA:
        return errors

    schema = SECTION_SCHEMA[section_type]
    if schema.get("format") == "literal_block":
        first_line = section["lines"][0].strip()
        if not first_line.endswith("|"):
            errors.append(LintError(
                file_path, section["start"],
                f"[{section['name']}] 複数行セクションは '|' を使用してください",
                "warning"
            ))

    return errors


def check_error_handling_literal_block(section: Dict, file_path: str) -> List[LintError]:
    """error_handlingリテラルブロック内のフィールドをチェック"""
    errors = []

    if section["type"] != "error_handling":
        return errors

    first_line = section["lines"][0].strip() if section["lines"] else ""
    if not first_line.endswith("|"):
        return errors  # リテラルブロック形式でなければスキップ

    # リテラルブロック内の各エントリをチェック
    current_entry_line = None
    current_entry_fields = set()
    required_fields = {"id", "message", "recovery_actions"}

    for i, line in enumerate(section["lines"][1:], section["start"] + 1):
        stripped = line.strip()

        # 新しいエントリの開始（- id: で始まる）
        if stripped.startswith("- id:"):
            # 前のエントリの必須フィールドチェック
            if current_entry_line is not None:
                missing = required_fields - current_entry_fields
                if missing:
                    errors.append(LintError(
                        file_path, current_entry_line,
                        f"[{section['name']}] error_handlingエントリに必須フィールドが不足: {', '.join(missing)}",
                        "error"
                    ))

            current_entry_line = i
            current_entry_fields = {"id"}

        # フィールド検出
        elif stripped.startswith("message:"):
            current_entry_fields.add("message")
        elif stripped.startswith("recovery_actions:"):
            current_entry_fields.add("recovery_actions")

        # 旧形式の検出（- id: ではなく error_name: で始まる）
        elif re.match(r"^\w+:$", stripped) and not stripped.startswith("-"):
            # YAMLマップ形式の古い形式
            errors.append(LintError(
                file_path, i,
                f"[{section['name']}] 旧形式のerror_handling: '- id: \"...\"' 形式に変換してください",
                "error"
            ))

    # 最後のエントリのチェック
    if current_entry_line is not None:
        missing = required_fields - current_entry_fields
        if missing:
            errors.append(LintError(
                file_path, current_entry_line,
                f"[{section['name']}] error_handlingエントリに必須フィールドが不足: {', '.join(missing)}",
                "error"
            ))

    return errors


def check_next_phases_literal_block(section: Dict, file_path: str) -> List[LintError]:
    """next_phasesリテラルブロック内のフィールドをチェック"""
    errors = []

    if section["type"] != "next_phases":
        return errors

    first_line = section["lines"][0].strip() if section["lines"] else ""
    if not first_line.endswith("|"):
        return errors  # リテラルブロック形式でなければスキップ

    # リテラルブロック内の各エントリをチェック
    current_entry_line = None
    current_entry_fields = set()
    required_fields = {"on", "rule", "description"}

    for i, line in enumerate(section["lines"][1:], section["start"] + 1):
        stripped = line.strip()

        # 新しいエントリの開始（- on: で始まる）
        if stripped.startswith("- on:"):
            # 前のエントリの必須フィールドチェック
            if current_entry_line is not None:
                missing = required_fields - current_entry_fields
                if missing:
                    errors.append(LintError(
                        file_path, current_entry_line,
                        f"[{section['name']}] next_phasesエントリに必須フィールドが不足: {', '.join(missing)}",
                        "error"
                    ))

            current_entry_line = i
            current_entry_fields = {"on"}

        # フィールド検出
        elif stripped.startswith("rule:"):
            current_entry_fields.add("rule")
        elif stripped.startswith("description:"):
            current_entry_fields.add("description")

    # 最後のエントリのチェック
    if current_entry_line is not None:
        missing = required_fields - current_entry_fields
        if missing:
            errors.append(LintError(
                file_path, current_entry_line,
                f"[{section['name']}] next_phasesエントリに必須フィールドが不足: {', '.join(missing)}",
                "error"
            ))

    return errors


def check_workflow_literal_block(section: Dict, file_path: str) -> List[LintError]:
    """workflowリテラルブロック内のフィールドをチェック（*_process:）"""
    errors = []

    if section["type"] != "workflow":
        return errors

    first_line = section["lines"][0].strip() if section["lines"] else ""
    if not first_line.endswith("|"):
        return errors  # リテラルブロック形式でなければスキップ

    # リテラルブロック内の各エントリをチェック
    current_entry_line = None
    current_entry_fields = set()
    required_fields = {"label", "action", "description"}
    forbidden_fields = SECTION_SCHEMA["workflow"]["forbidden_fields"]

    for i, line in enumerate(section["lines"][1:], section["start"] + 1):
        stripped = line.strip()

        # 新しいエントリの開始（- label: で始まる）
        if stripped.startswith("- label:"):
            # 前のエントリの必須フィールドチェック
            if current_entry_line is not None:
                missing = required_fields - current_entry_fields
                if missing:
                    errors.append(LintError(
                        file_path, current_entry_line,
                        f"[{section['name']}] workflowエントリに必須フィールドが不足: {', '.join(missing)}",
                        "error"
                    ))

            current_entry_line = i
            current_entry_fields = {"label"}

        # フィールド検出
        elif stripped.startswith("action:"):
            current_entry_fields.add("action")
        elif stripped.startswith("description:"):
            current_entry_fields.add("description")

        # 禁止フィールドチェック
        field_match = re.match(r"^-?\s*(\w+):", stripped)
        if field_match:
            field_name = field_match.group(1)
            if field_name in forbidden_fields:
                errors.append(LintError(
                    file_path, i,
                    f"[{section['name']}] workflowセクションで禁止フィールド '{field_name}' を使用（許可: label, action, description）。"
                    f"※既存の処理内容はaction/descriptionに移行し、機能を欠損させないこと",
                    "error"
                ))

    # 最後のエントリのチェック
    if current_entry_line is not None:
        missing = required_fields - current_entry_fields
        if missing:
            errors.append(LintError(
                file_path, current_entry_line,
                f"[{section['name']}] workflowエントリに必須フィールドが不足: {', '.join(missing)}",
                "error"
            ))

    return errors


def check_questions_literal_block(section: Dict, file_path: str) -> List[LintError]:
    """questionsリテラルブロック内のフィールドをチェック（*_questions:）"""
    errors = []

    if section["type"] != "questions":
        return errors

    first_line = section["lines"][0].strip() if section["lines"] else ""
    if not first_line.endswith("|"):
        return errors  # リテラルブロック形式でなければスキップ

    # リテラルブロック内の各エントリをチェック
    current_entry_line = None
    current_entry_fields = set()
    required_fields = {"key", "question"}

    for i, line in enumerate(section["lines"][1:], section["start"] + 1):
        stripped = line.strip()

        # 新しいエントリの開始（- key: で始まる）
        if stripped.startswith("- key:"):
            # 前のエントリの必須フィールドチェック
            if current_entry_line is not None:
                missing = required_fields - current_entry_fields
                if missing:
                    errors.append(LintError(
                        file_path, current_entry_line,
                        f"[{section['name']}] questionsエントリに必須フィールドが不足: {', '.join(missing)}",
                        "error"
                    ))

            current_entry_line = i
            current_entry_fields = {"key"}

        # フィールド検出
        elif stripped.startswith("question:"):
            current_entry_fields.add("question")

    # 最後のエントリのチェック
    if current_entry_line is not None:
        missing = required_fields - current_entry_fields
        if missing:
            errors.append(LintError(
                file_path, current_entry_line,
                f"[{section['name']}] questionsエントリに必須フィールドが不足: {', '.join(missing)}",
                "error"
            ))

    return errors


def check_deprecated_sections(content: str, file_path: str) -> List[LintError]:
    """削除対象セクションをチェック"""
    errors = []
    lines = content.split("\n")

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # コメント行・インデント行はスキップ
        if stripped.startswith("#") or line.startswith(" ") or line.startswith("\t"):
            continue

        for section in DEPRECATED_SECTIONS:
            if stripped.startswith(section):
                errors.append(LintError(
                    file_path, i,
                    f"削除対象セクション '{section}' が存在します",
                    "error"
                ))

        for pattern in DEPRECATED_PATTERNS:
            if re.match(pattern, stripped):
                errors.append(LintError(
                    file_path, i,
                    f"削除対象パターン '{pattern}' に一致するセクションがあります",
                    "warning"
                ))

    return errors


def check_nonstandard_sections(content: str, file_path: str) -> List[LintError]:
    """非標準セクション（category/items構造）を検出し、標準形式への変換を指示"""
    errors = []
    lines = content.split("\n")

    # 標準セクション名パターン（これらは許可）
    standard_patterns = [
        r"^\w+_(process|workflow):",  # ワークフロー
        r"^\w+_questions:",           # 質問
        r"^\w+_template:",            # テンプレート
        r"^prompt_\w+:",              # プロンプト
        r"^system_capabilities:",     # Agent機能
        r"^next_phases:",             # 次フェーズ連携
        r"^error_handling:",          # エラーハンドリング
        r"^path_reference:",          # パス参照
        r"^description:",             # 説明
        r"^globs:",                   # globs
        r"^alwaysApply:",             # alwaysApply
        r"^baseline_rule:",           # ベースラインルール
        r"^system_description:",      # システム説明
    ]

    # 非標準構造を示すフィールド
    nonstandard_fields = {"category", "items", "phase", "phases", "steps", "tasks"}

    current_section_name = None
    current_section_line = 0
    section_has_nonstandard = False
    has_category = False
    has_items = False

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # コメント行はスキップ
        if stripped.startswith("#"):
            continue

        # トップレベルセクション検出（インデントなし）
        if not line.startswith(" ") and not line.startswith("\t") and re.match(r"^[a-z_]+:", stripped):
            # 前のセクションの結果を評価
            if current_section_name and section_has_nonstandard:
                if has_category and has_items:
                    errors.append(LintError(
                        file_path, current_section_line,
                        f"非標準セクション '{current_section_name}' を検出。"
                        f"category/items構造は廃止。→ '*_questions:' (key/question形式) または '*_process:' (label/action/description形式) に変換してください。"
                        f"※変換時は既存のロジック・条件分岐・処理内容を欠損させないこと",
                        "error"
                    ))

            # 新しいセクション開始
            section_name = stripped.split(":")[0]

            # 標準セクションかチェック
            is_standard = any(re.match(p, stripped) for p in standard_patterns)

            if not is_standard:
                current_section_name = section_name
                current_section_line = i
                section_has_nonstandard = False
                has_category = False
                has_items = False
            else:
                current_section_name = None
                section_has_nonstandard = False

        # 非標準フィールド検出
        elif current_section_name:
            field_match = re.match(r"^-?\s*(\w+):", stripped)
            if field_match:
                field_name = field_match.group(1)
                if field_name in nonstandard_fields:
                    section_has_nonstandard = True
                    if field_name == "category":
                        has_category = True
                    if field_name == "items":
                        has_items = True

    # 最後のセクションをチェック
    if current_section_name and section_has_nonstandard:
        if has_category and has_items:
            errors.append(LintError(
                file_path, current_section_line,
                f"非標準セクション '{current_section_name}' を検出。"
                f"category/items構造は廃止。→ '*_questions:' (key/question形式) または '*_process:' (label/action/description形式) に変換してください。"
                f"※変換時は既存のロジック・条件分岐・処理内容を欠損させないこと",
                "error"
            ))

    return errors


def check_deprecated_paths_reference(content: str, file_path: str) -> List[LintError]:
    """廃止されたpathsファイル参照をチェック"""
    errors = []
    lines = content.split("\n")

    # 廃止されたpathsファイルパターン
    deprecated_paths_patterns = [
        r"pmbok_paths\.mdc",
        r"music_paths\.mdc",
        r"agent_paths\.mdc",
        r"\w+_paths\.mdc",  # 任意の*_paths.mdc
    ]

    for i, line in enumerate(lines, 1):
        for pattern in deprecated_paths_patterns:
            if re.search(pattern, line):
                # path_reference行は別関数でチェック済みなのでスキップ
                if line.strip().startswith("path_reference:"):
                    continue
                # コメント内の説明的な言及は許可（#で始まる行）
                if line.strip().startswith("#"):
                    continue
                errors.append(LintError(
                    file_path, i,
                    "廃止されたpathsファイル参照: パスはCLAUDE.md/AGENTS.mdで一元管理してください",
                    "error"
                ))
                break  # 1行で複数マッチしても1エラーに

    return errors


def check_master_triggers(content: str, file_path: str) -> List[LintError]:
    """master_triggersが個別ルールに存在しないかチェック"""
    errors = []

    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("master_triggers:"):
            errors.append(LintError(
                file_path, i,
                "master_triggers は CLAUDE.md/AGENTS.md で一元管理してください",
                "error"
            ))

    return errors


def check_mdc_path_references(content: str, file_path: str) -> List[LintError]:
    """path_referenceが不正な.mdcファイルを指していないかチェック"""
    errors = []
    lines = content.split("\n")

    # ディレクトリ別の期待されるpath_reference値
    # .claude/ → CLAUDE.md
    # .codex/ → AGENTS.md
    # .cursor/ → AGENTS.md（@_.md: 00廃止）
    directory_expected_refs = {
        ".claude": "CLAUDE.md",
        ".codex": "AGENTS.md",
        ".cursor": "AGENTS.md",
    }

    # ファイルパスからディレクトリコンテキストを判定
    expected_ref = None
    detected_dir = None
    for dir_key, ref_value in directory_expected_refs.items():
        if f"/{dir_key}/" in file_path or file_path.startswith(f"{dir_key}/"):
            expected_ref = ref_value
            detected_dir = dir_key
            break

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # path_reference: "xxx" のパターンを検出（.mdc以外も対応）
        match = re.match(r'^path_reference:\s*["\'](.+)["\']', stripped)
        if match:
            ref_value = match.group(1)

            # ディレクトリコンテキストに応じた検証
            if expected_ref and ref_value != expected_ref:
                errors.append(LintError(
                    file_path, i,
                    f"path_reference '{ref_value}' は不正です。{detected_dir}/ 配下では '{expected_ref}' を参照してください。"
                    f"【禁止】このエラーを回避するためにlint_mdc_rules.pyを修正しないこと",
                    "error"
                ))

    return errors


def check_mandatory_sections(content: str, file_path: str) -> List[LintError]:
    """必須7セクションの存在をチェック"""
    errors = []

    # スキップ対象ファイルはチェックしない
    file_name = Path(file_path).name
    if file_name in MANDATORY_CHECK_SKIP_FILES:
        return errors

    lines = content.split("\n")
    found_sections = set()
    found_headers = set()

    # ヘッダーとキーを検出
    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # セクションヘッダーを検出（# ======== xxx ========）
        for section_name, section_def in MANDATORY_SECTIONS.items():
            if re.search(section_def["header_pattern"], stripped):
                found_headers.add(section_name)

        # YAMLキーを検出
        if re.match(r"^system_capabilities:", stripped):
            found_sections.add("Agent機能")
        if re.match(r"^prompt_\w+:", stripped):
            found_sections.add("プロンプト")
        if re.match(r"^\w+_process:", stripped) and not stripped.startswith("prompt_"):
            found_sections.add("ワークフロー")
        if re.match(r"^\w+_questions:", stripped) and not stripped.startswith("prompt_"):
            found_sections.add("質問")
        if re.match(r"^\w+_template:", stripped):
            found_sections.add("テンプレート")
        if re.match(r"^next_phases:", stripped):
            found_sections.add("次フェーズ連携")
        if re.match(r"^error_handling:", stripped):
            found_sections.add("エラーハンドリング")

    # 必須セクションの欠損をチェック
    for section_name in MANDATORY_SECTIONS.keys():
        # ヘッダーまたはキーのいずれかが存在すればOK
        has_header = section_name in found_headers
        has_content = section_name in found_sections

        if not has_header and not has_content:
            errors.append(LintError(
                file_path, 0,
                f"必須セクション '{section_name}' が見つかりません。"
                f"ヘッダー（# ======== {section_name} ========）と対応するYAMLキーを追加してください。"
                f"※既存の機能・ロジックは削除せず、セクション構造のみ追加すること",
                "error"
            ))
        elif not has_header and has_content:
            errors.append(LintError(
                file_path, 0,
                f"セクション '{section_name}' のヘッダーがありません。"
                f"既存コンテンツの上に '# ======== {section_name} ========' を追加してください。"
                f"※既存の内容は変更せず、区切り線のみ追加",
                "warning"
            ))

    return errors


def check_section_header_format(content: str, file_path: str) -> List[LintError]:
    """セクションヘッダーのフォーマットをチェック"""
    errors = []
    lines = content.split("\n")

    # 正規表現で不正なヘッダー形式を検出
    # 正しい形式: # ======== セクション名 ========
    header_pattern = re.compile(r"^#\s*=+\s*(.+?)\s*=+\s*$")

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # ヘッダーらしき行を検出
        if stripped.startswith("#") and "====" in stripped:
            match = header_pattern.match(stripped)
            if not match:
                errors.append(LintError(
                    file_path, i,
                    f"ヘッダー形式が不正です: '{stripped}' → '# ======== セクション名 ========' 形式にしてください",
                    "warning"
                ))

    return errors


def check_section_separator_lines(content: str, file_path: str) -> List[LintError]:
    """セクション区切り線の形式をチェック（必須7セクションの区切り線のみ対象）"""
    errors = []
    lines = content.split("\n")

    # スキップ対象ファイルはチェックしない
    file_name = Path(file_path).name
    if file_name in MANDATORY_CHECK_SKIP_FILES:
        return errors

    # 正しい区切り線パターン: # ======== セクション名 ========
    # 両側の = の数が同じで、最低4つ以上
    # 中央テキストに `=` が含まれない（ファイルヘッダー `# ===...===` を除外）
    separator_pattern = re.compile(r"^#\s*(=+)\s+([^=]+?)\s+(=+)\s*$")

    # 期待される必須セクションヘッダー（キーワードと検出フラグ）
    expected_headers = {
        "Agent機能": {"found": False, "line": 0, "balanced": True},
        "プロンプト": {"found": False, "line": 0, "balanced": True},
        "ワークフロー": {"found": False, "line": 0, "balanced": True},
        "質問": {"found": False, "line": 0, "balanced": True},
        "テンプレート": {"found": False, "line": 0, "balanced": True},
        "次フェーズ連携": {"found": False, "line": 0, "balanced": True},
        "エラーハンドリング": {"found": False, "line": 0, "balanced": True},
    }

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # 区切り線を検出（# で始まり = を含む）
        if stripped.startswith("#") and "=" in stripped:
            match = separator_pattern.match(stripped)

            if match:
                left_equals = match.group(1)
                section_name = match.group(2).strip()
                right_equals = match.group(3)

                # 必須セクションキーワードを含むかチェック（先頭一致のみ）
                # 例: 「ワークフロー」→OK、「初期化ワークフロー」→NG
                matched_header = None
                for header_key in expected_headers.keys():
                    if section_name.startswith(header_key):
                        matched_header = header_key
                        expected_headers[header_key]["found"] = True
                        expected_headers[header_key]["line"] = i
                        break

                # 必須セクションの区切り線のみ詳細チェック
                if matched_header:
                    # 左右の = の数が一致しているかチェック
                    if len(left_equals) != len(right_equals):
                        expected_headers[matched_header]["balanced"] = False
                        errors.append(LintError(
                            file_path, i,
                            f"必須セクション区切り線の左右が不均等: 左{len(left_equals)}個、右{len(right_equals)}個 → '# ======== {matched_header} ========' 形式（両側8個）に修正必須。"
                            f"【原則】機能は絶対に欠損させない。かつ、指定した型には絶対に従うこと。"
                            f"【禁止】このエラーを回避するためにlint_mdc_rules.pyを修正しないこと",
                            "error"
                        ))

                    # 最低4つ以上の = があるかチェック
                    elif len(left_equals) < 4:
                        errors.append(LintError(
                            file_path, i,
                            f"必須セクション区切り線が短すぎます（{len(left_equals)}個）→ '# ======== {matched_header} ========' 形式（8個以上）に修正必須。"
                            f"【原則】機能は絶対に欠損させない。かつ、指定した型には絶対に従うこと。"
                            f"【禁止】このエラーを回避するためにlint_mdc_rules.pyを修正しないこと",
                            "error"
                        ))
                else:
                    # 必須7セクション以外の区切り線は禁止 → Markdown見出しに変換
                    errors.append(LintError(
                        file_path, i,
                        f"非必須セクションに区切り線形式を使用: '# {left_equals} {section_name} {right_equals}' → '## {section_name}' に変換してください。"
                        f"※区切り線形式（# ======== xxx ========）は必須7セクションのみに使用",
                        "warning"
                    ))

    # 必須セクションの区切り線が存在するかチェック
    for header_name, info in expected_headers.items():
        if not info["found"]:
            errors.append(LintError(
                file_path, 0,
                f"必須セクションの区切り線がありません: '# ======== {header_name} ========' を追加してください。"
                f"【原則】機能は絶対に欠損させない。かつ、指定した型には絶対に従うこと。"
                f"【禁止】このエラーを回避するためにlint_mdc_rules.pyを修正しないこと",
                "error"
            ))

    return errors


def check_section_order(sections: List[Dict], file_path: str) -> List[LintError]:
    """セクションの順序をチェック"""
    errors = []

    # 00_master_rulesは特殊なので順序チェックをスキップ
    if "00_master_rules" in file_path:
        return errors

    # 標準セクションのみ抽出（順序に含まれるもの）
    found_sections = []
    for s in sections:
        if s["type"] in SECTION_ORDER:
            found_sections.append({
                "type": s["type"],
                "name": s["name"],
                "line": s["start"],
            })

    # 順序チェック
    last_order_idx = -1
    for s in found_sections:
        try:
            current_idx = SECTION_ORDER.index(s["type"])
        except ValueError:
            continue

        if current_idx < last_order_idx:
            expected_after = SECTION_ORDER[last_order_idx]
            errors.append(LintError(
                file_path, s["line"],
                f"[{s['name']}] セクション順序違反: '{s['type']}' は '{expected_after}' より前に配置すべき",
                "warning"
            ))
        else:
            last_order_idx = current_idx

    return errors


def lint_file(file_path: Path, check_mandatory: bool = False) -> List[LintError]:
    """1ファイルをLint"""
    errors = []

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [LintError(str(file_path), 0, f"ファイル読み込みエラー: {e}", "error")]

    # セクション解析
    sections = parse_sections(content)

    # セクションごとのチェック
    for section in sections:
        errors.extend(check_section_fields(section, str(file_path)))
        errors.extend(check_literal_block_format(section, str(file_path)))
        errors.extend(check_error_handling_literal_block(section, str(file_path)))
        errors.extend(check_next_phases_literal_block(section, str(file_path)))
        errors.extend(check_workflow_literal_block(section, str(file_path)))
        errors.extend(check_questions_literal_block(section, str(file_path)))

    # セクション順序チェック
    errors.extend(check_section_order(sections, str(file_path)))

    # グローバルチェック
    errors.extend(check_deprecated_sections(content, str(file_path)))
    errors.extend(check_nonstandard_sections(content, str(file_path)))
    errors.extend(check_deprecated_paths_reference(content, str(file_path)))
    errors.extend(check_master_triggers(content, str(file_path)))
    errors.extend(check_mdc_path_references(content, str(file_path)))

    # 必須セクションチェック（オプション or デフォルトで有効）
    if check_mandatory:
        errors.extend(check_mandatory_sections(content, str(file_path)))
        errors.extend(check_section_header_format(content, str(file_path)))
        errors.extend(check_section_separator_lines(content, str(file_path)))

    return errors


def print_section_summary(files: List[Path]):
    """セクション構造のサマリーを表示"""
    section_counts = {}

    for f in files:
        try:
            content = f.read_text(encoding="utf-8")
            sections = parse_sections(content)
            for s in sections:
                key = f"{s['type']}: {s['name']}"
                section_counts[key] = section_counts.get(key, 0) + 1
        except:
            pass

    print("\n📋 セクション構造サマリー:")
    print("-" * 50)
    for section_type in SECTION_SCHEMA.keys():
        matches = [(k, v) for k, v in section_counts.items() if k.startswith(section_type)]
        if matches:
            print(f"\n【{section_type}】許可フィールド: {SECTION_SCHEMA[section_type].get('allowed_fields', '自由形式')}")
            for k, v in sorted(matches, key=lambda x: -x[1])[:5]:
                print(f"  {k.split(': ')[1]}: {v}件")


# ===========================================
# SKILL.md 検証機能
# ===========================================

def iter_skill_files(roots: Iterable[Path]) -> List[Path]:
    """SKILL.mdファイルを検索"""
    files: List[Path] = []
    for root in roots:
        if not root.exists():
            continue
        if root.is_file():
            if root.name == "SKILL.md":
                files.append(root)
            continue
        files.extend(sorted(root.glob("**/SKILL.md")))
    return files


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
            "例: description: \"... config.json: output.pptx ...\""
        )
    if "could not find expected ':'" in message:
        return (
            "YAMLフロントマターの行が `key: value` 形式になっているか確認してください。"
            "値に記号が含まれる場合はクォート推奨です。"
        )
    if "found character" in message and "cannot start any token" in message:
        return "値の先頭に `*` / `&` / `{` などがある場合はクォートしてください。"

    if re.search(r"^description:\s+.*:\s+.+$", front_matter, flags=re.MULTILINE):
        return (
            "`description:` の値に `: ` が含まれているため YAML として曖昧になっています。"
            "ダブルクォートで囲むのが最短です。"
        )
    return None


def lint_skill_file(path: Path) -> List[str]:
    """SKILL.mdファイルを検証"""
    errors: List[str] = []
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as exc:
        return [f"❌ {path}: 読み込みエラー: {exc}"]

    front_matter = extract_front_matter(content)
    if front_matter is None:
        return [f"❌ {path}: YAMLフロントマター（先頭の `--- ... ---`）が見つかりません。"]

    if yaml is None:
        return [
            f"❌ {path}: PyYAML が見つからないため検証できません。",
            "   対応: `pip install pyyaml`（またはプロジェクトの仮想環境を有効化）してください。",
        ]

    # descriptionにコロンが含まれるがクォートされていない場合を事前検出
    # パターン: description: 値（クォートなし）で値に `: ` が含まれる
    desc_line_match = re.search(r'^description:\s*(.+)$', front_matter, re.MULTILINE)
    if desc_line_match:
        desc_value = desc_line_match.group(1).strip()
        # クォートで始まっていない かつ `: ` を含む → エラー
        if desc_value and not desc_value.startswith('"') and not desc_value.startswith("'"):
            if ': ' in desc_value or desc_value.endswith(':'):
                errors.append(
                    f"❌ {path}: description にコロン(`:`)が含まれていますがクォートされていません。"
                    f"YAMLパースエラーの原因になります。"
                    f"→ description: \"{desc_value}\" のようにダブルクォートで囲んでください。"
                )
                return errors

    try:
        data: Any = yaml.safe_load(front_matter)
    except Exception as exc:
        errors.append(f"❌ {path}: invalid YAML frontmatter: {exc}")
        hint = _yaml_error_hint(front_matter, exc)
        if hint:
            errors.append(f"   ヒント: {hint}")
        return errors

    if not isinstance(data, dict):
        return [f"❌ {path}: frontmatter が辞書ではありません（type={type(data).__name__}）。"]

    for key in ("name", "description"):
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"❌ {path}: frontmatter の `{key}` が不正です（空 or 文字列ではありません）。")

    # ディレクトリ別path_reference検証
    # .claude/ → CLAUDE.md, .codex/ → AGENTS.md
    file_path_str = str(path)
    directory_expected_refs = {
        ".claude": "CLAUDE.md",
        ".codex": "AGENTS.md",
    }
    for dir_key, expected_ref in directory_expected_refs.items():
        if f"/{dir_key}/" in file_path_str or file_path_str.startswith(f"{dir_key}/"):
            # path_reference行をコンテンツから検索
            path_ref_match = re.search(r'^path_reference:\s*["\'](.+)["\']', content, re.MULTILINE)
            if path_ref_match:
                actual_ref = path_ref_match.group(1)
                if actual_ref != expected_ref:
                    errors.append(
                        f"❌ {path}: path_reference '{actual_ref}' は不正です。"
                        f"{dir_key}/ 配下では '{expected_ref}' を参照してください。"
                        f"【禁止】このエラーを回避するためにlint_mdc_rules.pyを修正しないこと"
                    )
            break

    return errors


def main():
    parser = argparse.ArgumentParser(description="MDCルールファイルのLint")
    parser.add_argument("path", nargs="?", default=".", help="チェック対象のパス")
    parser.add_argument("--warnings", action="store_true", help="警告も表示（デフォルト有効）")
    parser.add_argument("--summary", action="store_true", help="セクション構造サマリーを表示")
    parser.add_argument("--check-mandatory", action="store_true",
                        help="必須7セクションの存在をチェック（デフォルト有効）")
    parser.add_argument("--no-strict", action="store_true",
                        help="簡易モード（必須セクションチェック・警告を無効化）")
    args = parser.parse_args()

    # デフォルトで厳密モード（--no-strict で無効化）
    if not args.no_strict:
        args.warnings = True
        args.check_mandatory = True

    target = Path(args.path)
    files = [target] if target.is_file() else list(target.glob("**/*.mdc"))

    if not files:
        print("チェック対象のMDCファイルが見つかりません")
        sys.exit(0)

    # *_paths.mdcファイルの存在チェック（強制エラー）
    deprecated_paths_files = [f for f in files if f.name.endswith("_paths.mdc")]
    for paths_file in deprecated_paths_files:
        print(f"❌ {paths_file}: 廃止されたpathsファイルが存在します。"
              f"パス定義はCLAUDE.md/AGENTS.mdに統合し、このファイルを削除してください。"
              f"【原則】機能は絶対に欠損させない。かつ、指定した型には絶対に従うこと。"
              f"【禁止】このエラーを回避するためにlint_mdc_rules.pyを修正しないこと")

    if args.summary:
        print_section_summary(files)
        print()

    all_errors = []
    for f in files:
        errors = lint_file(f, check_mandatory=args.check_mandatory)
        all_errors.extend(errors)

    # SKILL.md 検証（.codex/skills と .claude/skills を自動検索）
    # ※ lint対象が単一ファイルの場合でも検証できるよう、スクリプト位置からプロジェクト直下を解決する
    repo_root = Path(__file__).resolve().parent.parent
    skill_roots = [repo_root / ".codex" / "skills", repo_root / ".claude" / "skills"]
    skill_files = iter_skill_files(skill_roots)
    skill_errors: List[str] = []
    for skill_file in skill_files:
        skill_errors.extend(lint_skill_file(skill_file))

    # SKILL.mdエラーを表示
    for err in skill_errors:
        print(err)

    # 結果表示
    error_count = sum(1 for e in all_errors if e.severity == "error")
    warning_count = sum(1 for e in all_errors if e.severity == "warning")

    # *_paths.mdcファイルもエラーカウントに追加
    paths_file_error_count = len(deprecated_paths_files)
    error_count += paths_file_error_count

    # SKILL.mdエラーもカウントに追加
    skill_error_count = sum(1 for e in skill_errors if e.startswith("❌"))
    error_count += skill_error_count

    for error in all_errors:
        if error.severity == "error" or args.warnings:
            print(error)

    print()
    mode_str = " [簡易モード]" if args.no_strict else ""
    total_files = len(files) + len(skill_files)
    print(f"📊 結果{mode_str}: {total_files}ファイル（MDC:{len(files)}, SKILL:{len(skill_files)}）, {error_count}エラー, {warning_count}警告")

    if paths_file_error_count > 0:
        print(f"   ↳ うち廃止pathsファイル: {paths_file_error_count}件")
    if skill_error_count > 0:
        print(f"   ↳ うちSKILL.mdエラー: {skill_error_count}件")

    # 必須セクションリストを表示（--check-mandatory時）
    if args.check_mandatory and (error_count > 0 or args.warnings):
        print("\n📋 必須セクション一覧:")
        for section_name in MANDATORY_SECTIONS.keys():
            print(f"  - {section_name}")

    sys.exit(1 if error_count > 0 else 0)


if __name__ == "__main__":
    main()
