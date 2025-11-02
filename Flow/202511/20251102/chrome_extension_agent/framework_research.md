# Chrome拡張機能開発 - フレームワーク調査ログ

作成日時: 2025-11-02
調査者: Claude Code

## 参照フレームワーク

### 1. Manifest V3 (Chrome Extensions Platform)
- **名称**: Chrome Extensions Manifest V3
- **公式/準拠元**: Google Chrome for Developers
- **URL**: https://developer.chrome.com/docs/extensions/develop/migrate/what-is-mv3
- **取得日時**: 2025-11-02

### 2. Chrome Extension Best Practices
- **名称**: Chrome Web Store Best Practices
- **公式/準拠元**: Google Chrome Web Store
- **URL**: https://developer.chrome.com/docs/webstore/best-practices
- **取得日時**: 2025-11-02

## 要点（業務観点）

### Manifest V3の重要変更点（2025年必須）
1. **Service Workers導入**: Background Pageの代わりにService Workerを使用
   - メモリ使用量削減、パフォーマンス向上
   - セキュリティ強化（拡張機能データへのアクセス制限）

2. **権限システムの詳細化**: ユーザーデータ（履歴、ブックマーク、ネットワーク）へのアクセス制限強化

3. **セキュリティ改善**: リモートホストコードの実行禁止（未審査コードの実行防止）

### 標準プロジェクト構造
```
/project-root
  ├── manifest.json         # ルート必須：バージョン、権限、メタ情報
  ├── /src
  │   ├── /css              # スタイルシート
  │   ├── /html             # HTMLファイル
  │   ├── /images           # 画像リソース
  │   ├── /js               # JavaScriptモジュール
  │   │   ├── popup.js      # Popup UI制御
  │   │   ├── background.js # Service Worker（MV3）
  │   │   └── content.js    # Content Script
  │   └── /libs             # サードパーティライブラリ
  ├── /build                # ビルド成果物（.crx）
  └── package.json          # プロジェクト情報
```

### ベストプラクティス（2025年版）
1. **パフォーマンス・セキュリティ優先**: 軽量化、Manifest V3準拠、Googleガイドライン遵守
2. **段階的移行**: 新機能追加とMV3移行を分離（権限警告によるユーザー離脱防止）
3. **一般的な失敗**: 機能過多、不要な権限要求、ガイドライン無視、UI/UX設計不備、更新不足
4. **データセキュリティ**: HTTPS経由でのユーザーデータ送信、セキュリティ脅威の排除

### 技術スタック推奨
- **言語**: HTML, CSS, JavaScript
- **フレームワーク**: React or Vue.js（動的UI向け）
- **API**: Chrome Extensions APIs（storage, tabs, runtime等）

## 本エージェントへの適用方針

### 適用箇所
1. **プロジェクト初期化ルール（01番）**: 標準フォルダ構造の自動生成
2. **Manifest生成ルール（02番）**: Manifest V3準拠のmanifest.json作成
3. **コンポーネント実装ルール（03-05番）**: popup, background, content script実装支援
4. **バリデーションルール（06番）**: Manifest V3要件チェック、権限検証、セキュリティチェック
5. **テスト・デバッグルール（07番）**: Chrome開発者モードでの読み込みテスト支援

### 反映方法
- **質問設計**: Manifest V3必須項目（name, version, manifest_version, permissions等）を質問で収集
- **テンプレート**: Manifest V3標準形式、各種スクリプトのボイラープレート提供
- **バリデーション**: manifest.jsonの必須フィールドチェック、Service Worker構文確認
- **ワークフロー**: フォルダ生成 → manifest作成 → コンポーネント実装 → バリデーション → 修正ループ

### 除外/留意事項
- **Manifest V2対応**: 2025年時点で非推奨のため、V3に特化
- **リモートコード実行**: セキュリティ上禁止されているため、エージェントでも対応しない
- **複雑なフレームワーク統合**: 初期バージョンではVanilla JSを推奨、React/Vue.jsはオプション扱い
- **Chrome Web Store公開**: パッケージング支援までで、実際の公開手続きはスコープ外

## 出典リスト

1. **Chrome Extension Development Guide 2025**
   - URL: https://www.diego-rodriguez.work/blog/chrome-extension-development-guide
   - 取得日時: 2025-11-02

2. **Mastering Chrome Extension Manifest v3: A Step-by-Step Tutorial**
   - URL: https://www.codedbrainy.com/mastering-chrome-extension-manifest-v3-a-step-by-step-tutorial-for-developers/
   - 取得日時: 2025-11-02

3. **Chrome Extensions Best Practices (Official)**
   - URL: https://developer.chrome.com/docs/webstore/best-practices
   - 取得日時: 2025-11-02

4. **Chrome Extension Project Structure Guide**
   - URL: https://medium.com/@fabio.sabbion/how-to-organize-a-chrome-extension-project-10d35e93b094
   - 取得日時: 2025-11-02

5. **Chrome Extension Skeleton (GitHub)**
   - URL: https://github.com/salsita/chrome-extension-skeleton
   - 取得日時: 2025-11-02

---

**調査完了**: framework_research_done=true
**次ステップ**: enhanced_generate_agent.pyでエージェントスケルトン生成
