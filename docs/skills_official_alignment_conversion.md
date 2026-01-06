# Skills 1WF単位 統一変換ガイド（汎用 / 機能欠損ゼロ / フォーマット強制 / Subagent必須）

最終更新: 2025-12-28

## 0. 目的

既存のSkillsをすべて「1 Skill = 1 WF（ワークフロー）」単位へ分解・再編し、SKILL.mdのフォーマットを統一する。

本ガイドは**全Agentで共通**のフレームワークであり、各Agentは自身のドメインに特化した内容でカスタマイズする。

### 本ガイドの最優先事項
1. WFに必要な機能は絶対に欠損させない
2. SKILL.mdのフォーマットは必ず統一フォーマットへ変更する
3. CLAUDE.md / AGENTS.md はスリム化し、詳細はSkillsに委譲する

---

## 1. 絶対ルール（破ったら変換失敗）

### 1.0 フォーマット強制
- 既存の「YAMLキーを大量に列挙する本文形式」は廃止する
- すべてのSkillのSKILL.mdは、本ガイドの「SKILL.md統一フォーマット」に必ず置換する

### 1.1 品質ループでの使用（Subagent必須）
品質ループは必ず次の流れで運用する（最大3回）。

```
Preflight → 生成 → SubAgentによるQC/チェック/フィードバック → 最小差分修正 → 再QC → 確定（最大3回）
```

- Skillsは成果物を生成する（単一責務）
- Subagentは並列の評価・チェックを行う
- Subagentの指摘を反映し、反映したか/しないかと理由を成果物（最終出力）に残す

### 1.2 1 Skill = 1 WF（例外なし）
- 1つのSkillに複数の主成果物（例: WBS + スケジュール + UX仕様）を同居させない
- 「主成果物が1つに決まる」単位をWFとして切り出し、Skillを作る

### 1.3 WFに必要な機能は欠損禁止（ただし"WF外の抱き合わせ"は維持必須ではない）
分解後のWFが成立するために必要な要素は欠損禁止：
- テンプレ準拠で生成/更新できる
- Preflightがある
- SubagentでQCを回す
- 最小差分で修正する
- バックログ反映がある（反映＋差分提示）
- エラー時の扱いがある

元Skillが「複数WFを一括でやる」こと自体は維持必須ではない（WF分解OK）

### 1.4 分解時の同梱ルール（assetsは必須、evaluation/scripts/questionsは必要な場合のみ同梱）
WFを新Skillとして作る際は、WFに必要なリソースを必ず同梱する。

| フォルダ | 同梱要否 | 内容 |
|----------|----------|------|
| `assets/` | 必須 | テンプレ、固定フォーマット、反映規約など |
| `evaluation/` | 必須（QCがあるWF） | 評価指標・チェック観点・採点基準。SubagentはこれをまずReadしてからQCを開始する |
| `scripts/` | 必要な場合のみ | 反映や抽出など自動処理に必要なもの |
| `questions/` | 必要な場合のみ | 不足情報の収集がWF成立に必須なら同梱する |

追加ルール:
- 空ディレクトリは残さない（`.gitkeep` だけ置いてフォルダを維持する運用は禁止）

禁止事項:
- 新Skillが他Skillの `assets/` や `scripts/` を参照して成立する構成（横参照）を禁止
- "共有ディレクトリを参照"で済ませる設計を禁止
- 同梱はコピーを正とする（同名ファイルの複製を許可し、共有参照をしない）

### 1.5 パス情報はSkillに書かない
- 保存先、命名規則、ディレクトリ構造、パターン変数などの「path情報」は、CLAUDE.md / AGENTS.md を正とし、Skillへ複製しない
- Skillには「全体ルールに従う」旨のみを書く（具体パスは書かない）

### 1.6 CLAUDE.md / AGENTS.md のスリム化原則
- 詳細な手順・QCチェックリストは各SKILL.mdに記載する
- CLAUDE.md / AGENTS.md にはコア原則とワークフロー索引のみを残す
- 各Agentのドメインに特化した内容で作成する（汎用的な記述は禁止）

---

## 2. 用語定義

