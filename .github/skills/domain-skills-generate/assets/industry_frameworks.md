# 業界標準フレームワーク リファレンス

## ドメイン別フレームワーク一覧

| ドメイン | 標準フレームワーク | 認定/発行元 | 主要プロセス |
|----------|-------------------|------------|--------------|
| 会計 | GAAP/IFRS | FASB/IASB | 仕訳、決算、財務諸表、税務、監査 |
| マーケティング | AMA Marketing BOK | American Marketing Association | 市場分析、戦略立案、キャンペーン、効果測定 |
| プロジェクト管理 | PMBOK | PMI | 立上げ、計画、実行、監視、終結 |
| ビジネス分析 | BABOK | IIBA | 要求抽出、分析、検証、変更管理 |
| IT開発 | Agile/Scrum | Scrum Alliance | 要件定義、設計、実装、テスト、デプロイ |
| 人事 | SHRM | Society for Human Resource Management | 採用、育成、評価、報酬、労務 |
| 製造 | ISO 9001 | ISO | 設計、調達、生産、検査、出荷 |
| 医療 | HL7/FHIR | HL7 International | 診察、診断、治療計画、経過観察 |
| 教育 | ADDIE | US Army | 分析、設計、開発、実施、評価 |
| 法務 | - | 各国法曹協会 | 契約審査、コンプライアンス、訴訟対応 |
| 品質管理 | Six Sigma | Motorola/GE | Define, Measure, Analyze, Improve, Control |
| サービス管理 | ITIL | AXELOS | 戦略、設計、移行、運用、継続的改善 |
| リスク管理 | COSO ERM | COSO | 目標設定、リスク識別、評価、対応、監視 |
| 調達 | ISM | Institute for Supply Management | 需要計画、調達、契約、納品、支払 |
| 財務分析 | CFA | CFA Institute | 倫理、定量分析、経済、財務報告、ポートフォリオ |

## 各フレームワーク詳細

### PMBOK (Project Management Body of Knowledge)

**プロセス群:**
1. 立上げ (Initiating)
   - プロジェクト憲章作成
   - ステークホルダー特定
2. 計画 (Planning)
   - スコープ定義
   - スケジュール作成
   - コスト見積り
   - リスク計画
3. 実行 (Executing)
   - チーム育成
   - 品質保証
   - 調達実行
4. 監視・コントロール (Monitoring & Controlling)
   - 変更管理
   - パフォーマンス報告
5. 終結 (Closing)
   - 成果物引渡し
   - 教訓文書化

**推奨Skills構成:**
- `pmbok-initiate-charter` - 憲章作成
- `pmbok-plan-scope` - スコープ計画
- `pmbok-plan-schedule` - スケジュール計画
- `pmbok-plan-cost` - コスト計画
- `pmbok-plan-risk` - リスク計画
- `pmbok-execute-team` - チーム管理
- `pmbok-monitor-change` - 変更管理
- `pmbok-close-project` - プロジェクト終結

### BABOK (Business Analysis Body of Knowledge)

**知識エリア:**
1. ビジネスアナリシス計画とモニタリング
2. 引き出しとコラボレーション
3. 要求ライフサイクル管理
4. 戦略分析
5. 要求分析とデザイン定義
6. ソリューション評価

**推奨Skills構成:**
- `babok-plan-analysis` - BA計画
- `babok-elicit-requirements` - 要求引き出し
- `babok-analyze-strategy` - 戦略分析
- `babok-design-solution` - ソリューション設計
- `babok-evaluate-solution` - ソリューション評価

### GAAP/IFRS (会計基準)

**主要プロセス:**
1. 取引記録
   - 仕訳作成
   - 元帳転記
2. 期末処理
   - 試算表作成
   - 決算整理
3. 財務諸表作成
   - 貸借対照表
   - 損益計算書
   - キャッシュフロー計算書
4. 監査対応
   - 証憑管理
   - 監査報告

**推奨Skills構成:**
- `accounting-create-journal` - 仕訳作成
- `accounting-post-ledger` - 元帳転記
- `accounting-prepare-trial` - 試算表作成
- `accounting-close-period` - 決算処理
- `accounting-create-bs` - 貸借対照表作成
- `accounting-create-pl` - 損益計算書作成
- `accounting-create-cf` - CF計算書作成
- `accounting-prepare-audit` - 監査準備

### AMA Marketing BOK

**コアコンピテンシー:**
1. 市場調査・分析
2. マーケティング戦略
3. ブランド管理
4. プロダクト管理
5. 価格戦略
6. チャネル管理
7. マーケティングコミュニケーション
8. デジタルマーケティング

**推奨Skills構成:**
- `marketing-analyze-market` - 市場分析
- `marketing-define-strategy` - 戦略立案
- `marketing-manage-brand` - ブランド管理
- `marketing-plan-product` - 製品計画
- `marketing-set-pricing` - 価格設定
- `marketing-plan-channel` - チャネル計画
- `marketing-create-campaign` - キャンペーン作成
- `marketing-measure-performance` - 効果測定

### SHRM (人事管理)

**HR機能領域:**
1. 人材獲得
2. 人材開発
3. 報酬・福利厚生
4. 従業員関係
5. 労務管理
6. HR情報管理

**推奨Skills構成:**
- `hr-plan-workforce` - 人員計画
- `hr-recruit-talent` - 採用
- `hr-onboard-employee` - オンボーディング
- `hr-develop-training` - 研修開発
- `hr-evaluate-performance` - 評価
- `hr-manage-compensation` - 報酬管理
- `hr-handle-relations` - 労使関係
- `hr-ensure-compliance` - コンプライアンス

## フレームワーク適用ガイドライン

### 適用手順
1. ドメイン特定 → 該当フレームワーク選択
2. フレームワークのプロセス/フェーズを列挙
3. 各プロセスを1 Skill = 1 WFでマッピング
4. ドメイン固有の追加機能を補完
5. 業界用語・テンプレートを反映

### カスタマイズポイント
- 業界慣行に合わせた用語調整
- 地域・法規制への対応
- 組織固有プロセスの追加
- 統合ポイントの明確化
