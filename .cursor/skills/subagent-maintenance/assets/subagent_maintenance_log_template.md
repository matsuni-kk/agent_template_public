# subagent-maintenance - subagent_maintenance_log_template

## ログテンプレート

subagent_maintenance_log_template: |
  # Subagent Maintenance Log - {{agent_name}}
  **日時:** {{meta.timestamp}}
  **担当:** {{meta.user}}
  **操作種別:** {{operation}}

  ## 変更概要
  - 対象エージェント: {{agent_name}}
  - ファイルパス: .claude/agents/{{agent_name}}.md
  - 変更箇所: {{change_scope}}
  - 期待する成果: {{expected_outcome}}
  - 変更理由: {{reason}}

  ## フロントマター情報
  - name: {{agent_name}}
  - description: {{agent_description}}
  - capabilities: {{capabilities}}
  - model: {{model}}

  ## 影響範囲と対応
  - ワークフロー索引更新: {{workflow_index_update}}
  - パス辞書更新: {{paths_update}}

  ## 検証とロールバック
  - 検証手順: {{verification_plan}}
  - ロールバック計画: {{rollback_plan}}

  ## 作成／更新作業
  {{completion_plan}}

  ## レビュー情報
  - レビュワー: {{reviewer}}
  - レビュー期限: {{due}}

  ---
  - Flowログ保存先: {{patterns.subagent_maintenance_log}}
