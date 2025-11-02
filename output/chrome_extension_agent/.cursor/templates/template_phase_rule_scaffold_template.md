---
description: "{{phase_name}}フェーズの質問リストとテンプレートを提供"
globs: 
alwaysApply: false
---
# {{new_rule_file}}
# 新フェーズ「{{phase_name}}」- ルール定義
# ----------------------------------------------------------
path_reference: "agent_paths.mdc"
# ----------------------------------------------------------
<!-- NOTE: 必要に応じて記述方法を変更してください -->

# ----------------------------------------------------------
# 1. 質問セット - {{phase_slug}}_questions
# ----------------------------------------------------------
{{phase_slug}}_questions:
  - category: "基本情報"
    items:
      - question: "プロジェクトID"
        key: project_id
        required: true
      - question: "TODO: 必要な質問1"
        key: question1
        required: true
      - question: "TODO: 必要な質問2"
        key: question2
        required: true

# ----------------------------------------------------------
# 2. テンプレート - {{phase_slug}}_template
# ----------------------------------------------------------
{{phase_slug}}_template: |
  ---
  doc_type: {{phase_slug}}_document
  project_id: {{project_id}}
  created_at: {{today}}
  version: v1.0
  ---

  # {{phase_name}} ドキュメント

  **プロジェクト**: {{project_id}}  
  **作成日**: {{today}}

  ## 1. 概要

  {{question1}}

  ## 2. 詳細

  {{question2}}

  ## 3. 次のステップ

  - [ ] TODO1
  - [ ] TODO2
  - [ ] TODO3