# Skills 1WF単位 統一変換ガイド（汎用 / 機能欠損ゼロ / フォーマット強制 / Subagent必須）

## 0. 目的
既存のSkillsをすべて「1 Skill = 1 WF（ワークフロー）」単位へ分解・再編し、SKILL.mdのフォーマットを統一する。

本ガイドで最優先するのは次の2点。
- WFに必要な機能は絶対に欠損させない
- SKILL.mdのフォーマットは必ず統一フォーマットへ変更する

ここでいう「機能欠損させない」は、元Skillが持っていた“全部入り一括実行”を維持することではない。
WF単位への分解は許可し、むしろ必須とする。
ただし、分解後の各WFが成立するために必要な機能（テンプレ準拠、検証、反映、制約、エラー処理等）は欠損禁止。

---

## 1. 絶対ルール（破ったら変換失敗）
### 1.0 フォーマット強制
- 既存の「YAMLキーを大量に列挙する本文形式」は廃止する
- すべてのSkillのSKILL.mdは、本ガイドの「SKILL.md統一フォーマット」に必ず置換する

### 1.1 品質ループでの使用（Subagent必須）
品質ループは必ず次の流れで運用する（最大3回）。
Preflight → 生成 → SubAgentによるQC/チェック/フィードバック → 最小差分修正 → 再QC → 確定（最大3回）

- Skillsは成果物を生成する（単一責務）
- Subagentは並列の評価・チェックを行う
- Subagentの指摘を反映し、反映したか/しないかと理由を成果物（最終出力）に残す

### 1.2 1 Skill = 1 WF（例外なし）
- 1つのSkillに複数の主成果物（例: WBS + スケジュール + UX仕様）を同居させない
- 「主成果物が1つに決まる」単位をWFとして切り出し、Skillを作る

### 1.3 WFに必要な機能は欠損禁止（ただし“WF外の抱き合わせ”は維持必須ではない）
- 分解後のWFが成立するために必要な要素は欠損禁止
  - テンプレ準拠で生成/更新できる
  - Preflightがある
  - SubagentでQCを回す
  - 最小差分で修正する
  - バックログ反映がある（反映＋差分提示）
  - エラー時の扱いがある
- 元Skillが「複数WFを一括でやる」こと自体は維持必須ではない（WF分解OK）

### 1.4 分解時の同梱ルール（assetsは必須、scripts/questionsは必要な場合のみ同梱）
WFを新Skillとして作る際は、WFに必要なリソースを必ず同梱する。
- `assets/`：必須。テンプレ、固定フォーマット、チェック観点、反映規約など
- `scripts/`：必要な場合のみ。反映や抽出など自動処理に必要なもの
- `questions/`：必要な場合のみ。不足情報の収集がWF成立に必須なら同梱する

追加ルール:
- 空ディレクトリは残さない（`.gitkeep` だけ置いてフォルダを維持する運用は禁止）

禁止事項:
- 新Skillが他Skillの `assets/` や `scripts/` を参照して成立する構成（横参照）を禁止
- “共有ディレクトリを参照”で済ませる設計を禁止
- 同梱はコピーを正とする（同名ファイルの複製を許可し、共有参照をしない）

### 1.5 パス情報はSkillに書かない
- 保存先、命名規則、ディレクトリ構造、パターン変数などの「path情報」は、CLAUDE.md / AGENTS.md を正とし、Skillへ複製しない
- Skillには「全体ルールに従う」旨のみを書く（具体パスは書かない）

### 1.6 CLAUDE.md / AGENTS.md は `templates/AGENTS_TEMPLATE.md` に従って作成する
- AGENTS.md は8セクション構成（詳細は「9. AGENTS.md 作成ガイド」を参照）
- `agent_repository_workflow: |` は **Agent特化の全作業フローを具体的に記述**する（汎用的・抽象的な記述は禁止）
- path情報（保存先、命名、Flow/Stockの原則、例外時の切替）
- バックログ反映の共通ルール（反映先、差分提示、編集制約、例外処理）
- トリガー機能（`master_triggers` / `- trigger:` / Trigger Router）のような「トリガー一覧」は保持しない（削除する）
- 禁止事項（推測禁止、勝手な外部操作禁止、Git操作禁止等）を必ずグローバルに集約する

