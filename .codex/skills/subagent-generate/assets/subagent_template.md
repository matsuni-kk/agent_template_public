# サブエージェント定義テンプレート

以下のフォーマットでサブエージェントを定義する:

```markdown
---
name: {agent-name}
description: "{1-2文の説明}"
type: "{research|feedback|ideation|validation|parallel-check}"
tools: [Read, Grep, Glob, WebSearch, WebFetch, Bash]
---

# {Agent Display Name}

{目的と役割の詳細説明。このサブエージェントが何を達成するか。}

## 携帯Skills

このサブエージェントは以下のSkillsを参照して実行する:

| Skill | 用途 |
|-------|------|
| `.codex/skills/{skill-1}/` | {このSkillから何を参照するか} |
| `.codex/skills/{skill-2}/` | {このSkillから何を参照するか} |

### 参照すべきファイル
- `{skill-1}/assets/{file}.md`: {何のために参照}
- `{skill-1}/evaluation/{file}.md`: {評価基準として使用}

## 実行手順

### Phase 1: 準備
1. 携帯SkillsのSKILL.mdを読み込む
2. 評価基準（evaluation/*.md）を確認する
3. 対象ファイル/情報を特定する

### Phase 2: 実行
4. {メインタスクのステップ1}
5. {メインタスクのステップ2}
6. {メインタスクのステップ3}

### Phase 3: 出力
7. 結果を構造化してまとめる
8. 優先度・重要度を付与する
9. 次のアクションを明記する

## 入力

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| target_path | string | ✅ | 対象ファイル/ディレクトリのパス |
| scope | string | - | チェック範囲（file/directory/project） |
| focus_areas | array | - | 重点チェック項目 |

## 出力

### 出力フォーマット
```json
{
  "status": "success|warning|error",
  "summary": "1-2文の要約",
  "findings": [
    {
      "severity": "critical|high|medium|low",
      "category": "{カテゴリ}",
      "location": "{ファイル:行番号}",
      "issue": "{問題の説明}",
      "suggestion": "{改善提案}"
    }
  ],
  "next_actions": [
    "{推奨アクション1}",
    "{推奨アクション2}"
  ]
}
```

### 出力例
```json
{
  "status": "warning",
  "summary": "3件の改善提案があります",
  "findings": [
    {
      "severity": "medium",
      "category": "error-handling",
      "location": "functions/my_func.ts:25",
      "issue": "try-catchブロックがありません",
      "suggestion": "外部API呼び出しをtry-catchで囲んでください"
    }
  ],
  "next_actions": [
    "error-handling Skillを参照してエラーハンドリングを追加"
  ]
}
```

## 判定基準

### 成功条件
- [ ] 全ての対象ファイルをチェック完了
- [ ] 各findingに severity, category, suggestion が含まれる
- [ ] next_actions が具体的で実行可能

### 失敗条件
- 対象ファイルが見つからない
- 携帯Skillsが読み込めない
- 評価基準が不明確
```

---

## タイプ別カスタマイズ

### research-agent用
```markdown
## Web検索クエリ

以下のクエリで情報を収集する:
- "{検索クエリ1}"
- "{検索クエリ2}"

## 情報ソース優先度
1. 公式ドキュメント
2. GitHub公式リポジトリ
3. 技術ブログ（信頼性の高いもの）
```

### feedback-agent用
```markdown
## レビュー観点

| 観点 | 重み | チェック内容 |
|------|------|-------------|
| 正確性 | 高 | 仕様通りの実装か |
| 保守性 | 中 | コードの読みやすさ |
| セキュリティ | 高 | 脆弱性の有無 |
```

### ideation-agent用
```markdown
## アイデア生成ルール

- 最低3つの異なるアプローチを提案
- 各アプローチのPros/Consを明記
- 推奨案を1つ選定し理由を説明
```
