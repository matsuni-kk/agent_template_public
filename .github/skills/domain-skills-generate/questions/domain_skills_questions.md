# Domain Skills Generate ヒアリング質問

## Phase 1: ドメイン特定

### 基本情報
| Key | 質問 | 必須 | 例 |
|-----|------|------|-----|
| domain_name | 対象ドメイン/業務領域は何ですか？ | Yes | 会計、マーケティング、法務、HR |
| domain_description | そのドメインの概要を教えてください | Yes | 企業の財務取引記録と報告 |
| target_users | 主な利用者は誰ですか？ | Yes | 経理担当者、財務マネージャー |

### 業界標準
| Key | 質問 | 必須 | 例 |
|-----|------|------|-----|
| industry_framework | 準拠すべき業界標準フレームワークはありますか？ | No | GAAP, IFRS, PMBOK, BABOK |
| regulations | 遵守すべき法規制はありますか？ | No | 会社法、金融商品取引法 |
| certifications | 関連する資格/認定はありますか？ | No | 公認会計士、PMP |

## Phase 2: 機能要件

### 必須機能
| Key | 質問 | 必須 | 例 |
|-----|------|------|-----|
| core_functions | 絶対に必要な機能は何ですか？（最大5つ） | Yes | 仕訳作成、決算処理、財務諸表作成 |
| primary_outputs | 主要な成果物は何ですか？ | Yes | 仕訳帳、貸借対照表、損益計算書 |
| workflow_phases | 業務のフェーズ/段階はありますか？ | No | 日次処理→月次処理→年次処理 |

### 追加機能
| Key | 質問 | 必須 | 例 |
|-----|------|------|-----|
| nice_to_have | あると便利な機能は？ | No | 自動仕訳提案、異常検知 |
| integrations | 連携すべきシステム/データは？ | No | 銀行データ、ERPシステム |
| automation_needs | 自動化したい作業は？ | No | 定型仕訳の自動生成 |

## Phase 3: 品質要件

### 品質基準
| Key | 質問 | 必須 | 例 |
|-----|------|------|-----|
| quality_standards | 品質基準は何ですか？ | No | 借貸一致、勘定科目正確性 |
| validation_rules | 検証すべきルールは？ | No | 金額の正の値チェック |
| review_process | レビュープロセスは？ | No | 上長承認、監査対応 |

### 成果物要件
| Key | 質問 | 必須 | 例 |
|-----|------|------|-----|
| output_formats | 成果物のフォーマットは？ | No | Markdown, PDF, Excel |
| naming_conventions | ファイル命名規則は？ | No | YYYYMMDD_仕訳帳.md |
| storage_structure | 保存先の構造は？ | No | Flow/Stock/Archived |

## Phase 4: 優先順位

### 実装優先度
| Key | 質問 | 必須 | 例 |
|-----|------|------|-----|
| phase1_skills | 最初に実装すべきSkills（3つ以内） | Yes | 仕訳作成、決算処理 |
| phase2_skills | 次に実装すべきSkills | No | 財務諸表作成、監査準備 |
| phase3_skills | 将来的に追加したいSkills | No | 予算管理、原価計算 |

### 成功基準
| Key | 質問 | 必須 | 例 |
|-----|------|------|-----|
| success_criteria | 成功をどう測定しますか？ | No | 処理時間50%削減、エラー率0% |
| kpis | 重要な指標は？ | No | 月次決算所要日数、修正仕訳件数 |

## 質問フロー

```
1. ドメイン特定（必須3問）
   ↓
2. 業界標準確認（該当あれば）
   ↓
3. 必須機能ヒアリング（必須3問）
   ↓
4. 追加機能・連携確認
   ↓
5. 品質要件確認
   ↓
6. 優先順位決定（必須1問）
```

## 回答テンプレート

```markdown
## ドメイン情報
- ドメイン名: {{domain_name}}
- 概要: {{domain_description}}
- 利用者: {{target_users}}
- 準拠フレームワーク: {{industry_framework}}

## 機能要件
### 必須機能
1. {{core_function_1}}
2. {{core_function_2}}
3. {{core_function_3}}

### 主要成果物
- {{primary_output_1}}
- {{primary_output_2}}

## 品質要件
- {{quality_standard_1}}
- {{quality_standard_2}}

## 実装優先度
### Phase 1
- {{phase1_skill_1}}
- {{phase1_skill_2}}

### Phase 2
- {{phase2_skill_1}}

## 成功基準
- {{success_criterion_1}}
```
