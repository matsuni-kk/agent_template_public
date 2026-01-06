# Skeleton Generate 評価指標

## 必須チェック項目

### 構造チェック（Pass/Fail）
| 項目 | 基準 | 重要度 |
|------|------|--------|
| 出力フォルダ | output/{domain}_agent/ が存在 | Critical |
| CLAUDE.md | CLAUDE.md が存在 | Critical |
| AGENTS.md | AGENTS.md が存在 | Critical |
| .claude/skills/ | .claude/skills/ が存在 | Critical |
| .claude/agents/ | .claude/agents/ が存在 | Critical |
| .claude/commands/ | .claude/commands/ が存在 | Critical |
| .codex/skills/ | .codex/skills/ が存在 | Critical |
| .codex/agents/ | .codex/agents/ が存在 | Critical |
| .codex/prompts/ | .codex/prompts/ が存在 | Critical |
| スクリプト | scripts/validate_skills.py が存在 | High |
| 同期スクリプト | scripts/update_agent_master.py が存在 | High |

### マルチプラットフォームチェック（Pass/Fail）
| 項目 | 基準 | 重要度 |
|------|------|--------|
| Copilot | .github/copilot-instructions.md が存在 | High |
| Gemini | .gemini/GEMINI.md が存在 | High |
| Kiro | .kiro/steering/KIRO.md が存在 | High |
| Cursor | .cursor/rules/ が存在 | Medium |

### 内容チェック（スコアリング）
| 観点 | 評価基準 | 配点 |
|------|----------|------|
| CLAUDE.md内容 | ドメイン名・説明・フレームワークが反映 かつ WF自動継続/テンプレートファースト/Next Action triggers参照ルールが明記 | 30 |
| ディレクトリ構成 | Flow/Stock/Archived が存在 | 25 |
| ファイル同期 | 全マスターファイルが同内容 | 25 |
| タスクリスト記録 | 設定値がタスクリストに記録 | 20 |

### 禁止事項
- プレースホルダ（{domain}, {AgentName}等）を置換せず残す
- CLAUDE.mdを生成しない
- .claude/skills/を作成しない
- 承認なしで生成する

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

## チェックリスト

### ディレクトリ構造
- [ ] output/{domain}_agent/ 存在
- [ ] .claude/skills/ 存在
- [ ] .claude/agents/ 存在
- [ ] .claude/commands/ 存在
- [ ] .codex/skills/ 存在
- [ ] .codex/agents/ 存在
- [ ] .codex/prompts/ 存在
- [ ] .cursor/rules/ 存在
- [ ] .github/skills/ 存在
- [ ] .github/prompts/ 存在
- [ ] .gemini/ 存在
- [ ] .kiro/steering/ 存在
- [ ] Flow/ 存在
- [ ] Stock/programs/ 存在
- [ ] Archived/ 存在
- [ ] scripts/ 存在

### マスターファイル
- [ ] CLAUDE.md 存在・内容正確
- [ ] AGENTS.md 存在・CLAUDE.mdと同内容
- [ ] .github/copilot-instructions.md 存在・同内容
- [ ] .gemini/GEMINI.md 存在・同内容
- [ ] .kiro/steering/KIRO.md 存在・同内容
- [ ] README.md 存在

### スクリプト
- [ ] scripts/validate_skills.py 存在
- [ ] scripts/update_agent_master.py 存在
