---
name: agent-discovery
description: "新規エージェント作成のためのヒアリング・要件定義を実施し、draft_requirements.mdとframework_research.mdを生成する。「エージェント作成」「新規Agent」「ヒアリング開始」を依頼されたときに使用する。"
---

# Agent Discovery Workflow

新規ドメイン特化エージェント作成のためのDiscoveryフェーズ。主成果物はdraft_requirements.mdとframework_research.md。

## Instructions

### 1. Preflight（事前確認）
- `./assets/discovery_checklist.md` を先に読み、必須項目を確認する。
- 対象ドメインの業界標準フレームワーク（BABOK、AMA等）をWeb検索で調査する。
- 既存資料があれば収集し、参照元リンクと取得日時を記録する。
- 確認できなかった資料は「未参照一覧」として明記する。

### 2. 生成
- `./questions/discovery_questions.md` に従い以下を収集する:
  - ドメイン名（スネークケース）、エージェント表示名
  - 解決したい課題・ペインポイント
  - 対象ユーザー（ペルソナ）
  - 期待成果・KPI・成功条件
  - 必須機能（3-5個）、推奨機能、将来機能
  - 利用シナリオ、成果物フォーマット
  - データソース・外部システム連携
- `./assets/requirements_template.md` に従いdraft_requirements.mdを生成する。
- `./assets/framework_research_template.md` に従いframework_research.mdを生成する。
- 不確定事項はTODO形式で列挙し、合意時刻を明記する。
- 元資料にない項目は省略せず「未記載」と明記する。

### 3. 構造承認
- Flow / Stock / Archived の初期構成を説明する。
- エージェント要件とフォルダ設計についてユーザー承認を得る。
- **承認が得られない場合は後続工程へ進まない。**

### 4. QC（必須）
- `recommended_subagents` のQC Subagent（`qa-skill-qc`）に評価を委譲する。
- Subagentは `./evaluation/discovery_criteria.md` をReadし、QCを実施する。
- 指摘を最小差分で反映する（最大3回）。
- 指摘に対し「修正した/しない」と理由を成果物に残す。

### 5. バックログ反映
- タスクリスト（{{flow_day_dir}}/{{today}}_agent_creation_tasklist.md）を生成する。
- 未決事項、次アクションをタスクリストへ追記する。
- framework_research_done=true を記録してから次工程へ進む。

subagent_policy:
  - 品質ループ（QC/チェック/フィードバック）は必ずサブエージェントへ委譲する
  - サブエージェントの指摘を反映し、反映結果（修正有無/理由）を成果物に残す

recommended_subagents:
  - qa-skill-qc: 必須項目網羅、曖昧表現、推測混入、業界標準整合、承認確認を検査

## Resources
- questions: ./questions/discovery_questions.md
- assets: ./assets/discovery_checklist.md
- assets: ./assets/requirements_template.md
- assets: ./assets/framework_research_template.md
- assets: ./assets/tasklist_template.md
- evaluation: ./evaluation/discovery_criteria.md
- triggers: ./triggers/next_action_triggers.md

## Next Action
- triggers: ./triggers/next_action_triggers.md

起動条件に従い、条件を満たすSkillを自動実行する。
