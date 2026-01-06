# ワークフロー索引メンテナンスガイド

## 概要

CLAUDE.md Section 6 のワークフロー索引は、PMBOKフェーズごとのSkill連携を定義する。各SkillのNext Action triggersと整合させる。

---

## 現在の索引構造

```yaml
### Initiating（立ち上げ）
project-charter → stakeholder-analysis

### Discovery / Research（調査・発見）
desk-research / customer-research / competitor-research
current-state → gap-analysis → idea-divergence → hypothesis-validation

### Planning（計画）
requirement-specification → wbs → schedule
resource-plan / quality-plan / backlog-yaml

### Executing（実行）
agenda → meeting-minutes → backlog-yaml
task-management / work-execution
presentation-planning → presentation-deck
training-outline → presentation-deck

### Decision（意思決定）
hypothesis-validation → decision-matrix

### Monitoring（監視・コントロール）
status-report / risk-monitoring / change-control / worklog-report

### Closing（終結）
lessons-learned / transition-document / project-closure / quality-assurance

### Annals（年表）
annals

### Recruiting（採用）
recruiting-interview

### 横断プロセス
external-data-import / flow-to-stock / document-delivery / skill-maintenance / subagent-maintenance / project-document-search / red-team-feedback-loop
```

---

## 記号の意味

| 記号 | 意味 | 例 |
|------|------|-----|
| → | 完了後に次へ進む（シーケンシャル） | `wbs → schedule` |
| / | 並列または選択（どちらでも可） | `resource-plan / quality-plan` |

---

## 追加手順

### 1. 新規Skillの追加

```yaml
# 1. 該当フェーズを特定
### Planning（計画）

# 2. 連携先を決定
requirement-specification → wbs → schedule → new-skill

# 3. または並列として追加
resource-plan / quality-plan / new-skill
```

### 2. 連携関係の変更

```yaml
# Before
project-charter → stakeholder-analysis

# After（中間Skillを追加）
project-charter → new-analysis → stakeholder-analysis
```

---

## Next Action triggersとの整合

WF索引を変更したら、関連SkillのNext Action triggersも更新する。

**例: wbs → schedule**

`pmbok-wbs/triggers/next_action_triggers.md`:
```markdown
| ID | 起動条件 | 実行Skill | 優先度 |
|----|---------|-----------|--------|
| T1 | WBSにタスクが1件以上存在する | `pmbok-schedule` | 1 |
```

---

## フェーズの選択基準

| フェーズ | 対象Skill |
|----------|-----------|
| Initiating | プロジェクト立ち上げ時のみ実行 |
| Discovery/Research | 調査・分析系 |
| Planning | 計画策定系 |
| Executing | 実行・作成系 |
| Decision | 意思決定支援系 |
| Monitoring | 進捗監視・報告系 |
| Closing | プロジェクト終結系 |
| 横断プロセス | フェーズを跨いで使用 |

---

## チェックリスト

追加・変更時は以下を確認:

- [ ] 参照先Skillが存在する（skill名のtypoなし）
- [ ] 該当フェーズが適切
- [ ] 連携方向が正しい（→ or /）
- [ ] 関連SkillのNext Action triggersを更新した
- [ ] 循環参照がない（A → B → A はNG）

---

## よくあるパターン

### 線形フロー

```yaml
# 順番に実行
A → B → C → D
```

### 分岐フロー

```yaml
# Aの後、BまたはCを選択
A → B / C
```

### 合流フロー

```yaml
# B, Cの後、Dへ合流
B → D
C → D
```

### 並列フロー

```yaml
# 独立して実行可能
A / B / C
```