---

## 2. 用語定義
- WF（Workflow）: 「主成果物の生成 → Subagentチェック → バックログ反映 → 次アクション」までが完結する最小単位
- 主成果物: そのWFが直接作る/更新する中心アウトプット（1つに限定）
- Preflight: 参照すべき既存資料の確認、前提・不足情報の整理、未参照の明示（推測しない）
- バックログ反映: 次アクション（Epic/Story/Task等）をバックログに反映し、変更差分を提示する工程
- Subagent: 並列評価・チェック専用のエージェント（成果物生成は担当しない）

---

## 3. SKILL.md 統一フォーマット（必須）
### 3.0 frontmatter ルール
- 必須: `name`, `description` のみ
- 禁止: path_reference 等のパス情報や運用パラメータをSkillに書くこと

### 3.1 必須見出し
SKILL.md本文は必ず次の見出しだけを使用する。
- `# XXX Workflow`
- `## Instructions`
- `## Resources`
- `## Next Action`（準必須: 原則必ず書く。省略する場合は「次アクション無し」が明確なWFに限る）

### 3.2 Instructions に必ず含める工程
Instructions には必ず次を含める（表現は自由だが内容は欠かさない）。
- Preflight（参照・不足情報・未参照の明示）
- 生成（主成果物をテンプレ/固定フォーマットに従って作成/更新）
- SubagentによるQC（品質ループを最大3回）
- 最小差分修正（Subagent指摘に対して必要最小限の修正のみ）
- バックログ反映（反映＋差分提示）
- 制約/禁止（WF成立に必須な制約。詳細なパスは書かない）

---

## 4. Subagent運用（必須）

### 4.1.1 必須セクション（全Skillsに追記すべき内容）
全てのSKILL.mdは、本文（通常はInstructionsの末尾）に次を必ず含める。

subagent_policy:
  - 品質ループ（QC/チェック/フィードバック）は必ずサブエージェントへ委譲する
  - サブエージェントの指摘を反映し、反映結果（修正有無/理由）を成果物に残す

recommended_subagents:
  - QC/チェック/フィードバックを担当するサブエージェント名と目的を列挙

注意:
- これは見出しではなく、本文内の“必須記述ブロック”として含める
- “成果物に残す”は、最終出力に「Subagent指摘→対応結果（修正/非修正と理由）」が追跡可能な形で含まれている状態を指す
  - テンプレにレビュー欄があればそこへ記載
  - なければ末尾に短い「QC結果/修正ログ」を付記する（主成果物の章立ては崩さない）

### 4.3 Skillsとの責務分離（本リポジトリ方針）
本リポジトリの方針は以下で固定する。

| 役割 | 担当 |
|---|---|
| 成果物生成（単一責務） | Skills |
| 並列の評価・チェック | Subagent |

例:
- meeting-minutes Skill → 議事録本文を生成
- qa-minutes Subagent → 抜け漏れ（決定/未決/論点/リスク/アクション/担当/期日）を検査

---

## 5. 変換手順（既存Skill → 1WF Skills）
### Step 1: 元SkillをWFに分解して棚卸しする
元Skillから「主成果物が1つに定まる単位」をWFとして列挙する。
各WFについて最低限これを決める。
- 主成果物（1つ）
- 使用テンプレ/固定フォーマット（assets候補）
- バックログ反映の形（Task/Epic/Story等への落とし方）
- 自動処理が必要か（scripts候補）
- チェック観点（Subagentが評価すべき観点）

禁止:
- 1WFに主成果物を複数入れる
- “計画一式” “実行全般” のように曖昧な塊でWFを切る

