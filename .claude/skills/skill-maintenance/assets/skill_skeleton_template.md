# Skill Skeleton Template

新規Skill作成時のテンプレート。`{skill-name}` を実際のSkill名に置換して使用する。

---

## フォルダ構造

```
{{AGENT_CONFIG_DIR}}/skills/{skill-name}/
├── SKILL.md
├── assets/
│   └── {name}_template.md
├── questions/
│   └── {name}_questions.md
├── evaluation/
│   └── evaluation_criteria.md
├── triggers/             # 必須: WF連携の起動条件
│   └── next_action_triggers.md
└── scripts/              # 任意
    └── {script_name}.py
```

`{{AGENT_CONFIG_DIR}}` は実行環境に応じて決定:
- Cursor: `.cursor`
- Claude Code: `.claude`
- Codex: `.codex`

---

## SKILL.md テンプレート

```markdown
---
name: {skill-name}
description: "{Skill説明}。{トリガーキーワード}を依頼されたときに使用する。"
---

# {Skill Name} Workflow

## Instructions
1. Preflight:
   - ドキュメント精査原則（Preflight必須）：テンプレート確認後、生成前に必ず以下を実施すること。
     - アジェンダ・依頼文に記載された参照資料を全て読み込む。
     - Flow/Stock配下の関連資料（前回議事録・要望リスト・プロジェクトREADME等）を網羅的に検索・確認する。
     - 確認できなかった資料は「未参照一覧」として成果物に明記する。
     - これらを完了するまで生成を開始しない。
   - 参照すべき既存資料があれば読み込み、前提・不足情報・未参照を整理する（推測しない）。
   - `./assets/{name}_template.md` を先に読み、章立て・必須項目・項目順序を確認する（テンプレートファースト）。
2. 生成:
   - `./questions/{name}_questions.md` を使って必要情報を収集し、テンプレ構造を崩さずにドキュメントを作成/更新する。
   - 元資料にない項目は省略せず「未記載」または「不明」と明記する。
3. QC（必須）:
   - `recommended_subagents` のQC Subagent（`qa-skill-qc`）に評価・チェックを委譲する。
   - Subagentは最初に `./evaluation/evaluation_criteria.md` をReadし、評価指標に基づいてQCを実施する。
   - 指摘を最小差分で反映する（テンプレの章立ては崩さない）。
   - 再度SubagentでQCする。
   - これを最大3回まで繰り返し、確定する。
   - 指摘に対し「修正した/しない」と理由を成果物に残す。
4. バックログ反映:
   - 次アクション（追加タスク、レビュー依頼等）を抽出しバックログへ反映する。
   - 反映先・編集制約・差分提示は AGENTS.md / CLAUDE.md の全体ルールに従う。

subagent_policy:
  - 品質ループ（QC/チェック/フィードバック）は必ずサブエージェントへ委譲する
  - サブエージェントの指摘を反映し、反映結果（修正有無/理由）を成果物に残す

recommended_subagents:
  - qa-skill-qc: {QC観点の説明}

## Resources
- questions: ./questions/{name}_questions.md
- assets: ./assets/{name}_template.md
- evaluation: ./evaluation/evaluation_criteria.md
- triggers: ./triggers/next_action_triggers.md
- scripts: ./scripts/

## Next Action
- triggers: ./triggers/next_action_triggers.md

起動条件に従い、条件を満たすSkillを自動実行する。
```

---

## Subagent Execution 追加セクション（該当するSkillのみ追記）

このSkillがSubagentとして独立実行される場合、SKILL.md末尾に以下を追加する：

```markdown
## Subagent Execution
このSkillはサブエージェントとして独立実行可能。
- サブエージェント: `agents/{subagent-name}.md`
- 用途: {並列画像取得、バックグラウンドダウンロード等}
- 入力: {`image_url`, `purpose`, `genre`, `title`, `filename`等}
- 出力: {保存先パス、処理結果等}
```

---

## evaluation_criteria.md テンプレート

