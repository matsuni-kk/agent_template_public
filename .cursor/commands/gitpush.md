---
description: "ステージングした変更をコメント付きでgitにプッシュ"
argument-hint: "コミットメッセージ（省略時は自動生成）"
allowed-tools: ["Bash"]
---

# Git Push with Comment

ステージングされた変更をコメント付きでコミット・プッシュします。

## 使用方法
- `/gitpush "コミットメッセージ"`
- `/gitpush` (メッセージ自動生成)

## 実行内容

1. git statusで現在の状態を確認
2. git diffで変更内容を確認  
3. コミットメッセージを設定（引数があれば使用、なければ自動生成）
4. git addで変更をステージング
5. git commitでコミット作成
6. git pushでリモートにプッシュ

!git status

!git diff --staged

!if [ -n "$ARGUMENTS" ]; then
  COMMIT_MSG="$ARGUMENTS"
else
  COMMIT_MSG="Auto-generated commit $(date '+%Y-%m-%d %H:%M:%S')"
fi

!git add .

!git commit -m "$(cat <<'EOF'
$COMMIT_MSG

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

!git push