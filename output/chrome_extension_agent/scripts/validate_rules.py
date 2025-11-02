#!/usr/bin/env python3
"""Validate .mdc rule files for front matter, path comments, and format standards."""

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

# 区切り線パターン
TITLE_SEPARATOR_PATTERN = r"^# ==========+$"  # タイトル帯
SECTION_SEPARATOR_PATTERN = r"^# ======== .+ ========$"  # セクション帯
SUBSECTION_SEPARATOR_PATTERN = r"^# ----- .+ -----$"  # サブセクション帯

# 必須プロンプトセクション
REQUIRED_PROMPT_SECTIONS = [
    "prompt_purpose:",
    "prompt_why_questions:",
    "prompt_why_templates:",
    "prompt_principles:",
]


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
        errors.append(
            f"{path}: フロントマター構文エラーが検出されました。\n"
            f"  【原因】{exc}\n"
            f"  【修正方法】ファイル冒頭に以下の形式でフロントマターを配置してください:\n"
            f"  ---\n"
            f"  description: ルールの説明\n"
            f"  globs:\n"
            f"  alwaysApply: false\n"
            f"  ---"
        )
        return errors

    if "description" not in fm:
        errors.append(
            f"{path}: フロントマターに 'description' が見つかりません。\n"
            f"  【修正方法】フロントマター内に以下を追加してください:\n"
            f"  description: このルールの目的を簡潔に記述"
        )
    if "globs" not in fm:
        errors.append(
            f"{path}: フロントマターに 'globs' ブロックが見つかりません。\n"
            f"  【修正方法】フロントマター内に以下を追加してください:\n"
            f"  globs:\n"
            f"  alwaysApply: false"
        )
        return errors

    always_line = fm.get("alwaysApply") or fm.get("alwaysapply")
    if always_line is None:
        errors.append(
            f"{path}: globs ブロック内に 'alwaysApply' が見つかりません。\n"
            f"  【修正方法】globs ブロックに以下を追加してください:\n"
            f"  alwaysApply: {'true' if expected_always_true(path) else 'false'}"
        )
    else:
        value = always_line.replace('"', '').strip().lower()
        expected = "true" if expected_always_true(path) else "false"
        if value != expected:
            errors.append(
                f"{path}: alwaysApply の値が不正です。現在値: {always_line.strip()}\n"
                f"  【修正方法】以下のように修正してください:\n"
                f"  alwaysApply: {expected}\n"
                f"  【理由】{'00番台ファイルとパスファイルはtrue' if expected == 'true' else '01-96番台ルールはfalse'}に設定する必要があります"
            )
    return errors


def check_path_comments(path: Path, content: str) -> List[str]:
    if not path.name.endswith("_paths.mdc"):
        return []
    missing = [line for line in PATH_COMMENT_LINES if line not in content]
    if missing:
        return [
            f"{path}: 必須パスコメントが見つかりません。\n"
            f"  【不足行】{missing[0]}\n"
            f"  【修正方法】ファイル冒頭のフロントマター直後に以下のコメントブロックを追加してください:\n"
            f"  <!-- NOTE: 環境に合わせてパスを調整し、必要に応じて記述方法を変更してください -->\n"
            f"  # ・{{{{ }}}} 内は動的に置換するプレースホルダ変数\n"
            f"  # ・`templates.root_dir` に自身のワークスペースパスを設定し、root を派生エージェント用に展開します\n"
            f"  # ----\n"
            f"  # 0. ルートディレクトリ\n"
            f"  # ----"
        ]

    # ensure root line present and concrete
    for line in content.splitlines():
        if line.strip().startswith("root:"):
            root_value = line.split(":", 1)[1].strip().strip('"')
            if "{{" in root_value or root_value in {"", "/"}:
                return [
                    f"{path}: root の設定が不適切です。現在値: {root_value!r}\n"
                    f"  【修正方法】root を実際の絶対パスに変更してください:\n"
                    f"  例: root: \"/Users/yourname/workspace/your_agent\"\n"
                    f"  【理由】{{{{templates.root_dir}}}}/{{{{agent_name}}}} のようなプレースホルダは実際のパスに置き換える必要があります"
                ]
            return []
    return [
        f"{path}: root 定義が見つかりません。\n"
        f"  【修正方法】パスコメントブロックの直後に以下を追加してください:\n"
        f"  root: \"/Users/yourname/workspace/your_agent\"\n"
        f"  【注意】実際の作業ディレクトリの絶対パスを指定してください"
    ]