| 用語 | 定義 |
|------|------|
| WF（Workflow） | 「主成果物の生成 → Subagentチェック → バックログ反映 → 次アクション」までが完結する最小単位 |
| 主成果物 | そのWFが直接作る/更新する中心アウトプット（1つに限定） |
| Preflight | 参照すべき既存資料の確認、前提・不足情報の整理、未参照の明示（推測しない） |
| バックログ反映 | 次アクション（Epic/Story/Task等）をバックログに反映し、変更差分を提示する工程 |
| Subagent | 並列評価・チェック専用のエージェント（成果物生成は担当しない） |

※ 成果物タイプ（Fact型/Proposal型等）の定義は各Agent固有のため、CLAUDE.md / AGENTS.md で定義する

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

1. **Preflight**（参照・不足情報・未参照の明示）
2. **生成**（主成果物をテンプレ/固定フォーマットに従って作成/更新）
3. **QC（必須）**（SubagentによるQC、品質ループを最大3回）
4. **バックログ反映**（反映＋差分提示）

### 3.3 subagent_policy と recommended_subagents（必須ブロック）
全てのSKILL.mdは、Instructionsの末尾に次を必ず含める。

```yaml
subagent_policy:
  - 品質ループ（QC/チェック/フィードバック）は必ずサブエージェントへ委譲する
  - サブエージェントの指摘を反映し、反映結果（修正有無/理由）を成果物に残す

recommended_subagents:
  - <qa-subagent-name>: <チェック観点の要約>
```

---

## 4. CLAUDE.md / AGENTS.md 構成ガイド

### 4.1 設計原則

| 原則 | 理由 |
|------|------|
| **100-150行以内** | AIが毎回読むため、コンパクトに |
| **Skillsへ委譲** | 詳細手順・QCチェックリストは各SKILL.mdに記載 |
| **Agent特化** | 各Agentのドメインに特化した具体的な内容で作成 |
| **索引形式** | ワークフローは詳細手順ではなく、Skill連携マップとして記載 |

### 4.2 CLAUDE.md の必須セクション

```markdown
# {Agent名}

## 1. コア原則（全Skill共通・絶対ルール）
- Skill優先: 依頼に合致するSkillを選んで実行
- テンプレートファースト: 各Skillのassets/を先に読む
- 品質ループ: Preflight→生成→Subagent QC→反映（最大3回）※ほとんどの場合必要
- 推測禁止: 元資料にない項目は「未記載」と明記
- 自己完結: 成果物に前提/背景/出典/参照を含める

## 2. 成果物タイプと語調（Agent固有）
{各Agentのドメインに応じた成果物タイプと語調ルールを定義}

## 3. 品質ゴール
- 欠損ゼロ: 参照データの可視情報を漏れなく反映
- 行間ゼロ: 初見でも前提・背景から理解できる自己完結
- ハルシネーションゼロ: 元資料にない項目は「未記載/不明」

## 4. Skill選択ポリシー
- 依頼に最も合致するSkillを選んで実行
- 完了後、各SKILL.mdのNext Actionに従い継続判断

## 5. ワークフロー索引（Skill連携マップ）
{Agent固有のPhase構成とSkill連携を索引形式で記載}

## 6. パス辞書
root: {Agent固有のルートパス}
dirs:
  {Agent固有のディレクトリ構成}
```

### 4.3 ワークフロー索引の書き方

**禁止**: 詳細な手順書形式（各Phaseの具体的ステップを長文で記述）
**推奨**: 索引/マップ形式（Skill連携の流れを簡潔に示す）

```markdown
## 5. ワークフロー索引

### Phase 1: {Phase名}
{skill-a} → {skill-b}

### Phase 2: {Phase名}
{skill-c} / {skill-d}
{skill-e} → {skill-f}

### 横断プロセス
{utility-skill-a} / {utility-skill-b}
```

### 4.4 CLAUDE.md から削除すべきもの（移管必須）

**絶対ルール: CLAUDE.mdから削除する内容は、削除前に必ず該当Skillへ移管すること**

- 移管先が明確でない場合は、削除前に「どのSkillへ移管するか」を決定する
- 該当Skillに既に同等の内容がある場合のみ、移管せず削除してよい
- 移管先が複数Skillにまたがる場合は、各Skillへ個別に移管する
- パス辞書（root/dirs/patterns/meta）は削除対象外（CLAUDE.mdに完全維持）

