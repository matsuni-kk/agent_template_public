# .gitignore テンプレート

以下の内容で .gitignore を作成する:

```gitignore
# Environment variables
.env
.env.local
.env.*.local

# Credentials
credentials.json
*.pem
*.key

# Logs
*.log
logs/

# OS files
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# Node.js (if applicable)
node_modules/
npm-debug.log

# Python (if applicable)
__pycache__/
*.pyc
.pytest_cache/
venv/
.venv/

# Deno (if applicable)
deno.lock

# Build outputs
dist/
build/
*.min.js

# Temporary files
tmp/
temp/
*.tmp

# Flow directory (work in progress)
Flow/
```

## 注意事項
- プロジェクト固有の除外対象があれば追加する
- Stock/ と Archived/ は通常含める（履歴管理のため）
- .claude/ は含める（Skills定義のため）