def check_separators(path: Path, content: str) -> List[str]:
    """区切り線フォーマットをチェック"""
    errors: List[str] = []

    # 00_master_rules.mdc と *_paths.mdc は区切り線チェックをスキップ
    if path.name.startswith("00_") or path.name.endswith("_paths.mdc"):
        return []

    # 97, 98, 99番台もスキップ
    if path.name.startswith(("97_", "98_", "99_")):
        return []

    lines = content.splitlines()

    # タイトル帯チェック (# ==========================================================)
    title_separators = [i for i, line in enumerate(lines) if re.match(TITLE_SEPARATOR_PATTERN, line.strip())]
    if len(title_separators) < 2:
        errors.append(
            f"{path}: タイトル帯の区切り線が不足しています。検出数: {len(title_separators)}行\n"
            f"  【修正方法】ファイル冒頭とタイトル直後に以下の区切り線を配置してください:\n"
            f"  # ==========================================================\n"
            f"  # NN_{{domain}}_{{function}}.mdc - タイトル\n"
            f"  # ==========================================================\n"
            f"  【理由】標準フォーマットではタイトルを挟む形で2行の区切り線が必要です"
        )

    # セクション帯チェック (# ======== セクション名 ========)
    section_separators = [i for i, line in enumerate(lines) if re.match(SECTION_SEPARATOR_PATTERN, line.strip())]
    if not section_separators:
        errors.append(
            f"{path}: セクション帯の区切り線が見つかりません。\n"
            f"  【修正方法】各主要セクションに以下の形式の区切り線を追加してください:\n"
            f"  # ======== プロンプト（目的と使い方） ========\n"
            f"  # ======== Phase 1: フェーズ名 ========\n"
            f"  # ======== Phase 2: フェーズ名 ========\n"
            f"  【理由】セクション構造を明確にするため、'========'で囲んだ区切り線が必要です"
        )

    return errors


def check_prompt_sections(path: Path, content: str) -> List[str]:
    """プロンプトセクションの存在をチェック"""
    errors: List[str] = []

    # 00_master_rules.mdc と *_paths.mdc はプロンプトセクション不要
    if path.name.startswith("00_") or path.name.endswith("_paths.mdc"):
        return []

    # 97, 98, 99番台もスキップ
    if path.name.startswith(("97_", "98_", "99_")):
        return []

    missing_sections = [section for section in REQUIRED_PROMPT_SECTIONS if section not in content]

    if missing_sections:
        errors.append(
            f"{path}: 必須プロンプトセクションが不足しています。\n"
            f"  【不足セクション】\n    " + "\n    ".join(missing_sections) + "\n"
            f"  【修正方法】path_reference の直後に以下のプロンプトセクションを追加してください:\n\n"
            f"  # ======== プロンプト（目的と使い方） ========\n"
            f"  prompt_purpose: |\n"
            f"    このルールの目的を1-2文で明確化。誰の意思決定を、何のために、どの成果物で支援するか。\n\n"
            f"  prompt_why_questions: |\n"
            f"    なぜ質問が必要か／何を揃えるかを1-4行で記述。\n\n"
            f"  prompt_why_templates: |\n"
            f"    テンプレートを使う理由を1-3行で説明。\n\n"
            f"  prompt_principles: |\n"
            f"    運用原則（事実記録・欠損明示・根拠明記など）を箇条書きで記述。\n\n"
            f"  【理由】プロンプトセクションは各ルールの目的と使い方を明確化するために必須です"
        )

    return errors


