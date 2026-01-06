# rule-maintenance - rule_skeleton_template

# ======== テンプレート ========

rule_skeleton_template: |
  # NOTE: operation=add の場合のみ使用してください
  # 必須7セクション: Agent機能 → プロンプト → ワークフロー → 質問 → テンプレート → 次フェーズ連携 → エラーハンドリング
  ---
  description: {{meta.domain}} における {{function_name}} システム
  globs:
  alwaysApply: false
  ---
  # ==========================================================
  # {{nn}}_{{meta.domain}}_{{function_code}}.mdc - {{function_name}}システム
  # ==========================================================

  path_reference: "AGENTS.md"

  # ======== Agent機能 ========

  system_capabilities:
    core_function: "{{function_name}}に関する中核処理"
    data_processing: "データ整形・検証・変換"
    workflow_management: "ワークフロー制御と自動化"
    integration_support: "paths/他ルール連携"
    user_experience: "最小手順で正確に記録"

  execution_restrictions: |
    - 必須項目が欠損した状態で成果物を確定しない
    - テンプレート構造を独自に変更しない
    - paths定義にない保存先を使用しない

  # ======== プロンプト（目的と使い方） ========

  prompt_purpose: |
    本ルールは {{function_name}} の事実を整え、合意形成と次アクションを高速化します。出来事記録の標準を守り、再現可能性を高めます。

  prompt_why_questions: |
    欠落・曖昧・書式ブレを防ぐため、5W1HとType別DoD、詳細度（L1/L2/L3）を満たす質問を用意します。

  prompt_why_templates: |
    一貫したテンプレで列・見出し・用語を統一し、監査と自動化を容易にします。

  prompt_principles: |
    - 追記専用で記録し、過去行は不変とする。
    - 事実のみ記述し、Whyは当時の明言に限定する。
    - 出典必須、24時間以内に追記、Thread鎖を維持する。

  # ======== ワークフロー ========

  {{function_code}}_process: |
    - label: "1_input_collection"
      action: "call .claude/agents/{{nn}}_{{meta.domain}}_{{function_code}}.md => {{function_code}}_questions"
      description: "必要情報を収集"
    - label: "2_draft_creation"
      action: "create_markdown_file => {{function_code}}_template"
      description: "Flowにドラフト作成"
      output_path: "{{patterns.flow_date}}/draft_{{function_code}}.md"
    - label: "3_quality_check"
      action: "validate_output"
      description: "必須項目・形式を検証"
    - label: "4_completion"
      action: "finalize"
      description: "成果物確定・ログ記録"

  # ======== 質問 ========

  {{function_code}}_questions: |
    - key: "target_scope"
      question: "対象範囲・対象物を入力してください"
    - key: "expected_outcome"
      question: "期待する成果・完了条件を入力してください"
    - key: "additional_context"
      question: "補足情報があれば入力してください（入力またはスキップ）"

  # ======== テンプレート ========

  {{function_code}}_template: |
    # {{function_name}} - {{meta.timestamp}}

    ## 対象範囲
    {{target_scope}}

    ## 期待する成果
    {{expected_outcome}}

    ## 詳細
    {{additional_context}}

    ---
    - 作成日時: {{meta.timestamp}}
    - 担当: {{meta.user}}

  # ======== 次フェーズ連携 ========

  next_phases: |
    - on: "draft_created"
      rule: ".claude/agents/98_flow_assist.md"
      description: "ドラフト作成後、品質レビューへ"
    - on: "quality_ok"
      rule: ".claude/agents/97_flow_to_stock_rules.md"
      description: "品質OK後、Stock確定へ"
    - on: "needs_revision"
      rule: ".claude/agents/{{nn}}_{{meta.domain}}_{{function_code}}.md"
      description: "修正が必要な場合、再実行"

  # ======== エラーハンドリング ========

  error_handling: |
    - id: "missing_required_field"
      recovery_actions:
        - "{{function_code}}_questionsを再実行"
        - "欠損項目を特定して入力を促す"
    - id: "invalid_format"
      recovery_actions:
        - "テンプレート構造を確認"
        - "入力値の形式を修正"
    - id: "path_not_found"
      recovery_actions:
        - "patterns定義を確認"
        - "ディレクトリを作成"