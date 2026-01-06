# Update Agent Master

## Description
Skills/Commands/Agents を **必ず Claude 起点**（`.claude/`）で他環境へ同期する。

## Execution Command

```bash
python3 scripts/update_agent_master.py --source claude --force
```

## What It Does

1. **Claude起点同期**: `.claude/{skills,commands,agents}` を `.cursor/.codex/.github/.opencode` へ同期
2. **Master File Update**: `AGENTS.md`/`CLAUDE.md` 等のマスターファイルを更新
3. **Force Mode**: 確認なしで上書き実行

## Notes

- このプロジェクトでは起点の自動検出は使わず、常に `--source claude` を指定する
- 破壊的変更が含まれうるため、必要に応じて `--dry-run` で事前確認する









