# rule-maintenance - path_update_questions

path_update_questions: |
  - key: "target_paths_file"
    question: "更新対象のパス定義ファイル（00_master_rules.mdc または CLAUDE.md）"
  - key: "current_root"
    question: "現在設定されている root（絶対パス）"
  - key: "new_root"
    question: "変更後の root（絶対パス）"
  - key: "structure_changes"
    question: "新たに追加・変更するディレクトリ／パターン（箇条書きで記載）"
  - key: "affected_rules"
    question: "影響を受けるルール番号または成果物"
  - key: "validation_status"
    question: "`python3 scripts/validate_rules.py` の実行結果（pass/fail とログパス）"
  - key: "followup_tasks"
    question: "必要なフォローアップ（入力またはスキップ）（タスクリストへの追加、レビュー担当など）"