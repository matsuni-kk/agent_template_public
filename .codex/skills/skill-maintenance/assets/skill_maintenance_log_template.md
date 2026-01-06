# skill-maintenance - skill_maintenance_log_template

## ログテンプレート

skill_maintenance_log_template: |
  # Skill Maintenance Log - {{target_skill}}
  **日時:** {{meta.timestamp}}
  **担当:** {{meta.user}}
  **操作種別:** {{operation}}

  ## 変更概要
  - 対象Skill: {{target_skill}}
  - 新規Skill名: {{new_skill_name}}
  - 新規Skill説明: {{new_skill_description}}
  - 変更箇所: {{change_scope}}
  - 期待する成果: {{expected_outcome}}
  - 変更理由: {{reason}}

  ## 影響範囲と対応
  - paths 更新: {{paths_update}}
  - ワークフロー索引更新: {{workflow_index_update}}

  ## 検証とロールバック
  - 検証手順: {{verification_plan}}
  - ロールバック計画: {{rollback_plan}}

  ## 作成／更新作業
  {{completion_plan}}

  ## レビュー情報
  - レビュワー: {{reviewer}}
  - レビュー期限: {{due}}

  ---
  - Flowログ保存先: {{patterns.skill_maintenance_log}}
