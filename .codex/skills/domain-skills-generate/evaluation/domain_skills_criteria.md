# Domain Skills Generate 評価指標

## 必須チェック項目

### 構造チェック（Pass/Fail）
| 項目 | 基準 | 重要度 |
|------|------|--------|
| SKILL.md存在 | 全Skillに SKILL.md が作成されている | Critical |
| フォーマット準拠 | frontmatter (name, description) が正しい | Critical |
| Instructions完備 | Preflight/生成/QC/バックログ反映 の4セクション | Critical |
| assets/存在 | 各Skillに assets/ フォルダがある | Critical |
| 1WF=1成果物 | 各Skillが単一の主成果物を持つ | High |
| 業界標準準拠 | 該当フレームワークのプロセスを反映 | High |

### 内容チェック（スコアリング）
| 観点 | 評価基準 | 配点 |
|------|----------|------|
| 網羅性 | 要件の全機能がSkillとしてカバー | 25 |
| 専門性 | ドメイン固有の用語・プロセスを反映 | 25 |
| 実用性 | テンプレート・質問が実務で即使用可能 | 25 |
| 整合性 | Skills間の依存関係・Phaseが明確 | 15 |
| 品質基準 | evaluation/に適切な評価指標 | 10 |

### 許容例外
- 初回生成で全assetsが完備されていないことは想定内（後続で補完）
- ドメインによっては evaluation/ が不要なSkillも許容

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

## 詳細評価基準

### 網羅性（25点）
| スコア | 基準 |
|--------|------|
| 25 | 要件の全機能（100%）がSkillとしてカバー |
| 20 | 90%以上の機能がカバー |
| 15 | 80%以上の機能がカバー |
| 10 | 70%以上の機能がカバー |
| 0 | 70%未満 |

### 専門性（25点）
| スコア | 基準 |
|--------|------|
| 25 | 業界標準フレームワーク完全準拠、専門用語正確 |
| 20 | フレームワーク準拠、用語ほぼ正確 |
| 15 | フレームワーク部分準拠、用語に一部誤り |
| 10 | フレームワーク参照あり、用語不正確 |
| 0 | フレームワーク未参照 |

### 実用性（25点）
| スコア | 基準 |
|--------|------|
| 25 | テンプレート・質問が即実務利用可能、詳細十分 |
| 20 | 軽微な調整で実務利用可能 |
| 15 | 追加作業で実務利用可能 |
| 10 | 骨格のみ、大幅な追加必要 |
| 0 | 実務利用不可 |

### 整合性（15点）
| スコア | 基準 |
|--------|------|
| 15 | Phase構成明確、Next Action適切にチェーン |
| 10 | Phase構成あり、一部Next Action不明確 |
| 5 | 依存関係の記載不十分 |
| 0 | 整合性なし |

### 品質基準（10点）
| スコア | 基準 |
|--------|------|
| 10 | 全QC対象Skillに適切な evaluation/ |
| 7 | 主要Skillに evaluation/ あり |
| 3 | 一部Skillのみ evaluation/ |
| 0 | evaluation/ なし |

## チェックリスト

### SKILL.md 必須要素
- [ ] frontmatter に name, description
- [ ] description にトリガーワード3つ以上
- [ ] `# XXX Workflow` タイトル
- [ ] `## Instructions` セクション
- [ ] Preflight / 生成 / QC / バックログ反映
- [ ] `subagent_policy` ブロック
- [ ] `recommended_subagents` ブロック
- [ ] `## Resources` セクション
- [ ] `## Next Action` セクション

### assets/ 必須要素
- [ ] メインチェックリスト（*_checklist.md）
- [ ] メインテンプレート（*_template.md）
- [ ] ドメイン固有の参照資料

### evaluation/ 必須要素（QC対象Skill）
- [ ] 構造チェック（Pass/Fail）テーブル
- [ ] 内容チェック（スコアリング）テーブル
- [ ] 採点基準（Pass/Conditional Pass/Fail）
- [ ] QC報告フォーマット