### Step 2: WFごとに新Skillディレクトリを作る（同梱）
WFごとに新Skillを作り、次を必ず同梱する。
- `SKILL.md`
- `assets/`（必須: WFに必要なテンプレ/規約）
- `scripts/`（必要なら: WFに必要な自動処理）
- `questions/`（必要なら: WF成立に必要な質問）

同梱の原則:
- 元Skillの `assets/ scripts/ questions` を、WFに必要な分だけ選んでコピーする
- 他Skillの参照で成立させない（横参照禁止）

### Step 3: 新SkillのSKILL.mdを統一フォーマットで作る
- 見出しは `# XXX Workflow`, `## Instructions`, `## Resources`, `## Next Action` のみ
- Instructionsには必ず「Preflight→生成→Subagent QC→最小差分修正→再QC→確定→バックログ反映」を含める
- Instructionsの末尾に 4.1.1 の必須ブロック（subagent_policy/recommended_subagents）を必ず入れる
- Resourcesは同梱ファイルを相対パスで列挙する（`./assets/...` 等）

### Step 4: 元Skillの扱いを決める（WF粒度への収束）
元Skillについては次のいずれかに統一する（混在させない）。
A) 元Skillを残し、分解後のWF Skillsへの導線（Next Action）だけを追加して移行する
B) 元Skillを1WFに縮退させ、他WFは新Skillへ完全移行する

どちらの場合も必須:
- 元Skillが担っていたWFが消えないこと（新Skill群で全WFが再現できること）

### Step 5: 欠損チェック（必須）
WFごとに次を確認し、満たさない場合は変換失敗とする。
- 主成果物がテンプレ準拠で生成/更新できる
- Preflightがある（未参照/不足の明示、推測禁止）
- Subagent QCループがある（最大3回、最小差分修正）
- バックログ反映がある（反映＋差分提示）
- 必要な assets/scripts/questions が同梱されている（横参照なし）
- subagent_policy / recommended_subagents が本文に含まれている

---

## 6. description 作成ルール（発火）
descriptionは必ず満たす。
- 第三人称で書く（〜を作成/更新する、〜を反映する）
- 「何をするか」＋「いつ使うか（ユーザーが言う単語）」を含める
- 主成果物が一意に想像できる
- “全般” “一式” “まとめて” のような広すぎる表現を禁止

---

## 7. CLAUDE.md / AGENTS.md に必ず書くこと

**AGENTS.md の作成・編集は `templates/AGENTS_TEMPLATE.md` に従う。詳細は「9. AGENTS.md 作成ガイド」を参照。**

グローバル側には必ず以下を記述する（Skill側へは複製しない）。
- path情報（保存先、命名、Flow/Stockの原則と例外）
- バックログ反映の共通ルール（編集制約、差分提示、例外処理）
- 禁止事項（推測禁止、外部操作禁止、Git操作禁止等）
- エラー時の基本方針（ロールバック、未記載、再検証）

追加ルール（トリガー機能は置かない）:
- `master_triggers` / `- trigger:` / Trigger Router のような「トリガー一覧」は保持しない（削除する）。
- `agent_repository_workflow: |` は **Agent特化の全作業フローを具体的に記述**する（汎用的・抽象的な記述は禁止）。

---

## 8. 変換完了チェックリスト
- [ ] 全Skillが1WF単位になっている（主成果物が1つ）
- [ ] 全SkillのSKILL.mdが統一フォーマット（必須見出し）になっている
- [ ] 全SkillのInstructionsに品質ループ（Subagent必須）が含まれている
- [ ] 全Skillに subagent_policy / recommended_subagents の必須ブロックが含まれている
- [ ] 全Skillがバックログ反映＋差分提示を行う
- [ ] 分解したSkillは必要な assets/scripts/questions を同梱している（横参照なし）
- [ ] path情報はCLAUDE.md/AGENTS.mdに集約され、Skillに複製されていない
- [ ] CLAUDE.md/AGENTS.mdに全体フローが明記されている


