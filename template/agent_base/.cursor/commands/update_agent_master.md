# Update Agent Master

## Description
Updates agent master files by converting `.mdc` rules to `.md` agents and generating command files. Executes with `--force` flag to overwrite existing files.

## Execution Command

```bash
python3 scripts/update_agent_master.py --source claude --force
```

## What It Does

1. **Rule Conversion**: Converts `.cursor/rules/*.mdc` files to `.claude/agents/*.md` format
2. **Command Generation**: Generates `.cursor/commands/agents_commands/*.md` files (without frontmatter)
3. **Master File Update**: Updates master files (`AGENTS.md`, `CLAUDE.md`, etc.)
4. **Force Mode**: Overwrites existing files without prompting

## Output Locations

- **Agents**: `.claude/agents/*.md`
- **Commands**: `.cursor/commands/agents_commands/*.md`
- **Master Files**: `.claude/AGENTS.md`, `.claude/CLAUDE.md`, etc.

## Execution Mode

- **Origin**: Claude (`--source claude`)
- **Force**: Enabled (overwrites existing files)

## Notes

- This command runs from the project root directory
- Non-master files (not containing "00" or "path" in filename) are copied to `agents_commands`
- Master files are excluded from `agents_commands` directory
- Frontmatter is removed when copying to `agents_commands`