def check_path_reference(path: Path, content: str) -> List[str]:
    """path_reference の存在をチェック"""
    errors: List[str] = []

    # *_paths.mdc 自体はpath_reference不要
    if path.name.endswith("_paths.mdc"):
        return []

    if 'path_reference:' not in content:
        errors.append(
            f"{path}: path_reference が見つかりません。\n"
            f"  【修正方法】フロントマター直後（最初の --- の後）に以下を追加してください:\n"
            f"  path_reference: \"{{domain}}_paths.mdc\"\n"
            f"  例: path_reference: \"marketing_paths.mdc\"\n"
            f"  【理由】全ルールファイルはパスファイルを参照する必要があります"
        )
    else:
        # path_reference の値をチェック
        for line in content.splitlines():
            if line.strip().startswith('path_reference:'):
                ref_value = line.split(':', 1)[1].strip().strip('"\'')
                if not ref_value.endswith('_paths.mdc'):
                    errors.append(
                        f"{path}: path_reference の形式が不正です。現在値: {ref_value}\n"
                        f"  【修正方法】以下のように'*_paths.mdc'形式に修正してください:\n"
                        f"  path_reference: \"{{domain}}_paths.mdc\"\n"
                        f"  例: path_reference: \"marketing_paths.mdc\"\n"
                        f"  【理由】パスファイル参照は'_paths.mdc'で終わる必要があります"
                    )
                break

    return errors


def check_system_capabilities(path: Path, content: str) -> List[str]:
    """system_capabilities セクションの存在をチェック (01-89番台のみ)"""
    errors: List[str] = []

    # 00, 97-99番台、パスファイルはスキップ
    if (path.name.startswith("00_") or
        path.name.startswith(("97_", "98_", "99_")) or
        path.name.endswith("_paths.mdc")):
        return []

    # 01-89番台のルールファイル
    if re.match(r"^\d{2}_.*\.mdc$", path.name):
        if "system_capabilities:" not in content:
            errors.append(
                f"{path}: system_capabilities セクションが見つかりません。\n"
                f"  【修正方法】プロンプトセクションの後に以下を追加してください:\n\n"
                f"  # ======== {{システム名}}統合エージェント ========\n\n"
                f"  system_capabilities:\n"
                f"    core_function: \"機能の中核となる処理の詳細説明\"\n"
                f"    data_processing: \"データ処理・分析機能の詳細説明\"\n"
                f"    workflow_management: \"ワークフロー管理・自動化の詳細説明\"\n"
                f"    quality_assurance: \"品質保証・検証機能の詳細説明\"\n"
                f"    integration_support: \"他システム連携・統合の詳細説明\"\n"
                f"    user_experience: \"ユーザー体験・インターフェースの詳細説明\"\n\n"
                f"  【理由】標準フォーマットでは6項目のシステム機能定義が必須です"
            )

    return errors


def check_phase_descriptions(path: Path, content: str) -> List[str]:
    """Phase description の存在をチェック (01-89番台のみ)"""
    errors: List[str] = []

    # 00, 97-99番台、パスファイルはスキップ
    if (path.name.startswith("00_") or
        path.name.startswith(("97_", "98_", "99_")) or
        path.name.endswith("_paths.mdc")):
        return []

    # 01-89番台のルールファイル
    if re.match(r"^\d{2}_.*\.mdc$", path.name):
        if "phase_1_description:" not in content and "phase_2_description:" not in content:
            errors.append(
                f"{path}: Phase description セクションが見つかりません。\n"
                f"  【修正方法】system_capabilities の後に以下のPhaseセクションを追加してください:\n\n"
                f"  # ======== Phase 1: {{フェーズ1名}}フェーズ ========\n\n"
                f"  phase_1_description: |\n"
                f"    フェーズ1の目的と処理内容の詳細説明（3-4行）\n"
                f"    具体的な処理ステップの概要と期待される成果物\n"
                f"    品質基準と完了条件の明確化\n\n"
                f"  # ======== Phase 2: {{フェーズ2名}}フェーズ ========\n\n"
                f"  phase_2_description: |\n"
                f"    フェーズ2の目的と処理内容の詳細説明（3-4行）\n"
                f"    具体的な処理ステップの概要と期待される成果物\n"
                f"    品質基準と完了条件の明確化\n\n"
                f"  【理由】標準フォーマットでは最低1つ以上のPhase descriptionが必須です"
            )

    return errors


