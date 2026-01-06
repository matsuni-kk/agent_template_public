# フレームワーク調査ログ - Slack SDK App Agent

作成日: 2026-01-03

---

## 1. 参照フレームワーク

### フレームワーク1: Slack Bolt Framework
- 名称: Bolt for Python / JavaScript / Java
- 公式/準拠元: Slack Technologies, LLC
- URL: https://docs.slack.dev/tools/bolt-js/ / https://github.com/slackapi/bolt-python
- 取得日時: 2026-01-03

### フレームワーク2: Slack Platform / App Manifest
- 名称: Slack Platform & App Manifest Specification
- 公式/準拠元: Slack Technologies, LLC
- URL: https://api.slack.com/concepts/manifests
- 取得日時: 2026-01-03

### フレームワーク3: Deno Slack SDK（次世代プラットフォーム）
- 名称: Deno Slack SDK
- 公式/準拠元: Slack Technologies, LLC
- URL: https://api.slack.com/automation/workflows
- 取得日時: 2026-01-03

---

## 2. 要点（業務観点）

### 主要概念

#### Bolt Framework
- **イベント駆動アーキテクチャ**: message, app_mention, reaction_added等のイベントをリッスン
- **ミドルウェアパターン**: リクエスト処理のパイプライン構築
- **ack()応答必須**: 3秒以内にSlackへ確認応答を返す必要あり
- **Socket Mode vs HTTP**:
  - Socket Mode: WebSocket接続、ファイアウォール内で動作可能
  - HTTP: 公開エンドポイント必要、本番環境向け

#### App Manifest
- **v1 vs v2**: Deno Slack SDKはv2専用、従来アプリは両方対応
- **ポータビリティ**: GitHubでバージョン管理可能
- **スコープ定義**: OAuth権限、イベント購読、スラッシュコマンドを一元管理

#### Block Kit
- **構造化UI**: sections, actions, inputs等のブロックで構成
- **インタラクティブ**: ボタン、セレクトメニュー、日付ピッカー等
- **Block Kit Builder**: ビジュアルプロトタイピングツール

### ベストプラクティス

1. **応答時間管理**
   - 3秒以内にack()を返す
   - 時間のかかる処理はバックグラウンド実行（asyncio, ExecutorService等）

2. **セキュリティ**
   - RequestVerification必須（署名検証）
   - トークンは環境変数で管理
   - .envファイルはバージョン管理から除外

3. **インタラクション設計**
   - 一度限りのアクションはメッセージ更新でボタン削除
   - エラーハンドリングを適切に実装

4. **開発環境**
   - ngrokで開発サーバーを公開
   - Socket Modeで開発すると公開エンドポイント不要

### 注意点

- **2025年3月31日**: レガシーカスタムボット非サポート化
- **ワークフロー自動化**: 有料プランまたはDeveloper Program必須
- **レート制限**: Bolt SDKが自動処理するが、設計時に考慮必要

---

## 3. 本エージェントへの適用方針

### 適用箇所
- **機能設計**: Bolt Frameworkのイベントハンドラーパターンを全面採用
- **テンプレート**: App Manifest v1/v2両対応のテンプレート提供
- **質問項目**: Socket Mode/HTTP、対応言語、必要スコープのヒアリング

### 反映方法
1. **プロジェクト初期化Skill**: Bolt (Python/JS/Java)のボイラープレート生成
2. **App Manifest Skill**: ヒアリング結果からmanifest.yaml自動生成
3. **イベントハンドラーSkill**: 各イベントタイプ別のコードテンプレート
4. **Block Kit Skill**: UIパターン別のJSON生成

### 除外/留意事項
- Enterprise Grid固有機能は将来対応（P3）
- Deno Slack SDKは基本機能確立後に対応（P3）
- Slack Connect機能は初期スコープ外

---

## 4. 出典リスト

| # | タイトル | URL | 取得日時 |
|---|----------|-----|----------|
| 1 | Slack platform overview | https://docs.slack.dev/ | 2026-01-03 |
| 2 | Bolt for JavaScript | https://docs.slack.dev/tools/bolt-js/ | 2026-01-03 |
| 3 | Bolt for Python (GitHub) | https://github.com/slackapi/bolt-python | 2026-01-03 |
| 4 | Bolt for JavaScript (GitHub) | https://github.com/slackapi/bolt-js | 2026-01-03 |
| 5 | App manifests | https://api.slack.com/concepts/manifests | 2026-01-03 |
| 6 | App manifests (Developer Docs) | https://docs.slack.dev/app-manifests/ | 2026-01-03 |
| 7 | Workflows | https://api.slack.com/automation/workflows | 2026-01-03 |
| 8 | Slack Quickstart | https://docs.slack.dev/quickstart/ | 2026-01-03 |
| 9 | Hello World Bolt Tutorial | https://api.slack.com/tutorials/tracks/hello-world-bolt | 2026-01-03 |
| 10 | Java Slack SDK - Bolt Basics | https://tools.slack.dev/java-slack-sdk/guides/bolt-basics | 2026-01-03 |

---

## 5. 調査完了確認
- [x] Web検索で業界標準を確認した
- [x] 出典を最低1件記録した
- [x] 適用方針を決定した
- [x] draft_requirements.mdに反映した

**保存先**: Flow/202601/2026-01-03/slack_sdk_agent/framework_research.md
**framework_research_done**: true