```
サンプル：
このガイドに従うと、あなたが以前出していたサンプル（議事録・WBSなど）は、**「1WF＝1Skill」＋「Subagentで必ずQC」＋「必須見出し固定」**の形に置き換わります。以下は参考例であり、各WF/各Agentに合わせて編集する前提です。

---

## 1) まず“完成形の雛形”（全Skill共通の最小フォーマット）

```markdown
---
name: <wf-name>-workflow
description: "<主成果物>を作成/更新し、Subagentでチェックし、バックログへ反映する。<ユーザーが言いがちなトリガー語>を依頼されたときに使用する。"
---

# <WF名> Workflow

## Instructions
1. Preflight:
   - ドキュメント精査原則（Preflight必須）：テンプレート確認後、生成前に必ず以下を実施すること。
     - アジェンダ・依頼文に記載された参照資料を全て読み込む。
     - Flow/Stock配下の関連資料（前回議事録・要望リスト・プロジェクトREADME等）を網羅的に検索・確認する。
     - 確認できなかった資料は「未参照一覧」として成果物に明記する。
     - これらを完了するまで生成を開始しない。
   - 参照すべき既存資料があれば読み、前提・不足情報・未参照を整理する（推測しない）。
2. 生成: `./assets/<template>` を先に読み、章立て・必須項目・順序を維持して主成果物を作成/更新する。不足は「未記載」で残す。
3. QC（必須）:
   - `recommended_subagents` のQC Subagentに評価・チェックを委譲する。
   - 指摘を最小差分で反映する。
   - 再度SubagentでQCする。
   - これを最大3回まで繰り返し、確定する。
   - 指摘に対し「修正した/しない」と理由を主成果物に残す（テンプレに欄があればそこへ。なければ末尾へ短く追記。テンプレの章立ては崩さない）。
4. バックログ反映:
   - 次アクション（Task/Epic/Story等）を抽出しバックログへ反映する。
   - 反映先・編集制約・差分提示は、AGENTS.md / CLAUDE.md の全体ルールに従う（Skillにパスは書かない）。
   - 反映後に差分（変更前→変更後）を提示する。

subagent_policy:
  - 品質ループ（QC/チェック/フィードバック）は必ずサブエージェントへ委譲する
  - サブエージェントの指摘を反映し、反映結果（修正有無/理由）を成果物に残す

recommended_subagents:
  - <qa-subagent-name>: <チェック観点の要約>

## Resources
- assets: ./assets/<...>.md
- questions: ./questions/<...>.md（必要な場合のみ）
- scripts: ./scripts/<...>.py（必要な場合のみ）

## Next Action
- 次に実行すべきWF（Skill）や、ユーザー確認事項を記載する。
```

---

## 2) サンプル：Meeting Minutes Workflow（議事録→QC→バックログ反映を1Skillに統合）

```markdown
---
name: meeting-minutes-workflow
description: "議事録をテンプレートに従って作成し、Subagentで抜け漏れをチェックしたうえで、決定事項/アクションをバックログへ反映する。議事録、会議要約、決定事項、ToDo、アクションアイテム、担当、期限の整理を依頼されたときに使用する。"
---

# Meeting Minutes Workflow

## Instructions
1. Preflight:
   - ドキュメント精査原則（Preflight必須）：テンプレート確認後、生成前に必ず以下を実施すること。
     - アジェンダ・依頼文に記載された参照資料を全て読み込む。
     - Flow/Stock配下の関連資料（前回議事録・要望リスト・プロジェクトREADME等）を網羅的に検索・確認する。
     - 確認できなかった資料は「未参照一覧」として成果物に明記する。
     - これらを完了するまで生成を開始しない。
   - アジェンダ、前回議事録、関連資料があれば読み、前提・不足情報・未参照を整理する（推測しない）。
2. 生成: `./assets/meeting_minutes_template.md` を先に読み、章立て・必須項目・順序を維持して議事録を作成する。
   - 事実と意見を分離する。
   - 決定事項は「決定/条件/担当/期限」を最小単位で記録する。
   - 不足情報は「未記載」と明示する。