def check_quality_metrics(path: Path, content: str) -> List[str]:
    """品質メトリクスをチェック (01-89番台のみ)"""
    warnings: List[str] = []

    # 00, 97-99番台、パスファイルはスキップ
    if (path.name.startswith("00_") or
        path.name.startswith(("97_", "98_", "99_")) or
        path.name.endswith("_paths.mdc")):
        return []

    # 01-89番台のルールファイル
    if not re.match(r"^\d{2}_.*\.mdc$", path.name):
        return []

    # 1. prompt_purpose の文字数チェック（80-400文字推奨、50文字未満はエラー級）
    purpose_match = re.search(r'prompt_purpose:\s*\|\s*\n((?:.*\n)*?)(?=\n\S|\Z)', content, re.MULTILINE)
    if purpose_match:
        purpose_text = purpose_match.group(1).strip()
        char_count = len(purpose_text)
        if char_count < 50:
            warnings.append(
                f"{path}: 🔴 prompt_purpose が著しく不足（{char_count}文字）\n"
                f"  【必須】最低80文字、推奨100-400文字で具体的に記述してください\n"
                f"  【内容】誰が・何のために・どの成果物で支援するか、1-2文で明確化\n"
                f"  【例】「Vtuberプロデューサーが視聴者層の心理的ニーズを理解し、ファンエンゲージメントを高めるための心理分析レポートを生成します。」"
            )
        elif char_count < 80:
            warnings.append(
                f"{path}: ⚠️  prompt_purpose が不足（{char_count}文字）\n"
                f"  【推奨】100-400文字でより詳細に記述してください\n"
                f"  【内容】誰が・何のために・どの成果物で・どのように支援するかを明確化"
            )
        elif char_count > 500:
            warnings.append(
                f"{path}: ⚠️  prompt_purpose が長すぎます（{char_count}文字）\n"
                f"  【推奨】100-400文字で簡潔に記述してください"
            )

    # 2. prompt_why_questions の文字数チェック（60-400文字推奨）
    why_questions_match = re.search(r'prompt_why_questions:\s*\|\s*\n((?:.*\n)*?)(?=\n\S|\Z)', content, re.MULTILINE)
    if why_questions_match:
        why_questions_text = why_questions_match.group(1).strip()
        wq_char_count = len(why_questions_text)
        if wq_char_count < 40:
            warnings.append(
                f"{path}: 🔴 prompt_why_questions が著しく不足（{wq_char_count}文字）\n"
                f"  【必須】最低60文字、推奨80-400文字で記述してください\n"
                f"  【内容】なぜ質問が必要か、何を揃えるかを1-4行で具体的に説明\n"
                f"  【例】「視聴者の心理的ニーズ（自律性・有能感・関係性）を特定するため、具体的な視聴動機・感情的つながり・コミュニティ体験を収集します。」"
            )
        elif wq_char_count < 60:
            warnings.append(
                f"{path}: ⚠️  prompt_why_questions が不足（{wq_char_count}文字）\n"
                f"  【推奨】80-400文字で、質問の必要性と収集情報を詳細に記述してください"
            )

    # 3. prompt_why_templates の文字数チェック（40-300文字推奨）
    why_templates_match = re.search(r'prompt_why_templates:\s*\|\s*\n((?:.*\n)*?)(?=\n\S|\Z)', content, re.MULTILINE)
    if why_templates_match:
        why_templates_text = why_templates_match.group(1).strip()
        wt_char_count = len(why_templates_text)
        if wt_char_count < 30:
            warnings.append(
                f"{path}: 🔴 prompt_why_templates が著しく不足（{wt_char_count}文字）\n"
                f"  【必須】最低40文字、推奨60-300文字で記述してください\n"
                f"  【内容】テンプレートを使う理由を1-3行で説明\n"
                f"  【例】「標準化されたレポート構造により、分析結果の再現性を確保し、他のVtuberとの比較可能性を維持します。」"
            )
        elif wt_char_count < 40:
            warnings.append(
                f"{path}: ⚠️  prompt_why_templates が不足（{wt_char_count}文字）\n"
                f"  【推奨】60-300文字で、テンプレート使用の理由と効果を詳細に記述してください"
            )

    # 4. prompt_principles の文字数チェック（60-500文字推奨）
    principles_match = re.search(r'prompt_principles:\s*\|\s*\n((?:.*\n)*?)(?=\n\S|\Z)', content, re.MULTILINE)
    if principles_match:
        principles_text = principles_match.group(1).strip()
        pp_char_count = len(principles_text)
        # 箇条書き数をカウント
        bullet_count = len(re.findall(r'^\s*[-•]\s+', principles_text, re.MULTILINE))

        if pp_char_count < 40:
            warnings.append(
                f"{path}: 🔴 prompt_principles が著しく不足（{pp_char_count}文字、{bullet_count}項目）\n"
                f"  【必須】最低60文字、推奨100-500文字、3-6項目で記述してください\n"
                f"  【内容】運用原則を箇条書きで明示\n"
                f"  【必須項目】事実記録・欠損明示・根拠明記・推測禁止など"
            )
        elif pp_char_count < 60:
            warnings.append(
                f"{path}: ⚠️  prompt_principles が不足（{pp_char_count}文字、{bullet_count}項目）\n"
                f"  【推奨】100-500文字、3-6項目で運用原則を詳細に記述してください"
            )

        if bullet_count < 3:
            warnings.append(
                f"{path}: ⚠️  prompt_principles の項目数が不足（{bullet_count}項目）\n"
                f"  【推奨】最低3項目、推奨4-6項目の運用原則を記述してください\n"
                f"  【例】「- 事実に基づく記録」「- 欠損の明示」「- 根拠の明記」「- 推測の禁止」"
            )

    # 5. system_capabilities の項目数チェック（6項目推奨）
    capabilities_section = re.search(r'system_capabilities:(.*?)(?=\n#|$)', content, re.DOTALL)
    if capabilities_section:
        capability_items = re.findall(r'^\s+\w+:', capabilities_section.group(1), re.MULTILINE)
        cap_count = len(capability_items)
        if cap_count < 6:
            warnings.append(
                f"{path}: ⚠️  system_capabilities の項目数が不足（{cap_count}項目）\n"
                f"  【推奨】6項目で詳細に記述してください\n"
                f"  【例】core_function, data_processing, workflow_management, quality_assurance, integration_support, user_experience"
            )
        # 各capability の文字数チェック（30文字以上推奨）
        for item in capability_items:
            item_match = re.search(rf'{item.strip()}.*?"([^"]+)"', capabilities_section.group(1))
            if item_match:
                item_text = item_match.group(1)
                if len(item_text) < 30:
                    warnings.append(
                        f"{path}: ⚠️  {item.strip()} の説明が短すぎます（{len(item_text)}文字）\n"
                        f"  【推奨】30文字以上で詳細に記述してください"
                    )

    # 6. 質問数チェック（5-10個推奨）
    # 実際の質問セクションを検索（initialization_questions, *_analysis_questions など）
    # prompt_why_questions は除外する
    questions_section = re.search(r'(?:initialization_questions|(?:(?!prompt_why)\w+)_questions):(.*?)(?=\n#|\n\w+_\w+:|$)', content, re.DOTALL)
    if questions_section and 'prompt_' not in questions_section.group(0):
        question_items = re.findall(r'- key:', questions_section.group(1))
        q_count = len(question_items)
        if q_count < 5:
            warnings.append(
                f"{path}: ⚠️  質問数が不足（{q_count}個）\n"
                f"  【推奨】5-10個の質問で十分な情報を収集してください\n"
                f"  【理由】最低5個の質問がないと分析の質が低下します"
            )
        elif q_count == 5:
            warnings.append(
                f"{path}: ⚠️  質問数が最小値（5個）です\n"
                f"  【推奨】6-10個に増やすとより詳細な分析が可能です"
            )

    # 7. テンプレートの文字数チェック（200文字以上推奨）
    template_section = re.search(r'_template:\s*\|\s*\n((?:.*\n)*?)(?=\n#|$)', content, re.MULTILINE)
    if template_section:
        template_text = template_section.group(1).strip()
        template_char_count = len(template_text)
        if template_char_count < 200:
            warnings.append(
                f"{path}: ⚠️  テンプレートが短すぎます（{template_char_count}文字）\n"
                f"  【推奨】200文字以上で実用的なテンプレートを作成してください\n"
                f"  【理由】短すぎると即利用可能な品質になりません"
            )

    # 8. Phase description の文字数チェック（各100文字以上推奨）
    for phase_num in [1, 2]:
        phase_match = re.search(rf'phase_{phase_num}_description:\s*\|\s*\n((?:.*\n)*?)(?=\n\S|\Z)', content, re.MULTILINE)
        if phase_match:
            phase_text = phase_match.group(1).strip()
            phase_char_count = len(phase_text)
            if phase_char_count < 100:
                warnings.append(
                    f"{path}: ⚠️  phase_{phase_num}_description が短すぎます（{phase_char_count}文字）\n"
                    f"  【推奨】100-300文字で詳細に記述してください（3-4行）\n"
                    f"  【内容】目的・処理ステップ・成果物・品質基準を含める"
                )

    return warnings


