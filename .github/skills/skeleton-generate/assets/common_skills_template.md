# 共通引き継ぎSkillsテンプレート

全エージェントに引き継ぐ共通Skillsの一覧とコピー手順。

## 引き継ぎ対象Skills

### 必須（全パターン共通）

| Skill | 用途 | コピー元 |
|-------|------|---------|
| skill-maintenance | Skill作成・編集・削除 | `.github/skills/skill-maintenance/` |
| subagent-maintenance | サブエージェント管理 | `.github/skills/subagent-maintenance/` |

### オプション（用途に応じて）

| Skill | 用途 | 対象パターン |
|-------|------|-------------|
| rule-validation | 構文検証 | 全パターン（推奨） |

## コピー手順

### Step 1: 必須Skillsコピー
```bash
# skill-maintenance
cp -r .github/skills/skill-maintenance output/{domain}_agent/.github/skills/

# subagent-maintenance
cp -r .github/skills/subagent-maintenance output/{domain}_agent/.github/skills/
```

### Step 2: スクリプトコピー
```bash
cp scripts/validate_skills.py output/{domain}_agent/scripts/
cp scripts/update_agent_master.py output/{domain}_agent/scripts/
```

### Step 3: 共通サブエージェントコピー（オプション）
```bash
# skill-builder, skill-validator
cp .claude/agents/skill-builder.md output/{domain}_agent/.claude/agents/
cp .claude/agents/skill-validator.md output/{domain}_agent/.claude/agents/
```

## skill-maintenance の調整ポイント

コピー後、以下を対象エージェントに合わせて調整:

1. **パス参照**: SKILL.md内のパスを確認
2. **評価基準**: evaluation/をドメインに合わせて調整（オプション）

## subagent-maintenance の調整ポイント

1. **テンプレート**: 必要に応じてドメイン固有テンプレートを追加
2. **評価基準**: evaluation/をドメインに合わせて調整（オプション）

## ディレクトリパターン別の追加Skills

### Business パターン
- Flow→Stock移行用Skill（オプション）

### Coding パターン
- テスト実行Skill（オプション）
- ビルドSkill（オプション）

### Data パターン
- データ検証Skill（オプション）
- レポート生成Skill（オプション）

### DevOps パターン
- デプロイSkill（オプション）
- 監視Skill（オプション）

## 自動化スクリプト例

```bash
#!/bin/bash
# copy_common_skills.sh

DOMAIN=$1
OUTPUT_DIR="output/${DOMAIN}_agent"

# 必須Skills
cp -r .github/skills/skill-maintenance "${OUTPUT_DIR}/.github/skills/"
cp -r .github/skills/subagent-maintenance "${OUTPUT_DIR}/.github/skills/"

# スクリプト
cp scripts/validate_skills.py "${OUTPUT_DIR}/scripts/"
cp scripts/update_agent_master.py "${OUTPUT_DIR}/scripts/"

# 共通サブエージェント
cp .claude/agents/skill-builder.md "${OUTPUT_DIR}/.claude/agents/"
cp .claude/agents/skill-validator.md "${OUTPUT_DIR}/.claude/agents/"

echo "✅ 共通Skills コピー完了: ${OUTPUT_DIR}"
```
