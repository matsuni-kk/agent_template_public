# Subagent Check Report Template

## チェック実施情報
- 実施日時: {{meta.timestamp}}
- 対象エージェント: {{agent_name}}
- チェック担当: {{meta.user}}

## フロントマター検証

### 必須フィールド
| フィールド | 存在 | 値 | 判定 |
|-----------|------|-----|------|
| name | {{has_name}} | {{name_value}} | {{name_pass}} |
| description | {{has_description}} | {{description_value}} | {{description_pass}} |
| capabilities | {{has_capabilities}} | {{capabilities_value}} | {{capabilities_pass}} |

### オプションフィールド
| フィールド | 存在 | 値 |
|-----------|------|-----|
| model | {{has_model}} | {{model_value}} |

## 構造検証

### 推奨セクション
| セクション | 存在 | 備考 |
|-----------|------|------|
| Expertise Overview | {{has_expertise}} | |
| Critical First Step | {{has_first_step}} | |
| Domain Coverage | {{has_domain}} | |
| Response Format | {{has_format}} | |
| Quality Assurance | {{has_qa}} | |

## 品質指標

- 文字数: {{word_count}} / 5000（推奨上限）
- capabilities数: {{cap_count}} / 7（推奨上限）
- 単一責任原則: {{single_responsibility}}

## 総合判定
- 結果: {{overall_result}}
- コメント: {{overall_comment}}

## 指摘事項
{{issues}}

## 推奨修正
{{recommendations}}
