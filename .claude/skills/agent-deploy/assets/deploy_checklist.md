# Agent Deploy チェックリスト

## 事前確認
- [ ] gh CLI がインストール済み
- [ ] gh CLI が認証済み（`gh auth status`で確認）
- [ ] 対象エージェントディレクトリが存在する

## 必須ファイル確認
- [ ] CLAUDE.md が存在する
- [ ] README.md が存在する
- [ ] .claude/skills/ ディレクトリが存在する
- [ ] 少なくとも1つのSkillが存在する

## 推奨ファイル確認
- [ ] scripts/update_agent_master.py が存在する
- [ ] scripts/validate_skills.py が存在する
- [ ] .gitignore が存在する

## マルチプラットフォーム同期確認
- [ ] AGENTS.md が CLAUDE.md と同期している
- [ ] .github/copilot-instructions.md が同期している
- [ ] .gemini/GEMINI.md が同期している
- [ ] .kiro/steering/KIRO.md が同期している

## セキュリティ確認
- [ ] .env ファイルが .gitignore に含まれている
- [ ] APIキー等の機密情報がコードに含まれていない
- [ ] credentials.json 等が除外されている

## リポジトリ設定
- [ ] リポジトリ名が適切（スネークケース推奨）
- [ ] プライベートリポジトリとして作成
- [ ] 初期コミットメッセージが適切

## デプロイ後クリーンアップ
- [ ] （ユーザー許可後）ローカルの `output/{agent_name}/` を削除
- [ ] （必要に応じて）`Flow/` などの一時ディレクトリも削除
