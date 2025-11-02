# Chrome拡張機能作成エージェント - 作成タスクリスト

作成日時: 2025-11-02
エージェント名: Chrome Extension Agent
ドメイン: chrome_extension

## タスク進捗

### Phase 1: Discovery（要件定義・調査）
- [ ] タスクリスト作成（このファイル）
- [ ] 要件定義ファイル作成（draft_requirements.md）
- [ ] ヒアリング実施
- [ ] Chrome拡張のベストプラクティス・標準フレームワーク調査
- [ ] framework_research.md 作成・記入
- [ ] framework_research_done=true 確認

### Phase 2: Build（エージェント生成・ルール整備）
- [ ] root_path設定（templates.root_dirの確定）
- [ ] enhanced_generate_agent.py 実行
- [ ] agent_paths.mdc → chrome_extension_paths.mdc リネーム
- [ ] template_paths.mdc 削除
- [ ] Flow/Stock/Archived 構成承認取得
- [ ] 01_chrome_extension_initialization.mdc 作成
- [ ] 02〜番ルール作成（サンプル参照、作成、テストなど）
- [ ] 00_master_rules.mdc 整備
- [ ] chrome_extension_paths.mdc パターン追加
- [ ] 97/98/99番台ルールのカスタマイズ

### Phase 3: Validation（品質保証）
- [ ] scripts/validate_rules.py 実行
- [ ] エラー修正
- [ ] rule_check_log作成
- [ ] 再バリデーション（通過まで繰り返し）

### Phase 4: Release（完了・運用移行）
- [ ] 動作テスト実施
- [ ] 改善タスク整理
- [ ] 運用方針確認（ブラッシュアップ継続 or プライベートGit）

## 設定記録

### Root Path設定
- templates.root_dir: （未設定）
- root: （未設定）

### 承認事項
- Flow/Stock/Archived構成: （未承認）
- 要件定義: （未完了）
- フレームワーク調査: framework_research_done=false

## メモ・判断事項
- Chrome拡張機能の開発フロー: フォルダ作成 → 要件定義 → サンプル参照 → 作成 → バリデーション → 修正
