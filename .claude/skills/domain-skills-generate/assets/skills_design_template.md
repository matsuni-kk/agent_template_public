# Skills設計書テンプレート

## {Domain}エージェント Skills設計書

### 基本情報
| 項目 | 内容 |
|------|------|
| ドメイン名 | {domain_name} |
| エージェント名 | {agent_name} |
| 準拠フレームワーク | {industry_framework} |
| 作成日 | {{meta.timestamp}} |
| 作成者 | {author} |

### ドメイン概要
{domain_description}

### 利用者
- {target_user_1}
- {target_user_2}
- {target_user_3}

---

## Skills一覧

### Phase 1: 基盤機能（必須）

| # | Skill名 | 説明 | 主成果物 | 優先度 |
|---|---------|------|----------|--------|
| 01 | {domain}-{action1}-{object1} | {description_1} | {output_1} | Critical |
| 02 | {domain}-{action2}-{object2} | {description_2} | {output_2} | Critical |
| 03 | {domain}-{action3}-{object3} | {description_3} | {output_3} | High |

### Phase 2: 中核機能

| # | Skill名 | 説明 | 主成果物 | 優先度 |
|---|---------|------|----------|--------|
| 04 | {domain}-{action4}-{object4} | {description_4} | {output_4} | High |
| 05 | {domain}-{action5}-{object5} | {description_5} | {output_5} | High |
| 06 | {domain}-{action6}-{object6} | {description_6} | {output_6} | Medium |

### Phase 3: 拡張機能

| # | Skill名 | 説明 | 主成果物 | 優先度 |
|---|---------|------|----------|--------|
| 07 | {domain}-{action7}-{object7} | {description_7} | {output_7} | Medium |
| 08 | {domain}-{action8}-{object8} | {description_8} | {output_8} | Low |

---

## Skills詳細設計

### 01. {domain}-{action1}-{object1}

**概要**: {skill_overview}

**トリガーワード**:
- {trigger_1}
- {trigger_2}
- {trigger_3}

**入力**:
- {input_1}
- {input_2}

**処理ステップ**:
1. {step_1}
2. {step_2}
3. {step_3}

**主成果物**: {primary_output}

**品質基準**:
- {quality_criterion_1}
- {quality_criterion_2}

**前提Skill**: なし / {prerequisite_skill}

**後続Skill**: {next_skill}

---

### 02. {domain}-{action2}-{object2}

**概要**: {skill_overview}

**トリガーワード**:
- {trigger_1}
- {trigger_2}
- {trigger_3}

**入力**:
- {input_1}
- {input_2}

**処理ステップ**:
1. {step_1}
2. {step_2}
3. {step_3}

**主成果物**: {primary_output}

**品質基準**:
- {quality_criterion_1}
- {quality_criterion_2}

**前提Skill**: {prerequisite_skill}

**後続Skill**: {next_skill}

---

## 依存関係図

```
Phase 1          Phase 2          Phase 3
┌─────┐         ┌─────┐         ┌─────┐
│ 01  │────────▶│ 04  │────────▶│ 07  │
└─────┘         └─────┘         └─────┘
    │               │
    ▼               ▼
┌─────┐         ┌─────┐         ┌─────┐
│ 02  │────────▶│ 05  │────────▶│ 08  │
└─────┘         └─────┘         └─────┘
    │               │
    ▼               ▼
┌─────┐         ┌─────┐
│ 03  │────────▶│ 06  │
└─────┘         └─────┘
```

---

## フレームワーク対応マッピング

| フレームワークプロセス | 対応Skill | カバー率 |
|----------------------|----------|----------|
| {framework_process_1} | 01, 02 | 100% |
| {framework_process_2} | 03, 04 | 100% |
| {framework_process_3} | 05, 06 | 80% |
| {framework_process_4} | 07 | 60% |
| {framework_process_5} | 08 | 40% |

---

## 成果物一覧

| Skill | 成果物 | 形式 | 保存先 |
|-------|--------|------|--------|
| 01 | {output_1} | Markdown | Flow/{date}/ |
| 02 | {output_2} | Markdown | Flow/{date}/ |
| 03 | {output_3} | Markdown | Stock/documents/ |

---

## 品質保証計画

### QC対象Skill
| Skill | QC Subagent | 評価基準ファイル |
|-------|-------------|-----------------|
| 01 | qa-{skill_01} | evaluation/{skill_01}_criteria.md |
| 02 | qa-{skill_02} | evaluation/{skill_02}_criteria.md |

### 共通品質基準
- [ ] 全SkillにSKILL.md存在
- [ ] 全Skillにassets/存在
- [ ] QC対象Skillにevaluation/存在
- [ ] 1 Skill = 1 WF = 1主成果物
- [ ] フレームワーク準拠率80%以上

---

## 実装計画

### Phase 1 (必須基盤)
- [ ] {domain}-{action1}-{object1}/SKILL.md
- [ ] {domain}-{action1}-{object1}/assets/
- [ ] {domain}-{action2}-{object2}/SKILL.md
- [ ] {domain}-{action2}-{object2}/assets/

### Phase 2 (中核機能)
- [ ] Phase 2 Skills 実装

### Phase 3 (拡張機能)
- [ ] Phase 3 Skills 実装

---

## 変更履歴

| 日付 | バージョン | 変更内容 | 担当 |
|------|-----------|----------|------|
| {{meta.timestamp}} | 1.0 | 初版作成 | {author} |
