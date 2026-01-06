# Next Action Triggers 仕様書

## 1. 概要

Skillの`## Next Action`セクションで参照する起動条件ファイル（`triggers/next_action_triggers.md`）の作成・メンテナンスルールを定義する。

**目的**: WF連携において「条件を満たせば必ず次Skillを実行する」という自動継続を実現する。

---

## 2. フォルダ構成

```
skills/{skill-name}/
├── SKILL.md
├── assets/
├── questions/
├── evaluation/
├── scripts/
└── triggers/                      # 起動条件フォルダ
    └── next_action_triggers.md    # 起動条件定義ファイル
```

---

## 3. next_action_triggers.md のフォーマット

```markdown
# {Skill名} Next Action Triggers

## 自動実行ルール
**以下の条件を満たす場合は、該当Skillを必ず実行すること（WF自動継続）。**
条件判定はSkill完了時に自動で行い、スキップ条件に該当しない限り次Skillへ進む。

## 起動条件テーブル

| ID | 起動条件 | 実行Skill | 優先度 | 備考 |
|----|---------|-----------|--------|------|
| T1 | {検証可能な条件} | `skill-name` | 1 | {補足} |
| T2 | {検証可能な条件} | `skill-name` | 2 | {補足} |

## スキップ条件
以下の場合のみ、起動条件を満たしても実行をスキップできる:
- ユーザーが明示的に「{Skill名}のみ」と指定した場合
- {その他のスキップ条件}

## 条件判定ロジック
1. Skill完了時、起動条件テーブルを上から順に評価する
2. 条件を満たす行があれば、スキップ条件を確認する
3. スキップ条件に該当しなければ、該当Skillを実行する
4. 複数条件が該当する場合は、優先度順に全て実行する（並列可能なら並列実行）
```

---

## 4. 起動条件の書き方ルール

### 4.1 検証可能な条件を書く

**NG例（曖昧）**:
- 「必要なら」「〜したい場合」「〜が求められる場合」

**OK例（検証可能）**:
- 「成果物に〜セクションが存在する」
- 「〜が未作成（該当ファイルが存在しない）」
- 「成果物のステータスが〜である」
- 「〜フィールドが空欄/未記載」
- 「依頼文に〜が含まれる」

### 4.2 条件の粒度

| 粒度 | 例 | 推奨 |
|------|-----|------|
| 成果物の状態 | 「WBSにスケジュール未設定のタスクがある」 | OK |
| ファイルの存在 | 「stakeholder_register.mdが存在しない」 | OK |
| フィールドの値 | 「statusフィールドが'draft'」 | OK |
| ユーザー意図の推測 | 「ユーザーが望んでいそうなら」 | NG |

### 4.3 優先度の付け方

| 優先度 | 意味 | 例 |
|--------|------|-----|
| 1 | 必須（条件満たせば常に実行） | 議事録→バックログ反映 |
| 2 | 推奨（通常は実行） | WBS→スケジュール |
| 3 | 任意（明示的指示があれば実行） | ドキュメント→PDF納品 |

---

## 5. SKILL.mdでの参照方法

```markdown
## Next Action
- triggers: ./triggers/next_action_triggers.md

起動条件に従い、条件を満たすSkillを自動実行する。
```

---

## 6. メンテナンス手順

### 6.1 新規Skill作成時
1. `triggers/`フォルダを作成
2. `next_action_triggers.md`を本仕様に従って作成
3. SKILL.mdのNext Actionセクションから参照
4. SKILL.mdのResourcesセクションに追加:
   ```markdown
   - triggers: ./triggers/next_action_triggers.md
   ```

### 6.2 既存Skillへの追加時
1. 現在のNext Actionセクションの内容を分析
2. 「〜なら」「〜の場合は」を検証可能な条件に変換
3. `triggers/next_action_triggers.md`を作成
4. SKILL.mdを更新

### 6.3 起動条件の変更時
1. `triggers/next_action_triggers.md`を直接編集
2. 変更理由をコミットメッセージに記載
3. 影響を受けるSkill（呼び出し元/呼び出し先）を確認

---

## 7. 変換例

### Before（従来形式）
```markdown
## Next Action
- スケジュールが必要なら `pmbok-schedule` を実行する。
- リソース計画が必要なら `pmbok-resource-plan` を実行する。
```

### After（triggers形式）
```markdown
<!-- triggers/next_action_triggers.md -->
# pmbok-wbs Next Action Triggers

## 自動実行ルール
以下の条件を満たす場合は、該当Skillを必ず実行すること（WF自動継続）。

## 起動条件テーブル

| ID | 起動条件 | 実行Skill | 優先度 | 備考 |
|----|---------|-----------|--------|------|
| T1 | WBSにタスクが1件以上存在する | `pmbok-schedule` | 1 | WBS完成後は必ずスケジュール化 |
| T2 | WBSに担当者未割当のタスクがある | `pmbok-resource-plan` | 2 | リソース計画で担当を確定 |

## スキップ条件
- ユーザーが「WBSのみ作成」と明示した場合
- プロジェクト憲章で「スケジュール管理対象外」と定義されている場合
```

---

## 8. WF連携マップとの整合性

CLAUDE.mdの「ワークフロー索引」と起動条件は整合させること。

```yaml
# CLAUDE.md Section 6 より
### Planning（計画）
requirement-specification → wbs → schedule
resource-plan / quality-plan / backlog-yaml
```

上記の場合:
- `requirement-specification`のtriggersに`wbs`への起動条件を定義
- `wbs`のtriggersに`schedule`への起動条件を定義

---

## 9. チェックリスト

triggers作成時は以下を確認:

- [ ] 全ての起動条件が検証可能（曖昧表現なし）
- [ ] 優先度が設定されている
- [ ] スキップ条件が明示されている
- [ ] CLAUDE.mdのワークフロー索引と整合している
- [ ] SKILL.mdのResourcesに参照を追加した
- [ ] 呼び出し先Skillが存在する（skill名のtypoなし）
