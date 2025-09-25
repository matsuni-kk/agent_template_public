---
doc_type: weekly_review
project_id: {{meta.project_id}}
iso_week: {{iso_week}}
version: 1.0
---

# Week {{iso_week}} Review

<!-- NOTE: このテンプレートの各項目は必ず記入し、空欄のままにしないでください。 -->

## ✔ 今週完了
{{#week_data.completed}}
- {{id}} {{title}}
{{/week_data.completed}}

## ⚠ 未完了／持越し
{{#week_data.remaining}}
- {{id}} {{title}} (Due: {{due}})
{{/week_data.remaining}}

## 📈 進捗率
- 完了 {{week_data.done_points}} / 合計 {{week_data.total_points}} pt ({{week_data.progress}}%)

## 🚀 次週フォーカス案
{{#week_data.next}}
- {{.}}
{{/week_data.next}}

## 🌟 学びと次のアクション

- 今週得られた学びや翌週に向けたアクションをここに記入
