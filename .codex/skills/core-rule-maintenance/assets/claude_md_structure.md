# CLAUDE.md 構造ガイド

## 概要

CLAUDE.mdはPMBOK Agentの中核設定ファイル。全Skillsが参照する共通ルールを定義する。

## セクション構成

```
CLAUDE.md
├── 1. コア原則（全Skill共通・絶対ルール）
├── 2. 成果物タイプと語調（PMBOK Agent固有）
├── 3. 品質ゴール
├── 4. Skill選択ポリシー
├── 5. 成果物分類（Personal vs Stock）
├── 6. ワークフロー索引（Skill連携マップ）
└── 7. パス辞書
```

---

## Section 1: コア原則

**絶対ルール**（全Skillで遵守）:
- Skill優先
- テンプレートファースト
- Preflight調査委譲
- 品質ループ
- レッドチーム（反証）
- 推測禁止
- 自己完結
- パス遵守

**変更時の注意**:
- 全Skillsに影響するため、変更は慎重に行う
- 変更後、主要Skillsで整合性を確認する

---

## Section 2: 成果物タイプと語調

| タイプ | 対象 | 語調 |
|--------|------|------|
| Fact型 | 議事録、要件定義、ステータスレポート等 | 中立・簡潔・正確 |
| Proposal型 | 提案書、プレゼン資料、見積等 | 敬体（です・ます） |

---

## Section 3: 品質ゴール

- **欠損ゼロ**: 可視情報を漏れなく反映
- **行間ゼロ**: 初見でも理解できる自己完結
- **ハルシネーションゼロ**: 元資料にない項目は「未記載/不明」

---

## Section 4: Skill選択ポリシー

- 依頼に最も合致するSkillを選定
- 完了後、各SKILL.mdのNext Action triggersに従い継続判断
- 無限ループ禁止

---

## Section 5: 成果物分類

| 分類 | パス | 対象 |
|------|------|------|
| Personal/ | 個人ファイル | 商談準備、個人メモ |
| Stock/programs/ | 共有ファイル | 公式ドキュメント |
| Flow/ | 作業中・一時 | ドラフト、日次タスク |

---

## Section 6: ワークフロー索引

PMBOKフェーズごとのSkill連携を定義。

```yaml
### Initiating（立ち上げ）
project-charter → stakeholder-analysis

### Discovery / Research（調査・発見）
desk-research / customer-research / competitor-research
current-state → gap-analysis → idea-divergence → hypothesis-validation

### Planning（計画）
requirement-specification → wbs → schedule
resource-plan / quality-plan / backlog-yaml

# ... 以下続く
```

**変更時の注意**:
- 矢印（→）は「完了後に次へ進む」を意味
- スラッシュ（/）は「並列または選択」を意味
- 各SkillのNext Action triggersと整合させる

---

## Section 7: パス辞書

### 構造

```yaml
root: "/Users/xxx/Desktop/pmbok-agent"

dirs:
  flow:           "{{root}}/Flow"
  stock:          "{{root}}/Stock"
  programs:       "{{dirs.stock}}/programs"
  # ...

patterns:
  flow_date:      "{{patterns.flow_yearmonth}}/{{today}}"
  draft_charter:  "{{patterns.flow_date}}/draft_project_charter.md"
  # ...

meta:
  today:          "{{env.NOW:date:YYYY-MM-DD}}"
  # ...
```

### 変数参照ルール

1. **参照順序**: root → dirs → patterns → meta
2. **解決方法**: `{{変数名}}` で参照
3. **ネスト**: `{{dirs.stock}}` → `{{root}}/Stock` → `/Users/xxx/Desktop/pmbok-agent/Stock`

### 追加時のチェックリスト

- [ ] 変数名がユニークであること
- [ ] 参照先が存在すること（循環参照NG）
- [ ] 実パスとして有効であること
- [ ] 既存パターンと命名規則が一致すること

---

## 変更フロー

```
1. 変更箇所を特定
2. 影響範囲を確認（関連Skills/パス参照）
3. 最小差分で修正
4. 整合性チェック
5. 3環境同期（update_agent_master.py）
6. 関連Skillsの更新（必要な場合）
```
