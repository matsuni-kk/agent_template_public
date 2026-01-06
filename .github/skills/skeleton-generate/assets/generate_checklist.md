# スケルトン生成チェックリスト

## 生成前の必須確認
- [ ] ドメイン名が確定（スネークケース）
- [ ] エージェント表示名が確定
- [ ] 説明文（1-2文）が用意されている
- [ ] draft_requirements.md が存在する
- [ ] framework_research.md が存在する
- [ ] framework_research_done=true が記録されている
- [ ] **要件定義がユーザー承認済み**
- [ ] output/配下に同名フォルダが存在しない
- [ ] **ディレクトリパターンが確定**（Business/Coding/Data/DevOps/MultiApp/Minimal）

## 生成方法
skeleton-generate Skillを実行し、以下を指定:
- エージェント名（表示名）
- ドメイン名（スネークケース）
- 説明文（1-2文）
- ディレクトリパターン

## 生成後の必須作業
- [ ] CLAUDE.md の内容を確認（テンプレートファースト/WF自動継続/Next Action triggers参照ルールを含む）
- [ ] ディレクトリ構造を確認
- [ ] validate_skills.py で検証

## 生成されるファイル構造
```
output/{domain}_agent/
├── .claude/
│   ├── skills/           # Skills群
│   ├── agents/           # サブエージェント
│   └── commands/         # スラッシュコマンド
├── .codex/
│   ├── skills/
│   ├── agents/
│   └── prompts/
├── .cursor/
│   └── skills/
├── .github/
│   └── skills/
├── .gemini/
├── .kiro/
├── Flow/                 # 作業中（日次管理）※パターンによる
├── Stock/                # 確定版 ※パターンによる
├── Archived/             # 履歴 ※パターンによる
├── scripts/
│   ├── validate_skills.py
│   └── update_agent_master.py
├── CLAUDE.md
├── AGENTS.md
└── README.md
```

## Skills整備計画
生成後、以下の順でSkillsを整備する:
1. {domain}-initialize - プロジェクト初期化
2. ドメイン固有Skills - domain-skills-generate で生成
3. CLAUDE.md - ワークフロー索引更新
4. validate_skills.py - 構文検証実行
