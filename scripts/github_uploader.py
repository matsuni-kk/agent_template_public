#!/usr/bin/env python3
"""
GitHub Private Repository Auto-Uploader for Agent Templates
"""

import os
import sys
import subprocess
import json
import argparse
from pathlib import Path
import shutil
from datetime import datetime

class GitHubUploader:
    def __init__(self, agent_dir: str):
        self.agent_dir = Path(agent_dir)
        self.agent_name = self.agent_dir.name
        base = self.agent_name.lower().replace('_', '-')
        # 末尾に -agent が重複しないように調整
        self.repo_name = base if base.endswith('-agent') else f"{base}-agent"
        
    def check_github_cli(self):
        """GitHub CLIがインストールされているかチェック"""
        try:
            result = subprocess.run(['gh', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ GitHub CLI検出: {result.stdout.strip().split()[2]}")
                return True
        except FileNotFoundError:
            print("❌ GitHub CLIがインストールされていません")
            print("インストール方法: https://cli.github.com/")
            return False
        return False
    
    def check_github_auth(self):
        """GitHub認証状態をチェック"""
        try:
            result = subprocess.run(['gh', 'auth', 'status'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ GitHub認証済み")
                return True
            else:
                print("❌ GitHub認証が必要です")
                print("認証コマンド: gh auth login")
                return False
        except subprocess.CalledProcessError:
            return False
    
    def create_gitignore(self):
        """エージェント用.gitignoreファイル作成"""
        gitignore_content = """# Agent Template Gitignore

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log
logs/

# Temporary files
*.tmp
*.temp

# Agent specific
Flow/Private/*
!Flow/Private/.gitkeep

# Environment variables
.env
.env.local

# Build outputs
dist/
build/
"""
        gitignore_path = self.agent_dir / '.gitignore'
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        print(f"✅ .gitignoreファイル作成: {gitignore_path}")
    
    def create_github_readme(self):
        """GitHub用READMEファイル作成"""
        readme_content = f"""# {self.agent_name} Agent

専門業務に特化したインテリジェントエージェントテンプレート

## 概要

{self.agent_name}エージェントは、業界標準に基づいた高品質な業務支援を提供するドメイン特化エージェントです。

## 特徴

- 🎯 **業界標準準拠**: 確立されたフレームワークに基づく設計
- 📊 **実務即応性**: 実際の業務で即座に使用可能
- 🔄 **ワークフロー統合**: Flow（作業中）→ Stock（確定版）の文書管理
- 🛠️ **高度なカスタマイズ**: ドメイン特化の詳細ルール

## 構造

```
{self.agent_name.lower()}_agent/
├── Flow/                      # 作業中ドラフト
│   ├── Public/               # 公開可能な作業ファイル  
│   └── Private/              # 非公開作業ファイル
├── Stock/                     # 確定版ドキュメント
├── Archived/                  # アーカイブ
├── .cursor/                   # Cursor IDE設定
│   ├── rules/                # 実行用ルール(.mdc)
│   └── templates/            # ドキュメントテンプレート
└── scripts/                   # 自動化スクリプト
```

## 使用方法

1. Cursor IDEでプロジェクトを開く
2. エージェント機能を起動
3. 業務に応じたワークフローを実行

## 開発情報

- **作成日**: {datetime.now().strftime('%Y-%m-%d')}
- **フレームワーク**: Agent Template Framework v2.0
- **対応IDE**: Cursor IDE

## プライベートリポジトリ

このエージェントは業務機密性を考慮してプライベートリポジトリとして管理されています。

## ライセンス

このプロジェクトはプライベート使用のみを想定しています。
"""
        readme_path = self.agent_dir / 'README.md'
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print(f"✅ GitHub用READMEファイル作成: {readme_path}")
    
    def init_git_repo(self):
        """Gitリポジトリ初期化"""
        os.chdir(self.agent_dir)
        
        # Git初期化
        subprocess.run(['git', 'init'], check=True)
        print("✅ Gitリポジトリ初期化")
        
        # ファイル追加
        subprocess.run(['git', 'add', '.'], check=True)
        print("✅ ファイル追加")
        
        # 初回コミット
        commit_message = f"Initial commit: {self.agent_name} Agent setup"
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        print(f"✅ 初回コミット: {commit_message}")
    
    def create_github_repo(self):
        """GitHubプライベートリポジトリ作成"""
        description = f"{self.agent_name} specialized intelligent agent template"
        
        try:
            # プライベートリポジトリ作成
            cmd = [
                'gh', 'repo', 'create', self.repo_name,
                '--private',
                '--description', description,
                '--clone=false'
            ]
            subprocess.run(cmd, check=True)
            print(f"✅ GitHubプライベートリポジトリ作成: {self.repo_name}")
            
            # リモート追加（HTTPS。ghの資格情報ヘルパを使用）
            repo_url = f"https://github.com/{self._get_github_user()}/{self.repo_name}.git"
            # 既にoriginがあるケースを考慮
            subprocess.run(['git', 'remote', 'remove', 'origin'], check=False)
            subprocess.run(['git', 'remote', 'add', 'origin', repo_url], check=True)
            print(f"✅ リモートリポジトリ追加: {repo_url}")
            
            # プッシュ
            subprocess.run(['git', 'branch', '-M', 'main'], check=True)
            subprocess.run(['git', 'push', '-u', 'origin', 'main'], check=True)
            print(f"✅ コード プッシュ完了")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ GitHubリポジトリ作成エラー: {e}")
            return False
    
    def _get_github_user(self):
        """現在のGitHubユーザー名取得"""
        try:
            result = subprocess.run(['gh', 'api', 'user'], capture_output=True, text=True)
            user_data = json.loads(result.stdout)
            return user_data['login']
        except:
            return "user"
    
    def upload_agent(self):
        """エージェント全体をGitHubにアップロード"""
        print(f"🚀 {self.agent_name} エージェントのGitHubアップロード開始")
        
        # 前提条件チェック
        if not self.check_github_cli():
            return False
        
        if not self.check_github_auth():
            return False
        
        if not self.agent_dir.exists():
            print(f"❌ エージェントディレクトリが見つかりません: {self.agent_dir}")
            return False
        
        try:
            # 必要ファイル作成
            self.create_gitignore()
            self.create_github_readme()
            
            # Git初期化・コミット
            self.init_git_repo()
            
            # GitHubリポジトリ作成・プッシュ
            if self.create_github_repo():
                print(f"🎉 {self.agent_name} エージェントのGitHubアップロード完了!")
                print(f"🔗 リポジトリURL: https://github.com/{self._get_github_user()}/{self.repo_name}")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ アップロードエラー: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Agent GitHub Uploader')
    parser.add_argument('agent_path', help='エージェントディレクトリのパス')
    
    args = parser.parse_args()
    
    uploader = GitHubUploader(args.agent_path)
    success = uploader.upload_agent()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
