# Skill スケルトンテンプレート

## SKILL.md テンプレート

```markdown
---
name: {domain}-{action}-{object}
description: "{処理内容の説明}。「{トリガーワード1}」「{トリガーワード2}」「{トリガーワード3}」を依頼されたときに使用する。"
---

# {Skill名} Workflow

{Skill概要}。主成果物は{成果物名}（{成果物説明}）。

## Instructions

### 1. Preflight（事前確認）
- `./assets/{checklist_file}.md` を先に読み、作業項目を確認する。
- 前回の成果物（{previous_output}）があれば参照する。
- 必要な入力情報が揃っているか確認する。
- 不足情報があればユーザーに質問する。

### 2. 生成
- 以下の手順で成果物を作成する:
  1. {step_1}
  2. {step_2}
  3. {step_3}
- テンプレート `./assets/{template_file}.md` を適用する。
- 元資料にない項目は省略せず「未記載」と明記する。

### 3. QC（必須）
- `recommended_subagents` のQC Subagent（`qa-skill-qc`）に評価を委譲する。
- Subagentは `./evaluation/{criteria_file}.md` をReadし、QCを実施する。
- 指摘を最小差分で反映する（最大3回）。
- 指摘に対し「修正した/しない」と理由を成果物に残す。

### 4. バックログ反映
- 成果物をタスクリストに記録する。
- 残課題があればバックログへ追記する。
- {completion_flag}=true を記録してから次工程へ進む。

subagent_policy:
  - 品質ループ（QC/チェック/フィードバック）は必ずサブエージェントへ委譲する
  - サブエージェントの指摘を反映し、反映結果（修正有無/理由）を成果物に残す

recommended_subagents:
  - qa-skill-qc: {QC観点の説明}

## Resources
- assets: ./assets/{checklist_file}.md
- assets: ./assets/{template_file}.md
- evaluation: ./evaluation/{criteria_file}.md
- questions: ./questions/{questions_file}.md
- triggers: ./triggers/next_action_triggers.md

## Next Action
- triggers: ./triggers/next_action_triggers.md

起動条件に従い、条件を満たすSkillを自動実行する。
```

## フォルダ構造テンプレート

```
{skill-name}/
├── SKILL.md                    # Skill定義（必須）
├── assets/                     # 関連資材（必須）
│   ├── {main_checklist}.md     # 作業チェックリスト
│   ├── {main_template}.md      # 成果物テンプレート
│   └── {additional_assets}.md  # 追加資材（任意）
├── evaluation/                 # 評価基準（QC用）
│   └── {criteria}.md           # 評価指標・採点基準
├── questions/                  # 質問項目（任意）
│   └── {questions}.md          # ヒアリング質問
└── triggers/                   # Next Action 起動条件（必須）
    └── next_action_triggers.md
```

## 命名規則

### Skill名
```
{domain}-{action}-{object}
```

例:
- `accounting-create-journal` - 仕訳作成
- `marketing-analyze-market` - 市場分析
- `legal-review-contract` - 契約レビュー
- `hr-evaluate-performance` - 人事評価
- `pmbok-plan-schedule` - スケジュール計画

### ファイル命名
| ファイル種別 | 命名パターン | 例 |
|-------------|-------------|-----|
| チェックリスト | {action}_{object}_checklist.md | create_journal_checklist.md |
| テンプレート | {object}_template.md | journal_template.md |
| 評価基準 | {skill}_criteria.md | journal_criteria.md |
| 質問 | {skill}_questions.md | journal_questions.md |

## プレースホルダ一覧

| プレースホルダ | 説明 | 例 |
|---------------|------|-----|
| {domain} | ドメイン名 | accounting, marketing |
| {action} | アクション動詞 | create, analyze, review |
| {object} | 対象オブジェクト | journal, market, contract |
| {skill_name} | Skill名（ハイフン区切り） | create-journal |
| {Skill名} | Skill表示名（日本語可） | 仕訳作成 |
| {成果物名} | 主成果物ファイル名 | journal_entry.md |
| {トリガーワード} | 発動キーワード | 仕訳, 仕訳作成, journal |
