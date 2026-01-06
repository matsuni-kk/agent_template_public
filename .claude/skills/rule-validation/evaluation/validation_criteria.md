# Skills Validation 評価指標

## 必須チェック項目

### 構造チェック（Pass/Fail）
| 項目 | 基準 | 重要度 |
|------|------|--------|
| スクリプト実行 | validate_skills.py が実行された | Critical |
| 全Skill検証 | 全SKILL.mdが検証対象に含まれる | Critical |
| エラー解消 | `All skills passed validation.` が出力 | Critical |
| ログ記録 | skills_check_log.md が作成されている | High |

### 内容チェック（スコアリング）
| 観点 | 評価基準 | 配点 |
|------|----------|------|
| 完全性 | 全Skillが検証済み | 30 |
| エラー対応 | エラーがあれば修正済み | 30 |
| ログ品質 | 検証日時・対象・結果が記載 | 20 |
| タスク反映 | validation_passed が記録 | 20 |

### 許容例外
- 初回検証でエラーがあることは想定内（修正すれば可）

## 採点基準
- **Pass**: 全CriticalがPass かつ スコア80点以上
- **Conditional Pass**: 全CriticalがPass かつ スコア60-79点
- **Fail**: CriticalにFailあり または スコア60点未満

## QC報告フォーマット
```
### QC結果: [Pass/Conditional Pass/Fail]
スコア: [XX]/100

#### 指摘事項
1. [項目名]: [指摘内容] (重要度: Critical/High/Medium/Low)

#### 修正推奨
- [具体的な修正アクション]
```
