# フレームワーク調査ログ - Electron App Factory Agent

作成日: 2026-01-04

---

## 1. 参照フレームワーク

### フレームワーク1: Electron Security（公式）
- 名称: Electron Security Tutorial / Checklist
- 公式/準拠元: electronjs.org
- URL: https://www.electronjs.org/docs/latest/tutorial/security
- 取得日時: 2026-01-04

### フレームワーク2: Packaging and Distribution（公式）
- 名称: Packaging and Distribution
- 公式/準拠元: electronjs.org
- URL: https://www.electronjs.org/docs/latest/tutorial/packaging-and-distribution
- 取得日時: 2026-01-04

### フレームワーク3: Electron Forge（公式）
- 名称: Electron Forge
- 公式/準拠元: electronforge.io
- URL: https://www.electronforge.io/
- 取得日時: 2026-01-04

---

## 2. 要点（実装観点）

### セキュリティ（最低限）
- RendererにNode権限を渡さない（`nodeIntegration`無効）
- `contextIsolation` を有効にし、Preload + `contextBridge`で安全なAPIのみ公開
- 外部URLの遷移/新規ウィンドウを制御（`setWindowOpenHandler`等）
- CSPを設定し、スクリプト注入リスクを下げる

### パッケージング/配布
- 配布物生成は「Packaging（実行可能な束ね）」と「Make（インストーラ/配布形式）」が分かれる
- Electron Forgeは `package/make/publish` の流れでクロスプラットフォーム配布を扱う
- 本エージェントの配布ターゲット: Windows（`msi`/`exe`）, macOS（`dmg`）
- Forge想定Makers（例）: `@electron-forge/maker-wix`（msi）, `@electron-forge/maker-squirrel`（exe）, `@electron-forge/maker-dmg`（dmg）
- 署名・Notarizeは必要だが、証明書管理が伴うため初期は手順と設定枠のみ（将来機能）

### スキャフォールド
- 公式に近い流儀（Forge / create-electron-app）をベースにすることで、保守性と互換性が上がる

---

## 3. 本エージェントへの適用方針

### 適用箇所
- **雛形生成Skill**: Main/Renderer/Preload分離とIPC骨組みを標準化
- **保存/台帳Skill**: 生成物の配置規約とメタデータを固定し、アプリを跨いだ管理を可能にする
- **ビルドSkill**: Forgeの `package/make` を前提に共通化（Windows: msi/exe, macOS: dmg）

### 除外/留意事項
- 証明書/署名/Notarizeは環境依存が強い（初期スコープ外、将来機能で対応）
- 具体的なテンプレートはReactをデフォルトとする（詳細はSkillで決める）

---

## 4. 出典リスト

| # | タイトル | URL | 取得日時 |
|---|----------|-----|----------|
| 1 | Electron Security | https://www.electronjs.org/docs/latest/tutorial/security | 2026-01-04 |
| 2 | Packaging and Distribution | https://www.electronjs.org/docs/latest/tutorial/packaging-and-distribution | 2026-01-04 |
| 3 | Electron Forge | https://www.electronforge.io/ | 2026-01-04 |

---

## 5. 調査完了確認
- [x] Web検索で公式の推奨を確認した
- [x] 出典を最低1件記録した
- [x] 適用方針を決定した
- [x] draft_requirements.mdに反映した

**保存先**: Flow/202601/2026-01-04/electron_app_factory_agent/framework_research.md
**framework_research_done**: true