3. QC（必須）:
   - `qa-meeting-minutes` に評価・チェックを委譲する。
   - 指摘を最小差分で反映する。
   - 再度 `qa-meeting-minutes` でQCする。
   - 最大3回まで繰り返し、確定する。
   - Subagent指摘への対応（修正/非修正と理由）を議事録に残す（テンプレに欄があればそこへ。なければ末尾へ短く追記。章立ては崩さない）。
4. バックログ反映:
   - 議事録からアクションをTaskに分解し、バックログへ反映する。
   - 反映先・編集制約・差分提示は、AGENTS.md / CLAUDE.md の全体ルールに従う（Skillにパスは書かない）。
   - 反映後に差分（変更前→変更後）を提示する。

subagent_policy:
  - 品質ループ（QC/チェック/フィードバック）は必ずサブエージェントへ委譲する
  - サブエージェントの指摘を反映し、反映結果（修正有無/理由）を成果物に残す

recommended_subagents:
  - qa-meeting-minutes: 抜け漏れ（決定/未決/論点/リスク/アクション/担当/期日）と事実意見分離、必須項目欠落を検査

## Resources
- questions: ./questions/meeting_minutes_questions.md
- assets: ./assets/meeting_minutes_template.md
- assets: ./assets/backlog_reflection_rules.md
- scripts: ./scripts/actions_to_backlog.py

## Next Action
- 未決事項が意思決定待ちなら decision-workflow を実行する。
- 日次の進捗管理に落とすなら daily-task-workflow を実行する。
```

---

## 3) サンプル：WBS Workflow（WBSだけ。スケジュール等は別Skill）

```markdown
---
name: wbs-workflow
description: "WBSをテンプレートに従って作成/更新し、Subagentで整合と欠落をチェックしたうえで、必要な作業をバックログへ反映する。WBS、作業分解、作業パッケージ、成果物、受入基準、DoD、WBS辞書の作成/更新を依頼されたときに使用する。"
---

# WBS Workflow

## Instructions
1. Preflight:
   - ドキュメント精査原則（Preflight必須）：テンプレート確認後、生成前に必ず以下を実施すること。
     - アジェンダ・依頼文に記載された参照資料を全て読み込む。
     - Flow/Stock配下の関連資料（前回議事録・要望リスト・プロジェクトREADME等）を網羅的に検索・確認する。
     - 確認できなかった資料は「未参照一覧」として成果物に明記する。
     - これらを完了するまで生成を開始しない。
   - 既存のWBSや関連計画があれば読み、前提・不足情報・未参照を整理する（推測しない）。
2. 生成: `./assets/wbs_template.md` を先に読み、章立て・必須項目・順序を維持してWBSを作成/更新する。
   - DoD（完了の定義）を付与する。
   - 前提・依存関係・受入基準を明記する。
   - 不足情報は「未記載」と明示する。
3. QC（必須）:
   - `qa-wbs` に評価・チェックを委譲する。
   - 指摘を最小差分で反映する。
   - 再度 `qa-wbs` でQCする。
   - 最大3回まで繰り返し、確定する。
   - Subagent指摘への対応（修正/非修正と理由）をWBS成果物に残す（テンプレに欄があればそこへ。なければ末尾へ短く追記。章立ては崩さない）。
4. バックログ反映:
   - WBSの作業パッケージから次アクションをTask化し、バックログへ反映する。
   - 反映先・編集制約・差分提示は、AGENTS.md / CLAUDE.md の全体ルールに従う（Skillにパスは書かない）。
   - 反映後に差分（変更前→変更後）を提示する。

subagent_policy:
  - 品質ループ（QC/チェック/フィードバック）は必ずサブエージェントへ委譲する
  - サブエージェントの指摘を反映し、反映結果（修正有無/理由）を成果物に残す

recommended_subagents:
  - qa-wbs: テンプレ必須項目欠落、DoD/前提/依存関係/受入基準の不足、分解の抜け・重複、整合矛盾を検査

