# rule-maintenance - rule_check_report_template

rule_check_report_template: |
  # Rule Structure Check Report - {{target_rules}}
  **日時:** {{meta.timestamp}}
  **担当:** {{meta.user}}

  ## 対象範囲
  - ルール: {{target_rules}}

  ## フォーマット確認
  - フロントマター/グロブ/パス参照: {{format_status}}
  - タイトル帯・区切り: {{delimiter_status}}

  ## 整合性チェック
  - master_triggers との整合: {{trigger_alignment}}
  - paths 定義との整合: {{paths_alignment}}
  - Flow/Stock/Archived の運用メモ: {{draft_vs_stock}}

  ## 所見・警告
  {{warnings}}

  ## 必要なアクション
  {{actions}}

  ---
  - レポート保存先: {{patterns.rule_check_log}}