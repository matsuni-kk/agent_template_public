# Subagent Template

## 公式仕様（Claude Code Plugins Reference準拠）

### ファイル配置
- 配置先: `{{AGENT_CONFIG_DIR}}/agents/{agent-name}.md`
- ファイル形式: Markdown + YAML frontmatter
- `{{AGENT_CONFIG_DIR}}` は実行環境に応じて決定:
  - Cursor: `.cursor`
  - Claude Code: `.claude`
  - Codex: `.codex`

### 必須フロントマター

```yaml
---
name: agent-name
description: "エージェントの専門領域と自動委譲のトリガー説明"
skills: skill1, skill2, skill3
---
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `name` | string | Yes | エージェントの一意識別子（ケバブケース推奨） |
| `description` | string | Yes | 専門領域の説明。自動委譲のマッチングに使用される |
| `skills` | string | No | ロードするSkill名のカンマ区切りリスト（省略時はSkillなし）。このSubagentが実行すべきSkillを指定する |

### 推奨構造

```markdown
---
name: {{agent_name}}
description: "{{agent_description}}"
skills: {{skill1}}, {{skill2}}, {{skill3}}
---

# {{Agent Title}}

{{agent_overview}}

## Expertise Overview
あなたは{{domain}}の専門家です。以下の領域に精通しています：
- {{expertise_1}}
- {{expertise_2}}
- {{expertise_3}}

## Critical First Step
タスク実行前に必ず以下を行ってください：
1. {{first_step_1}}
2. {{first_step_2}}

## Domain Coverage
対応可能なタスク：
- {{task_1}}
- {{task_2}}
- {{task_3}}

## Project Context
このプロジェクト固有のパターンと規約：
- {{context_1}}
- {{context_2}}

## Response Format
出力形式：
- {{format_requirement_1}}
- {{format_requirement_2}}

## Quality Assurance
検証ステップ：
1. {{qa_step_1}}
2. {{qa_step_2}}
```

### Subagent化の判断基準

**Subagentに向いているタスク:**
- 繰り返し利用される（QCチェック、レビュー、フィードバック）
- 並列実行が有効（複数観点からの評価、アイデア出し）
- 独立コンテキストが必要（批評、第三者視点の評価）

**典型的なSubagent用途:**
- 品質チェック（QC）・レビュー
- フィードバック・批評
- アイデア出し・ブレインストーミング
- リサーチ・情報収集

**skillsフィールドの使い方:**
- Subagentが実行すべきSkillを `skills:` に指定する
- 指定されたSkillはSubagent起動時にロードされ、そのSkillのInstructionsに従って実行される
- Skill側には `## Subagent Execution` セクションを追加し、サブエージェントパス・用途・入出力を明記する

**Subagentにすべきでないタスク:**
- 簡単な1ステップ処理 → メイン会話で実行
- 前後の文脈が強く結びついている → Skill
- ガイドライン・スタイル指定のみ → CLAUDE.md / Skill

### 動作メカニズム

1. **自動委譲**: Claudeは`description`とタスク内容をマッチングし、適切なSubagentに自動委譲
2. **コンテキスト分離**: Subagentは独立したコンテキストウィンドウで実行
3. **結果要約**: 結果はサマリーとしてメインセッションに返却
4. **非同期実行可能**: バックグラウンド実行（Ctrl+B）対応

### ベストプラクティス

- `description`は具体的なユースケースを含める（自動マッチング精度向上）
- `skills`は必要なSkillのみ指定（不要なら省略可）
- 5,000語以内に収める（コンテキストウィンドウ考慮）
- 単一責任原則を守る（1エージェント1専門領域）

### 例: QAレビューエージェント

```markdown
---
name: qa-reviewer
description: "コードレビューと品質保証を担当。プルリクエストレビュー、コード品質チェック、セキュリティ監査を依頼されたときに使用する。"
skills: code-review, security-check
---

# QA Reviewer Agent

あなたはコード品質とセキュリティの専門家です。

## Expertise Overview
- コードレビューベストプラクティス
- セキュリティ脆弱性検出
- テストカバレッジ分析
- パフォーマンス最適化提案

## Critical First Step
レビュー前に必ず以下を実行：
1. プロジェクトのコーディング規約を確認
2. 既存のテストスイートを把握

## Domain Coverage
- プルリクエストレビュー
- セキュリティ監査
- コード品質メトリクス評価
- リファクタリング提案

## Response Format
- 重要度別に分類（Critical/High/Medium/Low）
- 具体的な修正案を提示
- 該当コード行を引用

## Quality Assurance
1. 全指摘事項に根拠を明記
2. 誤検知リスクを明示
```