## Resources
- questions: ./questions/wbs_questions.md
- assets: ./assets/wbs_template.md
- assets: ./assets/backlog_reflection_rules.md
- scripts: ./scripts/wbs_to_backlog.py

## Next Action
- スケジュール化が必要なら schedule-workflow を実行する。
```

---

### 補足：このサンプルが意味する「分解結果」

たとえば元の `pmbok-planning` は「計画一式」ではなく、**WBS WF / スケジュール WF / 資源計画 WF / 品質計画 WF / UX仕様 WF / backlog編集WF…**のように、**主成果物が1つに定まるWFごとにSkillが分かれます**（1WF=1Skillルール）。

---

## 9. AGENTS.md 作成ガイド（AGENTS_TEMPLATE.md の使い方）

新しいAgentリポジトリを作成する際、または既存のAGENTS.mdを統一フォーマットへ変換する際は、**`templates/AGENTS_TEMPLATE.md`** を参照して作成する。

### 9.1 AGENTS.md の8セクション構成

AGENTS.md は以下の8セクションで構成する。

| # | セクション | 内容 | カスタマイズ |
|---|---|---|---|
| 1 | AI注意事項 | AIが守るべき指示 | 共通項目は維持、ドメイン固有を追加 |
| 2 | 成果物の分類基準 | 成果物の配置ルール | **必須** |
| 3 | 成果物タイプ定義 | 主成果物・副成果物の種類 | **必須** |
| 4 | 品質ループ | Preflight→生成→検証→改善→確定 | **必須** |
| 5 | QCチェックリスト | Must/Should項目 | **必須** |
| 6 | Repository Workflow | Agent全体の作業フロー | **必須（Agent特化で全文記述）** |
| 7 | パス辞書 | ディレクトリ・パターン・メタ変数 | ドメインに合わせて追加 |
| 8 | 推奨Skill一覧 | Skillを列挙（任意） | MDCルールで定義済みなら参照のみ |

### 9.2 カスタマイズ必須セクション（2〜6）

セクション2〜6は「【カスタマイズ必須】」であり、各Agentのドメインに合わせて具体的に記述する。

**テンプレートに記載の例を参考に、実際の値を埋める**：
- DifyFlow Agent → Difyフロー開発に特化した内容
- 小説作成Agent → 執筆・推敲に特化した内容
- システム開発Agent → コード開発に特化した内容
- Chrome拡張機能Agent → 拡張機能開発に特化した内容

### 9.3 agent_repository_workflow の書き方（最重要）

**`agent_repository_workflow: |` は、今作成/編集しているAgentが持つ全Skillsを統合したエンドツーエンドの作業フローを記述する。**

これは1つのSkillのワークフローではなく、**今作成しているAgent全体として案件をどう進めるか**を示す統合ワークフローである。各Phaseの中で、対応するSkill（例: requirements-workflow, validation-workflow など）が呼び出される想定で書く。

禁止事項：
- 汎用的・抽象的な記述（「要件を確認する」「成果物を作成する」等）
- 他Agentからのコピペそのまま
- 1つのSkillのワークフローだけを書く

必須事項：
- **Phase単位で分割**し、各Phaseの具体的なステップを記述する
- **ファイル名・フォルダ構造・ツール名・スクリプト名**を具体的に書く
- **プロジェクト立ち上げ→要件定義→開発→テスト→ナレッジ蓄積**のような、開始から終了までの全工程を網羅する
- Agent内の複数Skillsがどう連携するかがわかる粒度で書く

例（DifyFlow Agentの場合）：
```yaml
agent_repository_workflow: |
  ## DifyFlow Agent 統合ワークフロー

  ### Phase 1: 案件プロジェクト立ち上げ
  1) 案件プロジェクト作成
     - クライアント案件: dify/clients_dify_flow/{client}/{project}/ に構造作成
     - README.md、requirements/、flow_log/ 等を初期化

  ### Phase 2: AsIs-ToBe分析（要件定義）
  2) 現状分析（AsIs）
     - 業務プロセス・課題・ペインポイントのヒアリング
     - asis_analysis_YYYY-MM-DD.md を作成

  3) 理想状態設計（ToBe）
     - 理想の業務プロセス・自動化対象の特定
     - tobe_design_YYYY-MM-DD.md を作成

  4) ギャップ分析 & Dify実装方針
     - Workflow / Chatflow / Trigger の選定
     - gap_analysis_dify_definition_YYYY-MM-DD.md を作成

  ### Phase 3: Difyフロー開発
  5) テンプレート選定
  6) YML生成・カスタマイズ
  7) Validation（必須）: `python scripts/dify_validation.py <YML>`

  ### Phase 4: インポート・テスト
  8) Difyインポート: scripts/dify_import_api.py
  9) 動作テスト: scripts/dify_test_runner.py

  ### Phase 5: ブラッシュアップ・反復
  10) 既存フローブラッシュアップ
  11) 反復サイクル

  ### Phase 6: テンプレート化・ナレッジ蓄積
  12) テンプレート登録
  13) ドキュメント整備
  14) ナレッジ蓄積
