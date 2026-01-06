# Domain Skills Generate Next Action Triggers

## 自動実行ルール
**以下の条件を満たす場合は、該当Skillを必ず実行すること（WF自動継続）。**
条件判定はSkill完了時に自動で行い、スキップ条件に該当しない限り次Skillへ進む。

## 起動条件テーブル

| ID | 起動条件 | 実行Skill | 優先度 | 備考 |
|----|---------|-----------|--------|------|
| T1 | `output/{domain}_agent/.cursor/skills/` 配下に新規Skillディレクトリが1つ以上生成された | `rule-validation` | 1 | Skills/Agents/Commandsの整合性を検証 |
| T2 | 生成した各SKILL.mdの `recommended_subagents` に「qa-」以外のサブエージェント名が含まれる | `subagent-generate` | 2 | Skills携帯Subagentを生成 |
| T3 | 生成したSkillに追加修正が必要 | `skill-maintenance` | 3 | 個別Skillのブラッシュアップ |

## スキップ条件
以下の場合のみ、起動条件を満たしても実行をスキップできる:
- ユーザーが明示的に「Skills生成のみ」と指定した場合
- 検証目的のドライラン（反映なし）の場合

## 条件判定ロジック
1. Skill完了時、起動条件テーブルを上から順に評価する
2. 条件を満たす行があれば、スキップ条件を確認する
3. スキップ条件に該当しなければ、該当Skillを実行する
4. 複数条件が該当する場合は、優先度順に全て実行する

