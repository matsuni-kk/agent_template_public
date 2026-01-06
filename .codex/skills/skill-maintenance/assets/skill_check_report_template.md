# skill-maintenance - skill_check_report_template

skill_check_report_template: |
  # Skill Structure Check Report - {{target_skill}}
  **日時:** {{meta.timestamp}}
  **担当:** {{meta.user}}

  ## 対象範囲
  - Skill: {{target_skill}}
  - パス: .codex/skills/{{target_skill}}/

  ## フォーマット確認
  - SKILL.md フロントマター: {{frontmatter_status}}
  - 必須セクション存在: {{sections_status}}
  - Resources参照整合: {{resources_status}}

  ## 構造チェック
  - assets/ 存在: {{has_assets}}
  - questions/ 存在: {{has_questions}}
  - evaluation/ 存在: {{has_evaluation}}

  ## 整合性チェック
  - CLAUDE.md ワークフロー索引との整合: {{workflow_alignment}}
  - パス辞書との整合: {{paths_alignment}}

  ## 所見・警告
  {{warnings}}

  ## 必要なアクション
  {{actions}}

  ---
  - レポート保存先: {{patterns.skill_maintenance_log}}
