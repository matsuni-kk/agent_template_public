---
name: post-deploy-cleanup
description: "デプロイ完了後に不要になったoutput/やFlow/の一時ファイルを削除する。「クリーンアップ」「デプロイ後削除」「output削除」を依頼されたときに使用する。"
---

# Post Deploy Cleanup Workflow

デプロイ完了後に不要になった一時ファイル・ディレクトリを削除する。主成果物はクリーンな作業環境。

## Instructions

### 1. Preflight（事前確認）
- `./assets/cleanup_checklist.md` を先に読み、削除対象を確認する。
- デプロイが完了していることを確認する:
  - GitHubリポジトリが作成されている
  - リポジトリURLが記録されている
- **削除前に必ずユーザー確認を取る**

### 2. 削除対象の特定

以下のディレクトリ・ファイルが削除対象:

| 対象 | 理由 | 確認事項 |
|------|------|----------|
| `output/{agent_name}/` | デプロイ済み | GitHubリポジトリに存在 |
| `Flow/{year_month}/{date}/{agent_name}/` | 作業完了 | 成果物がStockに移動済み |

### 3. 削除前確認

以下を確認してから削除を実行する:

```bash
# デプロイ済みリポジトリの確認
gh repo view {owner}/{agent_name} --json url

# output内のファイル確認
ls -la output/{agent_name}/

# Flow内の関連ファイル確認
ls -la Flow/{year_month}/{date}/{agent_name}/ 2>/dev/null || echo "Flow directory not found"
```

### 4. 削除実行

ユーザー確認後、以下を実行:

```bash
# outputディレクトリ削除
rm -rf output/{agent_name}/

# Flowディレクトリ削除（存在する場合）
rm -rf Flow/{year_month}/{date}/{agent_name}/

# 空のFlowディレクトリを削除
find Flow/ -type d -empty -delete 2>/dev/null || true
```

### 5. 確認

削除完了を確認:
- `output/` に対象ディレクトリが存在しないこと
- `Flow/` に関連ファイルが存在しないこと

### 6. QC（必須）
- `./evaluation/cleanup_criteria.md` を参照し、以下を確認する:
  - ユーザー許可が取得されている
  - 削除対象が指定どおり
  - 想定外の削除が発生していない

### 7. バックログ反映
- 削除完了をタスクリストに記録する。
- cleanup_done=true を記録する。

subagent_policy:
  - このSkillはサブエージェント委譲不要（単純な削除操作のため）

recommended_subagents:
  - なし（evaluation/*.mdで十分）

## Resources
- assets: ./assets/cleanup_checklist.md
- assets: ./assets/cleanup_targets.md
- evaluation: ./evaluation/cleanup_criteria.md
- triggers: ./triggers/next_action_triggers.md

## Next Action
- triggers: ./triggers/next_action_triggers.md

起動条件に従い、条件を満たすSkillを自動実行する。
