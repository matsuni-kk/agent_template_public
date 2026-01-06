# rule-maintenance - rule_check_questions

rule_check_questions: |
  - key: "target_rules"
    question: "チェック対象のルール範囲（例: 00/agent_paths/01-05など）"
  - key: "format_status"
    question: "フロントマター・globs・path_reference の整合性は保たれていますか？（yes/no + 懸念点）"
  - key: "delimiter_status"
    question: "タイトル帯・Phase帯・下位区切りの維持状況を記録してください"
  - key: "trigger_alignment"
    question: "master_triggers と対象ルールの trigger/steps は一致していますか？差分があれば記載してください"
  - key: "paths_alignment"
    question: "00_master_rules.mdc のroot/dirs/patterns に保存先・テンプレパターンが定義され、参照キーが一致していますか？不足があれば列挙"
  - key: "draft_vs_stock"
    question: "Flow/Stock/Archived の遷移で追加すべきチェック項目や不足ファイルはありますか？（入力またはスキップ）"
  - key: "warnings"
    question: "確認中に見つかった警告・要フォロー事項（入力またはスキップ）"
  - key: "actions"
    question: "次のアクション（必要な修正・担当・期限）"