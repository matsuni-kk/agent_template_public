# ディレクトリパターン選択ガイド

用途に応じて最適なディレクトリ構造を選択する。

## パターン一覧

### 1. Business（ビジネス/ドキュメント管理）
PMBOKやBABOK等のビジネスフレームワーク向け。

```
{domain}_agent/
├── .claude/
│   ├── skills/
│   ├── agents/
│   └── commands/
├── Flow/                    # 作業中ドラフト（日次管理）
│   └── YYYYMM/YYYY-MM-DD/
├── Stock/                   # 確定版ドキュメント
│   └── programs/{project}/
│       ├── documents/
│       └── images/
├── Archived/                # 履歴保管
├── scripts/
├── CLAUDE.md
└── README.md
```

**適用例**: 会計、マーケティング、HR、法務、プロジェクト管理

---

### 2. Coding（ソフトウェア開発）
ソースコード管理向け。標準的なプロジェクト構造。

```
{domain}_agent/
├── .claude/
│   ├── skills/
│   ├── agents/
│   └── commands/
├── src/                     # ソースコード
│   ├── components/
│   ├── utils/
│   └── types/
├── tests/                   # テストコード
│   ├── unit/
│   └── integration/
├── docs/                    # ドキュメント
├── scripts/                 # ビルド/ユーティリティ
├── CLAUDE.md
└── README.md
```

**適用例**: Webアプリ、CLI、ライブラリ、API

---

### 3. Data（データ分析/ML）
データサイエンス・機械学習向け。

```
{domain}_agent/
├── .claude/
│   ├── skills/
│   ├── agents/
│   └── commands/
├── data/                    # データセット
│   ├── raw/
│   ├── processed/
│   └── external/
├── notebooks/               # Jupyter Notebooks
├── src/                     # ソースコード
│   ├── data/
│   ├── features/
│   ├── models/
│   └── visualization/
├── models/                  # 学習済みモデル
├── reports/                 # レポート・図表
├── scripts/
├── CLAUDE.md
└── README.md
```

**適用例**: データ分析、ML/AI、レポート自動生成

---

### 4. DevOps（インフラ/運用）
インフラ管理・自動化向け。

```
{domain}_agent/
├── .claude/
│   ├── skills/
│   ├── agents/
│   └── commands/
├── infra/                   # インフラ定義
│   ├── terraform/
│   ├── kubernetes/
│   └── docker/
├── scripts/                 # 自動化スクリプト
│   ├── deploy/
│   ├── backup/
│   └── monitoring/
├── configs/                 # 設定ファイル
├── docs/                    # 運用ドキュメント
├── CLAUDE.md
└── README.md
```

**適用例**: CI/CD、クラウドインフラ、監視、自動化

---

### 5. MultiApp（ミニアプリ量産型）
小さなアプリ・フロー・ボットを複数管理するパターン。
Power Platform、Copilot Studio、n8n、Zapier的な思想。

```
{domain}_agent/
├── .claude/
│   ├── skills/
│   ├── agents/
│   └── commands/
├── apps/                    # 個別アプリ群
│   ├── {app_name_1}/
│   │   ├── src/
│   │   ├── config.json
│   │   └── README.md
│   ├── {app_name_2}/
│   └── {app_name_3}/
├── flows/                   # 自動化フロー群
│   ├── {flow_name_1}.json
│   └── {flow_name_2}.json
├── shared/                  # 共通コンポーネント
│   ├── components/
│   ├── connectors/
│   └── templates/
├── Flow/                    # 作業中（設計・検討）
│   └── YYYYMM/YYYY-MM-DD/
├── Stock/                   # 確定版ドキュメント
│   ├── specs/
│   └── catalog/             # アプリカタログ
├── Archived/
├── scripts/
├── CLAUDE.md
└── README.md
```

**適用例**: Power Apps/Automate、Copilot Studio、n8n、ローコード開発、ボット量産

---

### 6. Minimal（最小構成）
シンプルなプロジェクト向け。

```
{domain}_agent/
├── .claude/
│   ├── skills/
│   ├── agents/
│   └── commands/
├── src/                     # メインコード/コンテンツ
├── scripts/
├── CLAUDE.md
└── README.md
```

**適用例**: 小規模プロジェクト、PoC、スクリプト集

---

## 共通要素（全パターン必須）

| 要素 | 説明 |
|------|------|
| `.cursor/skills/` | Skills群 |
| `.claude/agents/` | サブエージェント |
| `.claude/commands/` | スラッシュコマンド |
| `scripts/` | validate_skills.py, update_agent_master.py |
| `CLAUDE.md` | マスター指示 |
| `README.md` | リポジトリ説明 |

## 引き継ぎSkills（全パターン共通）

以下のSkillsは全エージェントにコピー:

- `skill-maintenance/` - Skill保守
- `subagent-maintenance/` - サブエージェント保守

## 選択フロー

```
1. 用途を確認
   ├── ビジネス/ドキュメント管理 → Business
   ├── ソフトウェア開発（単一プロジェクト） → Coding
   ├── データ分析/ML → Data
   ├── インフラ/運用 → DevOps
   ├── ミニアプリ・フロー量産 → MultiApp
   └── その他/シンプル → Minimal

2. skeleton-generate 実行時にパターン指定

3. 必要に応じてカスタマイズ
```
