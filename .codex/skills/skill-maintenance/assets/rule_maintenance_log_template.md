# rule-maintenance - rule_maintenance_log_template

## ログテンプレート

rule_maintenance_log_template: |
  # Rule Maintenance Log - {{target_rule}}
  **日時:** {{meta.timestamp}}
  **担当:** {{meta.user}}
  **操作種別:** {{operation}}

  ## 変更概要
  - 対象ルール: {{target_rule}}
  - 追加番号: {{new_rule_number}}
  - 追加コード: {{new_rule_code}}
  - 追加名称: {{new_rule_name}}
  - 変更箇所: {{change_scope}}
  - 期待する成果: {{expected_outcome}}
  - 変更理由: {{reason}}

  ## 影響範囲と対応
  - paths 更新: {{paths_update}}
  - master_triggers 更新: {{master_trigger_update}}
  - タスクリスト同期: {{tasklist_sync}}

  ## 検証とロールバック
  - 検証手順: {{verification_plan}}
  - ロールバック計画: {{rollback_plan}}

  ## 埋め込み／更新作業
  {{completion_plan}}

  ## レビュー情報
  - レビュワー: {{reviewer}}
  - レビュー期限: {{due}}

  ---
  - Flowログ保存先: {{patterns.rule_maintenance_log}}