# Skills設計ガイド

## 1. 設計原則

### 1.1 1 Skill = 1 WF（ワークフロー）
- 1つのSkillに複数の主成果物を含めない
- 「主成果物が1つに決まる」単位でSkillを切り出す
- 例: 「財務諸表作成」ではなく「貸借対照表作成」「損益計算書作成」に分割

### 1.2 業界標準準拠
- 対象ドメインの業界標準フレームワークを調査する
- フレームワークの各プロセス/フェーズをSkillにマッピングする
- 業界用語、標準的なワークフローを反映する

### 1.3 自己完結
- 各Skillは必要なassets/evaluation/questionsを同梱する
- 他Skillのassets参照（横参照）は禁止
- パス情報はCLAUDE.mdに集約（Skillに書かない）

## 2. Skills分解アプローチ

### 2.1 機能ベース分解
1. 必須機能一覧を取得（draft_requirements.mdから）
2. 各機能を「主成果物」で分類
3. 1成果物 = 1 Skillとして分解

### 2.2 フレームワークベース分解
1. 業界標準フレームワークを特定
2. フレームワークのフェーズ/プロセスを列挙
3. 各プロセスをSkillにマッピング

### 2.3 ハイブリッド分解
1. 機能ベースで初期分解
2. フレームワークで抜け漏れチェック
3. 不足があれば追加

## 3. ドメイン別フレームワーク例

| ドメイン | 標準フレームワーク | 主要プロセス |
|----------|-------------------|--------------|
| 会計 | GAAP/IFRS | 仕訳、決算、財務諸表、税務 |
| マーケティング | AMA Marketing BOK | 市場分析、戦略立案、キャンペーン、効果測定 |
| プロジェクト管理 | PMBOK | 立上げ、計画、実行、監視、終結 |
| ビジネス分析 | BABOK | 要求抽出、分析、検証、変更管理 |
| 法務 | - | 契約審査、コンプライアンス、訴訟対応 |
| HR | SHRM | 採用、育成、評価、報酬、労務 |
| 製造 | ISO 9001 | 設計、調達、生産、検査、出荷 |
| IT開発 | Agile/Scrum | 要件定義、設計、実装、テスト、デプロイ |
| 医療 | HL7/FHIR | 診察、診断、治療計画、経過観察 |
| 教育 | ADDIE | 分析、設計、開発、実施、評価 |

## 4. Skill命名規則

```
{domain}-{action}-{object}
```

例:
- `accounting-create-journal-entry` - 仕訳作成
- `marketing-analyze-market` - 市場分析
- `pmbok-plan-schedule` - スケジュール計画
- `hr-evaluate-performance` - 人事評価

## 5. Skills間の依存関係

### 5.1 Phase構成
Skills群をPhaseでグループ化し、実行順序を明確化する。

```
Phase 1: 準備
  skill-a → skill-b

Phase 2: 実行
  skill-c / skill-d（並列可）
  skill-e → skill-f

Phase 3: 完了
  skill-g
```

### 5.2 Next Actionチェーン
各SkillのNext Actionで次のSkillを指定し、ワークフローをチェーンする。

## 6. 生成チェックリスト

- [ ] 全必須機能がSkillとしてカバーされている
- [ ] 各Skillが1WF=1主成果物になっている
- [ ] 業界標準フレームワークが反映されている
- [ ] Skills間の依存関係が明確
- [ ] 全SkillがSKILL.md統一フォーマットに準拠
- [ ] 全Skillにassets/evaluationが同梱されている
- [ ] Next Actionが適切にチェーンしている
