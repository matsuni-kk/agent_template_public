# Subagent Maintenance 評価指標

## 必須チェック項目

### 構造チェック（Pass/Fail）

| 項目 | 基準 | 重要度 |
|------|------|--------|
| フロントマター準拠 | 必須フィールド（name/description）が存在する | Critical |
| name形式 | ケバブケース形式である | Critical |
| skills整合性 | skillsフィールドで指定されたSkillが実在する（省略可） | High |
| 推奨セクション | Expertise Overview/Domain Coverage が存在する | High |
| 文字数制限 | 5,000語以内である | Medium |

### 内容チェック（スコアリング）

| 観点 | 評価基準 | 配点 |
|------|----------|------|
| description品質 | 自動委譲のトリガーとして具体的なユースケースを含む | 30 |
| skills連携 | skillsフィールドとSkill側のSubagent Executionセクションが整合している | 25 |
| 単一責任原則 | 1エージェント1専門領域を守っている | 25 |
| 追跡可能性 | 変更理由・変更ログが明記されている | 20 |

### 許容例外

- 新規作成時は「既存機能維持」チェック対象外
- model指定は省略可（親から継承）

## 採点基準

- **Pass**: 全Criticalチェック項目がPass かつ スコア80点以上
- **Conditional Pass**: 全Criticalチェック項目がPass かつ スコア60-79点
- **Fail**: CriticalチェックにFailあり または スコア60点未満

## QC報告フォーマット

```
### QC結果: [Pass/Conditional Pass/Fail]
スコア: [XX]/100

#### 構造チェック
- [ ] フロントマター準拠: [Pass/Fail]
- [ ] name形式: [Pass/Fail]
- [ ] skills整合性: [Pass/Fail]
- [ ] 推奨セクション: [Pass/Fail]
- [ ] 文字数制限: [Pass/Fail]

#### 内容チェック
- description品質: [XX]/30
- skills連携: [XX]/25
- 単一責任原則: [XX]/25
- 追跡可能性: [XX]/20

#### フロントマター検証
- name: [値] - [OK/NG]
- description: [要約] - [OK/NG]
- skills: [Skill名] - [OK/NG]

#### 指摘事項
1. [指摘内容]
2. [指摘内容]

#### 推奨修正
1. [修正提案]
```