```markdown
# {Skill Name} 評価指標

## 必須チェック項目

### 構造チェック（Pass/Fail）

| 項目 | 基準 | 重要度 |
|------|------|--------|
| テンプレート準拠 | 必須セクション（{セクション1}/{セクション2}/{セクション3}）が存在する | Critical |
| {チェック項目2} | {基準} | Critical |
| {チェック項目3} | {基準} | High |
| 未記載項目の明示 | 不明項目は「未記載」「不明」と明記されている | High |

### 内容チェック（スコアリング）

| 観点 | 評価基準 | 配点 |
|------|----------|------|
| 完全性 | {評価基準} | 30 |
| {観点2} | {評価基準} | 25 |
| {観点3} | {評価基準} | 25 |
| {観点4} | {評価基準} | 20 |

### 許容例外

- {例外条件1}
- {例外条件2}

## 採点基準

- **Pass**: 全Criticalチェック項目がPass かつ スコア80点以上
- **Conditional Pass**: 全Criticalチェック項目がPass かつ スコア60-79点
- **Fail**: CriticalチェックにFailあり または スコア60点未満

## QC報告フォーマット

\`\`\`
### QC結果: [Pass/Conditional Pass/Fail]
スコア: [XX]/100

#### 構造チェック
- [ ] テンプレート準拠: [Pass/Fail]
- [ ] {チェック項目2}: [Pass/Fail]
- [ ] {チェック項目3}: [Pass/Fail]
- [ ] 未記載項目の明示: [Pass/Fail]

#### 内容チェック
- 完全性: [XX]/30
- {観点2}: [XX]/25
- {観点3}: [XX]/25
- {観点4}: [XX]/20

#### 指摘事項
1. [指摘内容]
2. [指摘内容]

#### 推奨修正
1. [修正提案]
\`\`\`
```

---

## questions テンプレート

```markdown
# {Skill Name} Questions

## 必須入力項目

1. **目的**: このドキュメントの目的は？
2. **対象**: 対象となるプロジェクト/範囲は？
3. **期待成果**: 最終的な成果物・アウトプットは？

## 任意入力項目

4. **制約**: 制約条件・前提条件は？
5. **参照資料**: 参照すべき既存資料は？
6. **関係者**: ステークホルダー・レビューアは？
```

---

## assets テンプレート

```markdown
# {Document Name}

## 概要
- 作成日: {{today}}
- 作成者:
- ステータス: Draft

## {セクション1}

{内容}

## {セクション2}

{内容}

## {セクション3}

{内容}

## 変更履歴

| 日付 | 変更者 | 変更内容 |
|------|--------|----------|
| {{today}} | - | 初版作成 |
```

---

## triggers/next_action_triggers.md テンプレート

```markdown
# {Skill Name} Next Action Triggers

## 自動実行ルール
**以下の条件を満たす場合は、該当Skillを必ず実行すること（WF自動継続）。**
条件判定はSkill完了時に自動で行い、スキップ条件に該当しない限り次Skillへ進む。

## 起動条件テーブル

| ID | 起動条件 | 実行Skill | 優先度 | 備考 |
|----|---------|-----------|--------|------|
| T1 | {検証可能な条件を記載} | `{skill-name}` | 1 | {補足} |
| T2 | {検証可能な条件を記載} | `{skill-name}` | 2 | {補足} |

## スキップ条件
以下の場合のみ、起動条件を満たしても実行をスキップできる:
- ユーザーが明示的に「{現Skill名}のみ」と指定した場合
- {その他のスキップ条件}

## 条件判定ロジック
1. Skill完了時、起動条件テーブルを上から順に評価する
2. 条件を満たす行があれば、スキップ条件を確認する
3. スキップ条件に該当しなければ、該当Skillを実行する
4. 複数条件が該当する場合は、優先度順に全て実行する
```

### 起動条件の書き方

**検証可能な条件を書くこと（曖昧表現NG）**

| NG例 | OK例 |
|------|------|
| 「必要なら」 | 「成果物に〜セクションが存在する」 |
| 「〜したい場合」 | 「〜が未作成（ファイル不存在）」 |
| 「〜が求められる場合」 | 「〜フィールドが空欄/未記載」 |

**詳細は `./assets/next_action_triggers_spec.md` を参照。**
