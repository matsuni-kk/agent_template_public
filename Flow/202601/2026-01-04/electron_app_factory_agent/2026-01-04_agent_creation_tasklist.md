# Electron App Factory Agent 作成タスクリスト

作成日: 2026-01-04
ステータス: 進行中

---

## Phase 1: Discovery（完了）
- [x] フレームワーク調査（Electron Security / Packaging / Forge）
- [x] draft_requirements.md 作成
- [x] framework_research.md 作成
- [x] ユーザー承認取得
  - [x] 要件承認（2026-01-04）
  - [x] 保存設計承認（aappごと保存, 2026-01-04）
  - [x] デフォルト雛形=Electron Forge（2026-01-04）
  - [x] デフォルトUI=React（2026-01-04）
  - [x] 配布形式=msi/exe/dmg（Win/macOS, 2026-01-04）

## Phase 2: Build
- [ ] skeleton-generate でエージェント骨格生成（output/electron_app_factory_agent）
- [ ] domain-skills-generate でSkills群生成
- [ ] subagent-generate（必要な場合）
- [ ] skill-maintenance で個別Skillの微調整

## Phase 3: Validation
- [ ] validate_skills.py 実行
- [ ] Skills/Agents/Commands 構文検証

## Phase 4: Release
- [ ] README.md 最終化
- [ ] 初回コミット（必要な場合）

---

## 確定事項
| 項目 | 値 | 承認日時 |
|------|-----|----------|
| ドメイン名 | electron_app_factory | 2026-01-04 |
| 雛形 | Electron Forge | 2026-01-04 |
| UI | React | 2026-01-04 |
| 配布形式 | Windows: msi/exe, macOS: dmg | 2026-01-04 |
| 保存方針 | Stock/programs/{app_slug}/ に保存 | 2026-01-04 |

## 未決事項
- [ ] パッケージマネージャ（npm/pnpm/yarn）
- [ ] 台帳形式（JSON固定 / Markdown併用）

---

**framework_research_done**: true
**next_action**: skeleton-generate
