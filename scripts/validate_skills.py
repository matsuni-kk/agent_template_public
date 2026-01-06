#!/usr/bin/env python3
"""
Skills Validation Script
Skills版エージェントの構造・フロントマター・必須セクションを検証する
"""

import os
import sys
import re
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def find_project_root() -> Path:
    """プロジェクトルートを特定"""
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / "CLAUDE.md").exists() or (parent / ".claude").exists():
            return parent
    return current


def parse_frontmatter(content: str) -> Tuple[Optional[Dict], str]:
    """フロントマターをパース"""
    if not content.startswith("---"):
        return None, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, content

    try:
        frontmatter = yaml.safe_load(parts[1])
        body = parts[2]
        return frontmatter, body
    except yaml.YAMLError as e:
        return {"_error": str(e)}, content


def validate_skill(skill_path: Path) -> List[str]:
    """単一Skillを検証"""
    errors = []
    skill_name = skill_path.name
    skill_md = skill_path / "SKILL.md"

    # SKILL.md存在チェック
    if not skill_md.exists():
        errors.append(f"[Critical] SKILL.md が存在しない: {skill_name}")
        return errors

    content = skill_md.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(content)

    # フロントマターチェック
    if frontmatter is None:
        errors.append(f"[Critical] フロントマターがない: {skill_name}/SKILL.md")
    elif "_error" in frontmatter:
        errors.append(f"[Critical] YAML構文エラー: {skill_name}/SKILL.md - {frontmatter['_error']}")
    else:
        # 必須フィールドチェック
        if "name" not in frontmatter:
            errors.append(f"[Critical] name フィールドがない: {skill_name}/SKILL.md")
        if "description" not in frontmatter:
            errors.append(f"[Critical] description フィールドがない: {skill_name}/SKILL.md")

    # 必須セクションチェック
    required_sections = [
        ("## Instructions", "Instructions セクション"),
        ("## Resources", "Resources セクション"),
        ("## Next Action", "Next Action セクション"),
    ]

    for section, label in required_sections:
        if section not in body:
            errors.append(f"[High] {label}がない: {skill_name}/SKILL.md")

    # Instructions内の必須サブセクション
    if "## Instructions" in body:
        instructions_checks = [
            ("Preflight", "Preflight（事前確認）"),
            ("QC", "QC（必須）"),
        ]
        for keyword, label in instructions_checks:
            if keyword not in body:
                errors.append(f"[Medium] {label}がない: {skill_name}/SKILL.md")

    # subagent_policy チェック
    if "subagent_policy:" not in body:
        errors.append(f"[Medium] subagent_policy ブロックがない: {skill_name}/SKILL.md")

    # recommended_subagents チェック
    if "recommended_subagents:" not in body:
        errors.append(f"[Medium] recommended_subagents ブロックがない: {skill_name}/SKILL.md")

    # assets/ フォルダチェック
    assets_dir = skill_path / "assets"
    if not assets_dir.exists():
        errors.append(f"[High] assets/ フォルダがない: {skill_name}")
    elif not any(assets_dir.iterdir()):
        errors.append(f"[Medium] assets/ が空: {skill_name}")

    # evaluation/ フォルダチェック（QC対象Skillの場合）
    if "recommended_subagents:" in body and "qa-" in body:
        eval_dir = skill_path / "evaluation"
        if not eval_dir.exists():
            errors.append(f"[High] evaluation/ フォルダがない（QC対象Skill）: {skill_name}")

    return errors


def validate_agent(agent_path: Path) -> List[str]:
    """単一Agentを検証"""
    errors = []
    agent_name = agent_path.stem

    content = agent_path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(content)

    # フロントマターチェック
    if frontmatter is None:
        errors.append(f"[Critical] フロントマターがない: agents/{agent_name}.md")
    elif "_error" in frontmatter:
        errors.append(f"[Critical] YAML構文エラー: agents/{agent_name}.md - {frontmatter['_error']}")
    else:
        if "name" not in frontmatter:
            errors.append(f"[Critical] name フィールドがない: agents/{agent_name}.md")
        if "description" not in frontmatter:
            errors.append(f"[Critical] description フィールドがない: agents/{agent_name}.md")

    return errors


