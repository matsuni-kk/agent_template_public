# Skills版ディレクトリ構造テンプレート

## 生成するディレクトリ構造

```
output/{domain}_agent/
├── CLAUDE.md                    # エージェントマスター（スリム版）
├── AGENTS.md                    # Claude Code用（CLAUDE.mdと同内容）
├── README.md                    # リポジトリ説明
│
├── .claude/
│   ├── skills/                  # Skills格納
│   │   └── .gitkeep
│   ├── agents/                  # Sub Agents格納
│   │   └── .gitkeep
│   └── commands/                # スラッシュコマンド格納
│       └── .gitkeep
│
├── .codex/
│   ├── skills/                  # Skills（.claudeと同期）
│   │   └── .gitkeep
│   ├── agents/                  # Sub Agents（.claudeと同期）
│   │   └── .gitkeep
│   └── prompts/                 # スラッシュコマンド（commandsと同期）
│       └── .gitkeep
│
├── .cursor/
│   └── rules/                   # Cursor用（互換性のため残す）
│       └── .gitkeep
│
├── .github/
│   ├── skills/                  # GitHub Copilot用
│   │   └── .gitkeep
│   ├── prompts/
│   │   └── .gitkeep
│   └── copilot-instructions.md
│
├── .gemini/
│   └── GEMINI.md
│
├── .kiro/
│   └── steering/
│       └── KIRO.md
│
├── Flow/                        # 作業中ドラフト
│   └── .gitkeep
│
├── Stock/                       # 確定版
│   └── programs/
│       └── {project}/
│           ├── documents/
│           │   └── .gitkeep
│           └── images/
│               └── .gitkeep
│
├── Archived/                    # 履歴
│   └── .gitkeep
│
└── scripts/
    ├── validate_skills.py       # バリデーションスクリプト
    └── update_agent_master.py   # マスター同期スクリプト
```

## 必須ファイル一覧

| ファイル | 役割 | テンプレート |
|---------|------|-------------|
| CLAUDE.md | マスター指示 | claude_md_template.md |
| AGENTS.md | Claude Code用 | CLAUDE.mdと同内容 |
| README.md | リポジトリ説明 | readme_template.md |
| .github/copilot-instructions.md | Copilot用 | CLAUDE.mdと同内容 |
| .gemini/GEMINI.md | Gemini用 | CLAUDE.mdと同内容 |
| .kiro/steering/KIRO.md | Kiro用 | CLAUDE.mdと同内容 |

## 生成手順

### Step 1: ディレクトリ作成
```bash
mkdir -p output/{domain}_agent/.claude/{skills,agents,commands}
mkdir -p output/{domain}_agent/.codex/{skills,agents,prompts}
mkdir -p output/{domain}_agent/.cursor/rules
mkdir -p output/{domain}_agent/.github/{skills,prompts}
mkdir -p output/{domain}_agent/.gemini
mkdir -p output/{domain}_agent/.kiro/steering
mkdir -p output/{domain}_agent/Flow
mkdir -p output/{domain}_agent/Stock/programs/{project}/{documents,images}
mkdir -p output/{domain}_agent/Archived
mkdir -p output/{domain}_agent/scripts
```

### Step 2: .gitkeep配置
```bash
find output/{domain}_agent -type d -empty -exec touch {}/.gitkeep \;
```

### Step 3: マスターファイル生成
1. `claude_md_template.md` を使用して `CLAUDE.md` を生成
2. 同内容を `AGENTS.md`, `.github/copilot-instructions.md`, `.gemini/GEMINI.md`, `.kiro/steering/KIRO.md` にコピー

### Step 4: スクリプトコピー
```bash
cp scripts/validate_skills.py output/{domain}_agent/scripts/
cp scripts/update_agent_master.py output/{domain}_agent/scripts/
```

### Step 5: README生成
`readme_template.md` を使用して `README.md` を生成

## Skills版の特徴

| 項目 | 説明 |
|------|------|
| 設定場所 | .codex/skills/*/SKILL.md |
| マスター | CLAUDE.md（スリム版） |
| パス定義 | CLAUDE.md内のパス辞書 |
| 同期方式 | update_agent_master.py |
| 検証 | validate_skills.py |