```

### 9.4 AI注意事項（セクション1）の書き方

共通項目は維持し、ドメイン固有の注意事項を追加する。

**共通項目（全Agentで維持推奨）**：
```yaml
ai_instructions:
  - "すべてのルールは正確に実行し、独自の解釈で変更しないこと。"
  - "指定されたファイルパスやフォルダ構造を尊重し、勝手に構造を変更しないこと。"
  - "失敗した場合でも代替手段を取らず、失敗を報告してユーザーの指示を仰ぐこと。"
  - "テンプレートがある場合はテンプレートファースト原則：生成前に該当テンプレートの構造を確認し、その構造に従うこと。テンプレートがない場合はドメインの標準的な構造・慣習に従うこと。"
  - "品質ループ：Preflight→生成→自己評価→改善→確定のサイクルを実施すること（最大3反復）。"
  - "元資料にない項目は『未記載』または『不明』と明記し、推測で埋めないこと。"
  - "Skillが定義されている場合は、依頼に最も合致するSkillを選んで実行すること。"
```

**ドメイン固有の追加例**：
```yaml
  # DifyFlow Agent:
  - "graph.nodesに存在しないノードIDをsource/targetに設定しないこと。"
  - "YMLファイル名は英数字・ハイフン・アンダースコアのみとし、日本語ファイル名を禁止する。"

  # システム開発Agent:
  - "既存コードのスタイル・命名規則に従うこと。"
  - "セキュリティ脆弱性（OWASP Top 10）を作り込まないこと。"
```

### 9.5 推奨Skill一覧（セクション8）の書き方

SkillsがMDCルールで既に定義されている場合は、詳細をAGENTS.mdに書かず、参照のみとする。

```yaml
# =========================
# 8. 推奨Skill一覧
# =========================
# Skillsは .cursor/rules/ 配下の各MDCルールで定義済み。
# 詳細は各ルールファイルを参照。
```

Skillsを新規定義する場合のみ、ここに列挙する。

### 9.6 AGENTS.md 作成手順

1. `templates/AGENTS_TEMPLATE.md` をコピーして `AGENTS.md` を作成する
2. `{{AGENT_NAME}}` をAgent名に置換する（例: `DifyFlow Agent`）
3. セクション1のドメイン固有注意事項を追加する
4. セクション2〜5をドメインに合わせて具体的に記述する
5. セクション6（`agent_repository_workflow`）を**Agent特化で全文記述**する
6. セクション7のパス辞書をドメインに合わせて追加・修正する
7. セクション8はMDCルールで定義済みなら参照のみにする

### 9.7 記法ルール

- **`----` 装飾は使用禁止**
  - `# ---- 問い合わせ管理 ----` → `# 問い合わせ管理` のように `----` を削除し、見出しテキストのみ残す
  - 可読性のための空行は許可する