def validate_command(cmd_path: Path) -> List[str]:
    """単一Commandを検証"""
    errors = []
    cmd_name = cmd_path.stem

    content = cmd_path.read_text(encoding="utf-8")

    # 基本的な構造チェック（フロントマターは任意）
    if len(content.strip()) < 10:
        errors.append(f"[Medium] 内容が少なすぎる: commands/{cmd_name}.md")

    return errors


def main():
    """メイン処理"""
    root = find_project_root()
    print(f"📂 プロジェクトルート: {root}")
    print()

    all_errors = []
    stats = {"skills": 0, "agents": 0, "commands": 0}

    # .claude/skills/ 検証
    skills_dir = root / ".claude" / "skills"
    if skills_dir.exists():
        print("🔍 Skills検証中...")
        for skill_path in sorted(skills_dir.iterdir()):
            if skill_path.is_dir() and not skill_path.name.startswith("."):
                stats["skills"] += 1
                errors = validate_skill(skill_path)
                if errors:
                    all_errors.extend(errors)
                    print(f"  {RED}✗{RESET} {skill_path.name}: {len(errors)} エラー")
                else:
                    print(f"  {GREEN}✓{RESET} {skill_path.name}")
    else:
        print(f"{YELLOW}⚠ .claude/skills/ が存在しません{RESET}")

    print()

    # .claude/agents/ 検証
    agents_dir = root / ".claude" / "agents"
    if agents_dir.exists():
        print("🔍 Agents検証中...")
        for agent_path in sorted(agents_dir.glob("*.md")):
            stats["agents"] += 1
            errors = validate_agent(agent_path)
            if errors:
                all_errors.extend(errors)
                print(f"  {RED}✗{RESET} {agent_path.name}: {len(errors)} エラー")
            else:
                print(f"  {GREEN}✓{RESET} {agent_path.name}")
    else:
        print(f"{YELLOW}⚠ .claude/agents/ が存在しません{RESET}")

    print()

    # .claude/commands/ 検証
    commands_dir = root / ".claude" / "commands"
    if commands_dir.exists():
        print("🔍 Commands検証中...")
        for cmd_path in sorted(commands_dir.glob("*.md")):
            stats["commands"] += 1
            errors = validate_command(cmd_path)
            if errors:
                all_errors.extend(errors)
                print(f"  {RED}✗{RESET} {cmd_path.name}: {len(errors)} エラー")
            else:
                print(f"  {GREEN}✓{RESET} {cmd_path.name}")
    else:
        print(f"{YELLOW}⚠ .claude/commands/ が存在しません{RESET}")

    print()
    print("=" * 50)
    print(f"📊 検証結果サマリー")
    print(f"   Skills: {stats['skills']} 件")
    print(f"   Agents: {stats['agents']} 件")
    print(f"   Commands: {stats['commands']} 件")
    print()

    if all_errors:
        print(f"{RED}❌ {len(all_errors)} 件のエラー{RESET}")
        print()

        # 重要度別に分類
        critical = [e for e in all_errors if "[Critical]" in e]
        high = [e for e in all_errors if "[High]" in e]
        medium = [e for e in all_errors if "[Medium]" in e]

        if critical:
            print(f"{RED}[Critical] {len(critical)} 件{RESET}")
            for e in critical:
                print(f"  {e}")
        if high:
            print(f"{YELLOW}[High] {len(high)} 件{RESET}")
            for e in high:
                print(f"  {e}")
        if medium:
            print(f"[Medium] {len(medium)} 件")
            for e in medium:
                print(f"  {e}")

        sys.exit(1)
    else:
        print(f"{GREEN}✅ All skills passed validation.{RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()
