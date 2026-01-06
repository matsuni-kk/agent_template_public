# クリーンアップ対象一覧

## 削除対象ディレクトリ

### 1. output/{agent_name}/

デプロイ完了後のエージェントディレクトリ。

**削除条件:**
- GitHubリポジトリが作成済み
- リポジトリにpush済み
- ユーザー確認済み

**含まれる内容:**
```
output/{agent_name}/
├── .claude/
├── .codex/
├── .cursor/
├── .github/
├── .gemini/
├── .kiro/
├── Flow/
├── Stock/
├── Archived/
├── scripts/
├── CLAUDE.md
├── AGENTS.md
├── README.md
└── ...
```

### 2. Flow/{year_month}/{date}/{agent_name}/

エージェント作成中の作業ファイル。

**削除条件:**
- 作業が完了している
- 必要な成果物がStock/に移動済み
- ユーザー確認済み

**含まれる内容:**
```
Flow/{year_month}/{date}/{agent_name}/
├── draft_requirements.md
├── framework_research.md
├── {date}_agent_creation_tasklist.md
└── ...
```

## 削除しないもの

以下は削除対象外:

| 対象 | 理由 |
|------|------|
| `output/` ディレクトリ自体 | 他のエージェントが存在する可能性 |
| `Flow/` ディレクトリ自体 | 他の作業ファイルが存在する可能性 |
| `Stock/` 配下 | 確定済み成果物 |
| `Archived/` 配下 | 履歴保存 |
| テンプレート側のファイル | 再利用するため |

## 削除コマンド例

```bash
# 特定エージェントのoutput削除
rm -rf output/slack_sdk_agent/

# 特定日付のFlow削除
rm -rf Flow/202501/2025-01-04/slack_sdk_agent/

# 空ディレクトリの掃除
find Flow/ -type d -empty -delete 2>/dev/null
find output/ -type d -empty -delete 2>/dev/null
```