def iter_rule_files() -> List[Path]:
    if not RULE_DIR.exists():
        return []
    return sorted(RULE_DIR.glob("*.mdc"))


def validate() -> int:
    errors: List[str] = []
    warnings: List[str] = []
    files = iter_rule_files()
    if not files:
        print("No .cursor/rules/*.mdc files found. Run this script inside an agent directory.")
        return 1

    print("=" * 80)
    print("エージェントルールファイル検証")
    print("=" * 80)
    print()

    for file_path in files:
        text = file_path.read_text(encoding="utf-8")
        rel = file_path.relative_to(ROOT)

        print(f"検証中: {rel}")

        # エラーチェック（必須項目）
        file_errors = []
        file_errors.extend(check_front_matter(rel, text))
        file_errors.extend(check_path_comments(rel, text))
        file_errors.extend(check_path_reference(rel, text))
        file_errors.extend(check_separators(rel, text))
        file_errors.extend(check_prompt_sections(rel, text))
        file_errors.extend(check_system_capabilities(rel, text))
        file_errors.extend(check_phase_descriptions(rel, text))

        # 品質チェック（推奨項目）
        file_warnings = check_quality_metrics(rel, text)

        if file_errors:
            print(f"  ✗ エラー検出 ({len(file_errors)}件)")
            for error in file_errors:
                print(f"    - {error.split(': ', 1)[1] if ': ' in error else error}")
            errors.extend(file_errors)
        elif file_warnings:
            print(f"  ⚠️  品質警告 ({len(file_warnings)}件)")
            for warning in file_warnings:
                print(f"    - {warning.split(': ', 1)[1] if ': ' in warning else warning}")
            warnings.extend(file_warnings)
        else:
            print(f"  ✓ OK")

        print()

    print("=" * 80)
    if errors:
        print(f"❌ 検証失敗: {len(errors)}件のエラーが見つかりました")
        print("=" * 80)
        return 1

    if warnings:
        print(f"⚠️  品質警告: {len(warnings)}件の改善推奨項目があります")
        print("=" * 80)
        print()
        print("【注意】警告は検証合格扱いですが、品質向上のため改善を推奨します。")
        print()
        return 0

    print("✓ 全てのルールファイルが検証を通過しました（エラー・警告なし）")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(validate())