| 削除対象 | 移管先 | 備考 |
|----------|--------|------|
| 品質ループ詳細手順（prompt_self_review_protocol等） | 各SKILL.mdのInstructions | 既存Skillに記載済みなら移管不要 |
| QCチェックリスト詳細（qc_checklist） | 各SKILL.mdのassets/ | Agent固有の成果物タイプ別チェック観点として移管 |
| QCメモフォーマット（prompt_qc_output_format） | 各SKILL.mdのassets/ | 必要なSkillのみに移管 |
| 修正ポリシー詳細（prompt_revision_policy） | 各SKILL.mdのInstructions | 「最小差分で反映」に統合 |
| 成果物配置先の詳細 | 不要（パス辞書で十分） | 移管不要 |
| ワークフロー詳細手順（agent_repository_workflow） | 各SKILL.mdのInstructions/Next Action | Phase別に該当Skillへ分散移管 |
| recommended_skills一覧 | 不要（索引で代替） | 移管不要 |
| 成果物タイプ定義詳細（artifact_types） | 各SKILL.mdのassets/ | Agent固有の成果物タイプのテンプレート補足として移管 |
| ai_instructions詳細 | 各SKILL.mdのInstructions | Skill固有のルールとして移管 |

**移管チェックリスト（削除前に必須確認）**
- [ ] 削除対象の内容を特定した
- [ ] 移管先Skillを決定した（複数可）
- [ ] 移管先Skillに内容を追加した
- [ ] 移管後の欠損がないことを確認した
- [ ] CLAUDE.mdから削除した

### 4.5 CLAUDE.md に残すべきもの

| 残すもの | 理由 |
|----------|------|
| コア原則（5-6項目） | 全Skill共通の絶対ルール |
| 成果物タイプと語調（Agent固有） | Agentドメイン固有の概念定義 |
| 品質ゴール（3項目） | 全Skill共通の目標 |
| Skill選択ポリシー | ルーティング指針 |
| ワークフロー索引 | Skill連携の全体像 |
| パス辞書（root/dirs/meta） | 保存先の定義 |

---

## 5. Subagent運用（必須）

### 5.1 Skillsとの責務分離

| 役割 | 担当 |
|------|------|
| 成果物生成（単一責務） | Skills |
| 並列の評価・チェック | Subagent |

例:
- meeting-minutes Skill → 議事録本文を生成
- qa-minutes Subagent → 抜け漏れ（決定/未決/論点/リスク/アクション/担当/期日）を検査

### 5.2 recommended_subagents の命名規則

```
qa-{skill-name}: {チェック観点の要約}
```

例:
- `qa-meeting-minutes`: 必須構造（決定/論点/アクション）欠損、曖昧語、推測混入、担当/期日未記載を検査
- `qa-wbs`: 粒度不整合、漏れ/重複、依存/マイルストン欠損を検査

### 5.3 evaluation/ の必須参照ルール

Subagentは評価を開始する前に、必ず `./evaluation/` 配下の評価指標ファイルをReadする。

```
評価指標参照フロー:
1. Subagent起動
2. ./evaluation/<evaluation_criteria>.md をRead
3. 評価指標に基づいてQC実施
4. 指摘事項を評価指標の項目に紐づけて報告
```

評価指標ファイルには以下を含める:
- 必須チェック項目（欠損検知）
- 品質基準（曖昧語、推測混入、形式不備等）
- 採点基準（Pass/Fail条件、重要度レベル）
- 許容例外（意図的に省略してよい条件）

### 5.4 Subagentでの検索・並列処理活用ルール

Subagentは以下のケースで積極的に活用する:

**検索が必要な場合:**
- 関連資料の網羅的な検索（Flow/Stock配下）
- 類似成果物・先行事例の収集
- 参照すべき資料の特定

**並列処理が可能な場合:**
- 複数観点での同時評価（構造チェック、内容チェック、形式チェック等）
- 複数ファイルの同時読み込み・比較
- 独立したQC項目の並列実行

```yaml
subagent_parallel_policy:
  - 検索を伴う情報収集はSubagentに委譲する
  - 独立した評価観点は並列Subagentで同時実行可能
  - Subagentの結果を統合し、重複指摘は除去する
```

---

## 6. 変換手順（既存Skill → 1WF Skills）

### Step 1: 元SkillをWFに分解して棚卸しする
元Skillから「主成果物が1つに定まる単位」をWFとして列挙する。

各WFについて最低限これを決める：
- 主成果物（1つ）
- 使用テンプレ/固定フォーマット（assets候補）
- バックログ反映の形（Task/Epic/Story等への落とし方）
- 自動処理が必要か（scripts候補）
- チェック観点（Subagentが評価すべき観点）

