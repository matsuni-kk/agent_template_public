---
doc_type: daily_tasks
project_id: {{meta.project_id}}
date: {{date}}
type: daily_tasks
version: 1.0
---

<!-- NOTE: 空欄で残さないこと。必要項目を必ず記入して利用します。 -->

# 📋 {{date}} - 日次タスク

## 📅 今日の予定

{{#calendar}}
{{#events}}
- {{start_time}}-{{end_time}} {{summary}}{{#location}} at {{location}}{{/location}}
{{/events}}
{{^events}}
- 特になし
{{/events}}
{{/calendar}}

## 🔥 今日のフォーカス

- [ ] ここに今日最も重要なタスクを記入

## 📝 タスクリスト

### 🚀 高優先度
{{#tasks}}
{{#is_high}}
- [ ] {{task}} {{#due}}(期限: {{due}}){{/due}}
{{/is_high}}
{{/tasks}}

### 📊 中優先度
{{#tasks}}
{{#is_medium}}
- [ ] {{task}} {{#due}}(期限: {{due}}){{/due}}
{{/is_medium}}
{{/tasks}}

### 🔍 低優先度
{{#tasks}}
{{#is_low}}
- [ ] {{task}} {{#due}}(期限: {{due}}){{/due}}
{{/is_low}}
{{/tasks}}

## 📓 メモ・気づき

- ここにメモや気づきを必ず記載

## 💡 明日のタスク候補

- [ ] ここに明日実施したいタスクを列挙

## ⚠ 課題・懸念点

- 懸念事項や課題を書き出しておく
