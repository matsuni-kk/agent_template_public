# CLAUDE.md テンプレート

生成エージェント用のスリム版CLAUDE.mdテンプレート。100行以内を目標とする。

```markdown
# {AgentName} Agent

{domain}領域の業務支援エージェント。{description}

## 1. 基本原則

- 事実優先: データ・出典・日時を明示
- 推測禁止: 元資料にない項目は「未記載」と明記
- 自己完結: 成果物に前提/背景/出典/参照を含める
- 承認優先: フォルダ構成・要件は承認を得てから進む
- テンプレートファースト: 各Skillの `assets/` を先に読む
- WF自動継続: Skill完了後は各Skillの `triggers/next_action_triggers.md` に従い、条件を満たす次Skillを自動実行する
- Next Action 形式: 各SKILL.mdの `## Next Action` は手動箇条書き禁止、`- triggers: ./triggers/next_action_triggers.md` の参照のみ許可
- triggers必須: 新規Skillには `triggers/next_action_triggers.md` を必ず作成し、起動条件は検証可能な形式で書く（曖昧表現NG）

## 2. 成果物タイプ

- ドラフト（Flow）: 作業中成果物。日次階層で管理
- 確定版（Stock）: 承認済み成果物。programs/配下で管理
- Skills/Agents/Commands: .claude/配下で管理

## 3. 品質ゴール

- 欠損ゼロ: 参照データの可視情報を漏れなく反映
- 行間ゼロ: 初見でも前提・背景から理解できる自己完結
- ハルシネーションゼロ: 元資料にない項目は「未記載/不明」

## 4. Skill選択ポリシー

- 依頼に最も合致するSkillを選んで実行
- 完了後、各SKILL.mdのNext Actionに従い継続判断
- 詳細手順は各Skillのassetsを参照

## 5. ワークフロー索引

### 主要Skills
{skills_index}

### スクリプト
- `scripts/validate_skills.py`: Skills/Agents/Commands検証
- `scripts/update_agent_master.py`: マルチプラットフォーム同期

## 6. パス辞書

```yaml
root: "./"

dirs:
  flow: "Flow"
  stock: "Stock"
  archived: "Archived"
  claude_skills: ".claude/skills"
  claude_agents: ".claude/agents"
  claude_commands: ".claude/commands"
  codex_skills: ".codex/skills"
  codex_agents: ".codex/agents"
  codex_prompts: ".codex/prompts"

patterns:
  flow_day_dir: "Flow/{{meta.year_month}}/{{meta.today}}"
  draft_document: "{{flow_day_dir}}/draft_{{document_name}}.md"
  stock_documents_dir: "Stock/programs/{{project}}/documents/{{document_genre}}"
  stock_images_dir: "Stock/programs/{{project}}/images/{{image_category}}"

meta:
  today: "YYYY-MM-DD"
  year_month: "YYYYMM"
  timestamp: "YYYY-MM-DD HH:mm"
```

## 7. エージェント構造

```
{domain}_agent/
├── .claude/
│   ├── skills/          # Skills（1WF=1Skill）
│   ├── agents/          # Sub Agents（QC用等）
│   └── commands/        # スラッシュコマンド
├── .codex/
│   ├── skills/
│   ├── agents/
│   └── prompts/
├── Flow/                # 作業中ドラフト
├── Stock/               # 確定版
│   └── programs/{project}/
├── Archived/            # 履歴
├── scripts/
└── README.md
```

## 8. 準拠フレームワーク

{framework_info}

---
Do what has been asked; nothing more, nothing less.
```

## プレースホルダ一覧

| プレースホルダ | 説明 | 例 |
|---------------|------|-----|
| {AgentName} | エージェント表示名 | Accounting Agent |
| {domain} | ドメイン名（スネークケース） | accounting |
| {description} | エージェント説明（1-2文） | 財務取引記録と報告を支援 |
| {skills_index} | Skills一覧（生成後に追記） | - accounting-create-journal |
| {framework_info} | 準拠フレームワーク情報 | GAAP/IFRS準拠 |

## 使用方法

1. テンプレートをコピー
2. プレースホルダを置換
3. `output/{domain}_agent/CLAUDE.md` として保存
4. Skills生成後に `{skills_index}` を更新