禁止:
- 1WFに主成果物を複数入れる
- "計画一式" "実行全般" のように曖昧な塊でWFを切る

### Step 2: WFごとに新Skillディレクトリを作る（同梱）
WFごとに新Skillを作り、次を必ず同梱する。
- `SKILL.md`
- `assets/`（必須: WFに必要なテンプレ/規約）
- `evaluation/`（QCがあるWFは必須: 評価指標・チェック観点・採点基準）
- `scripts/`（必要なら: WFに必要な自動処理）
- `questions/`（必要なら: WF成立に必要な質問）

### Step 3: 新SkillのSKILL.mdを統一フォーマットで作る
- 見出しは `# XXX Workflow`, `## Instructions`, `## Resources`, `## Next Action` のみ
- Instructionsには必ず「Preflight→生成→Subagent QC→最小差分修正→再QC→確定→バックログ反映」を含める
- Instructionsの末尾に subagent_policy / recommended_subagents を必ず入れる
- Resourcesは同梱ファイルを相対パスで列挙する（`./assets/...` 等）

### Step 4: ai_instructions / 詳細ルールの移管（必須）

CLAUDE.mdから削除する前に、以下の手順で各Skillへ移管する。

1. **移管対象の洗い出し**: 元のai_instructionsを全項目リストアップ
2. **移管先の決定**: 各項目について以下を判断
   - コア原則として残す（全Skill共通の絶対ルール）
   - 特定Skillへ移管（そのSkill固有のルール）
   - 複数Skillへ移管（共通だが全Skillではない）
   - 不要（既に各SKILL.mdに同等の記載あり）

3. **移管の実施**: 該当Skillの以下いずれかに追記
   - SKILL.md の Instructions セクション
   - assets/ 配下のテンプレートやチェックリスト

4. **移管完了の確認**: 以下をチェック
   - [ ] 元のai_instructionsの全項目について移管先を決定した
   - [ ] 「特定Skillへ移管」の項目は該当Skillに追記済み
   - [ ] 追記後の各SKILL.mdで欠損がないことを確認した
   - [ ] CLAUDE.mdから削除しても機能が失われないことを確認した

**移管先の例（PMBOK Agent）**:
| 元のルール | 移管先 |
|------------|--------|
| トランスクリプト直書き禁止 | pmbok-meeting-minutes-workflow |
| Fact型議事録スタイル | pmbok-meeting-minutes-workflow |
| CWパック構造 | Proposal型Skill（提案書/プレゼン等） |
| 外部送付時の原則 | document-delivery-workflow |
| Mermaid記法 | プレゼン系Skill |
| バックログ作成後の実行 | pmbok-backlog-yaml-workflow |

**移管先の例（コード開発Agent）**:
| 元のルール | 移管先 |
|------------|--------|
| テスト必須（カバレッジ基準） | implementation-workflow |
| コードスタイル（Linter設定） | code-review-workflow |
| PR作成ルール | pull-request-workflow |
| ドキュメント更新ルール | documentation-workflow |
| デプロイ前チェック | deploy-workflow |

**移管先の例（リサーチAgent）**:
| 元のルール | 移管先 |
|------------|--------|
| 出典明記ルール | desk-research-workflow |
| 一次/二次情報の区別 | interview-workflow / desk-research-workflow |
| 仮説検証フレーム | hypothesis-validation-workflow |
| データ可視化ルール | analysis-report-workflow |

**移管の書き方**（SKILL.mdへの追記例）:

```markdown
## Instructions
...
2. 生成:
   - [既存の生成ルール]
   - [移管したルール1]: [具体的な内容]  ← ここに追記
   - [移管したルール2]: [具体的な内容]  ← ここに追記
   - 元資料にない項目は省略せず「未記載」または「不明」と明記する。
```

**移管時の注意点**:
- SKILL.mdのInstructionsセクション「2. 生成:」に追記するのが基本
- 語調・スタイル系のルールは「生成」ステップに追記
- チェック系のルールはassets/配下のチェックリストに追記
- 追記位置は「元資料にない項目は〜」の直前が適切

### Step 5: CLAUDE.md / AGENTS.md をスリム化する
- **Step 4の移管完了後に実施**（移管前の削除は禁止）
- 詳細手順・QCチェックリストを削除
- コア原則・ワークフロー索引・パス辞書のみに圧縮
- Agent特化の具体的な内容で記述

### Step 6: 欠損チェック（必須）
WFごとに次を確認し、満たさない場合は変換失敗とする。

- [ ] 主成果物がテンプレ準拠で生成/更新できる
- [ ] Preflightがある（未参照/不足の明示、推測禁止）
- [ ] Subagent QCループがある（最大3回、最小差分修正）
- [ ] バックログ反映がある（反映＋差分提示）
- [ ] 必要な assets/evaluation/scripts/questions が同梱されている（横参照なし）
- [ ] QCがあるWFは evaluation/ に評価指標ファイルがある
- [ ] subagent_policy / recommended_subagents が本文に含まれている

---

## 7. description 作成ルール（発火）

descriptionは必ず満たす：
- 第三人称で書く（〜を作成/更新する、〜を反映する）
- 「何をするか」＋「いつ使うか（ユーザーが言う単語）」を含める
- 主成果物が一意に想像できる
- "全般" "一式" "まとめて" のような広すぎる表現を禁止

---

## 8. 変換完了チェックリスト

### Skills
- [ ] 全Skillが1WF単位になっている（主成果物が1つ）
- [ ] 全SkillのSKILL.mdが統一フォーマット（必須見出し）になっている
- [ ] 全SkillのInstructionsに品質ループ（Subagent必須）が含まれている
- [ ] 全Skillに subagent_policy / recommended_subagents の必須ブロックが含まれている
- [ ] 全Skillがバックログ反映＋差分提示を行う
- [ ] 分解したSkillは必要な assets/evaluation/scripts/questions を同梱している（横参照なし）
- [ ] QCがあるSkillは evaluation/ に評価指標ファイルを同梱している
- [ ] path情報はCLAUDE.md/AGENTS.mdに集約され、Skillに複製されていない

### CLAUDE.md / AGENTS.md
- [ ] 100-150行以内にスリム化されている
- [ ] コア原則が5-6項目に圧縮されている
- [ ] Agent固有の成果物タイプと語調が定義されている
- [ ] 品質ゴール（3項目）が含まれている
- [ ] ワークフローが索引形式になっている（詳細手順ではない）
- [ ] 詳細手順・QCチェックリストが削除されている
- [ ] Agent特化の具体的な内容で記述されている
- [ ] パス辞書（root/dirs/patterns/meta）が完全に維持されている

### ai_instructions移管（Step 4）
- [ ] 元のai_instructionsを全項目リストアップした
- [ ] 各項目の移管先（コア原則/特定Skill/複数Skill/不要）を決定した
- [ ] 特定Skillへ移管する項目は該当SKILL.mdに追記した
- [ ] 移管後のSKILL.mdで欠損がないことを確認した
- [ ] 移管完了後にCLAUDE.mdから詳細を削除した（移管前削除は禁止）

---

## サンプル

### SKILL.md 統一フォーマット（全Skill共通の最小フォーマット）

```markdown
---
name: <wf-name>-workflow
description: "<主成果物>をテンプレートに従って作成/更新し、Subagentで品質チェックしたうえで、次アクションをバックログへ反映する。<ユーザーが言いがちなトリガー語>を依頼されたときに使用する。"
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
   - `./assets/<template>` を先に読み、章立て・必須項目・項目順序を確認する（テンプレートファースト）。
2. 生成:
   - `./questions/<questions>` を使って必要情報を収集し、テンプレ構造を崩さずに主成果物を作成/更新する。
   - 元資料にない項目は省略せず「未記載」または「不明」と明記する。
3. QC（必須）:
   - `recommended_subagents` のQC Subagentに評価・チェックを委譲する。
   - Subagentは最初に `./evaluation/<evaluation_criteria>.md` をReadし、評価指標に基づいてQCを実施する。
   - 指摘を最小差分で反映する（テンプレの章立ては崩さない）。
   - 再度SubagentでQCする。
   - これを最大3回まで繰り返し、確定する。
   - 指摘に対し「修正した/しない」と理由を成果物に残す。
4. バックログ反映:
   - 次アクション（Task/Epic/Story等）を抽出しバックログへ反映する。
   - 反映先・編集制約・差分提示は AGENTS.md / CLAUDE.md の全体ルールに従う。

subagent_policy:
  - 品質ループ（QC/チェック/フィードバック）は必ずサブエージェントへ委譲する
  - サブエージェントの指摘を反映し、反映結果（修正有無/理由）を成果物に残す

recommended_subagents:
  - <qa-subagent-name>: <チェック観点の要約>

## Resources
- questions: ./questions/<...>.md
- assets: ./assets/<...>.md
- evaluation: ./evaluation/<...>.md（QCがあるWFは必須）
- scripts: ./scripts/<...>.py（必要な場合のみ）

## Next Action
- 次に実行すべきWF（Skill）を記載する。
```

### evaluation/ ファイルのサンプル

```markdown
# <WF名> 評価指標

## 必須チェック項目

### 構造チェック（Pass/Fail）
| 項目 | 基準 | 重要度 |
|------|------|--------|
| テンプレート準拠 | 必須見出しが全て存在する | Critical |
| 必須フィールド | 〇〇/〇〇/〇〇が記載されている | Critical |
| フォーマット | 指定形式（日付形式、命名規則等）に従っている | High |

### 内容チェック（スコアリング）
| 観点 | 評価基準 | 配点 |
|------|----------|------|
| 完全性 | 元資料の情報が漏れなく反映されている | 30 |
| 正確性 | 推測・ハルシネーションがない | 30 |
| 明瞭性 | 曖昧語・主観表現がない | 20 |
| 自己完結性 | 前提・背景・出典が含まれている | 20 |

### 許容例外
- 〇〇の場合は省略可
- 〇〇が存在しない場合は「該当なし」と記載

## 採点基準
- **Pass**: 全Criticalチェック項目がPass かつ スコア80点以上
- **Conditional Pass**: 全Criticalチェック項目がPass かつ スコア60-79点（軽微な修正で確定可）
- **Fail**: CriticalチェックにFailあり または スコア60点未満（再生成が必要）

## QC報告フォーマット
```
### QC結果: [Pass/Conditional Pass/Fail]
スコア: [XX]/100

#### 指摘事項
1. [項目名]: [指摘内容] (重要度: Critical/High/Medium/Low)
2. ...

#### 修正推奨
- [具体的な修正アクション]
```
```

### CLAUDE.md スリム化サンプル

```markdown
# {Agent名}

## 1. コア原則
- Skill優先: 依頼に合致するSkillを選んで実行
- テンプレートファースト: 各Skillのassets/を先に読む
- 品質ループ: Preflight→生成→Subagent QC→反映（最大3回）※ほとんどの場合必要
- 推測禁止: 元資料にない項目は「未記載」と明記
- 自己完結: 成果物に前提/背景/出典/参照を含める

## 2. 成果物タイプと語調（Agent固有）
{各Agentのドメインに応じて定義}
例（PMBOK Agent）:
- Fact型（議事録/要件/ステータス等）: 事実のみ記載。中立・簡潔・正確。推測禁止
- Proposal型（提案書/プレゼン/見積等）: 推奨案単一選択・根拠必須。丁寧で明快に提示

例（コード開発Agent）:
- 実装コード: 既存スタイル準拠。コメントは最小限
- 設計ドキュメント: 図表優先。決定理由を明記

例（リサーチAgent）:
- 調査レポート: 出典必須。一次/二次情報を区別。仮説→検証の構造
- 分析サマリ: データ可視化優先。結論→根拠の順

例（カスタマーサポートAgent）:
- 回答テンプレート: 敬語統一。手順は番号付き。FAQ参照リンク必須
- エスカレーション報告: 事実→影響→対応案の構造

## 3. 品質ゴール
- 欠損ゼロ: 参照データの可視情報を漏れなく反映
- 行間ゼロ: 初見でも前提・背景から理解できる自己完結
- ハルシネーションゼロ: 元資料にない項目は「未記載/不明」

## 4. Skill選択ポリシー
- 依頼に最も合致するSkillを選んで実行
- 完了後、各SKILL.mdのNext Actionに従い継続判断

## 5. ワークフロー索引
{Agent固有のPhase構成}

例（PMBOK Agent）:
### Initiating
project-charter → stakeholder-analysis

### Planning
requirement-spec → wbs → schedule → backlog-yaml

### Executing
agenda → meeting-minutes → flow-backlog-yaml

### 横断
external-data-import / flow-to-stock / document-delivery

## 6. パス辞書
root: /path/to/agent
dirs:
  {Agent固有のディレクトリ構成}

meta:
  today: "YYYY-MM-DD"
```
