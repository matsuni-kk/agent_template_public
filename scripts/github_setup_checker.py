#!/usr/bin/env python3
"""
GitHub CLI Setup Checker for Agent Templates
GitHub CLIの認証・設定状態をチェックし、セットアップを支援
"""

import subprocess
import sys
import json
from pathlib import Path

class GitHubSetupChecker:
    def __init__(self):
        self.checks = []
        
    def run_command(self, cmd, capture_output=True):
        """コマンド実行"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True)
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            return False, "", str(e)
    
    def check_github_cli_installed(self):
        """GitHub CLIインストール確認"""
        print("1. GitHub CLIインストール確認")
        print("-" * 40)
        
        success, stdout, stderr = self.run_command("gh --version")
        
        if success:
            version = stdout.split('\n')[0]
            print(f"✅ GitHub CLI検出: {version}")
            return True
        else:
            print("❌ GitHub CLIがインストールされていません")
            print("\n📋 インストール方法:")
            print("  macOS (Homebrew): brew install gh")  
            print("  Windows (Chocolatey): choco install gh")
            print("  Linux (apt): sudo apt install gh")
            print("  または公式サイト: https://cli.github.com/")
            return False
    
    def check_github_auth(self):
        """GitHub認証状態確認"""
        print("\n2. GitHub認証状態確認")
        print("-" * 40)
        
        success, stdout, stderr = self.run_command("gh auth status")
        
        if success:
            print("✅ GitHub認証済み")
            print(f"詳細: {stdout}")
            return True
        else:
            print("❌ GitHub認証が必要です")
            print(f"エラー: {stderr}")
            print("\n📋 認証方法:")
            print("  1. コマンド実行: gh auth login")
            print("  2. 認証方法選択 (推奨: GitHub.com)")
            print("  3. プロトコル選択 (推奨: HTTPS)")
            print("  4. ブラウザで認証完了")
            return False
    
    def check_github_user_info(self):
        """GitHubユーザー情報確認"""
        print("\n3. GitHubユーザー情報確認")
        print("-" * 40)
        
        success, stdout, stderr = self.run_command("gh api user")
        
        if success:
            try:
                user_data = json.loads(stdout)
                print(f"✅ ユーザー: {user_data.get('login', 'Unknown')}")
                print(f"   名前: {user_data.get('name', 'Not set')}")
                print(f"   アカウント種別: {user_data.get('type', 'Unknown')}")
                if user_data.get('plan'):
                    print(f"   プラン: {user_data['plan'].get('name', 'Unknown')}")
                return True, user_data.get('login', 'user')
            except json.JSONDecodeError:
                print("⚠️  ユーザー情報の解析に失敗しました")
                return True, "user"
        else:
            print("❌ ユーザー情報取得に失敗しました")
            print(f"エラー: {stderr}")
            return False, None
    
    def check_git_config(self):
        """Gitローカル設定確認"""
        print("\n4. Gitローカル設定確認")
        print("-" * 40)
        
        # ユーザー名確認
        success_name, name, _ = self.run_command("git config user.name")
        success_email, email, _ = self.run_command("git config user.email")
        
        if success_name and success_email:
            print(f"✅ Git設定完了")
            print(f"   ユーザー名: {name}")
            print(f"   メールアドレス: {email}")
            return True
        else:
            print("⚠️  Git設定が不完全です")
            if not success_name:
                print("   ユーザー名が未設定")
            if not success_email:
                print("   メールアドレスが未設定")
            
            print("\n📋 設定方法:")
            print('  git config --global user.name "Your Name"')
            print('  git config --global user.email "your.email@example.com"')
            return False
    
    def check_repo_creation_permission(self, username):
        """リポジトリ作成権限確認"""
        print("\n5. リポジトリ作成権限確認")
        print("-" * 40)
        
        # 現在のスコープ確認
        success, stdout, stderr = self.run_command("gh auth status --show-token")
        
        if success and "repo" in stdout:
            print("✅ リポジトリ作成権限あり")
            return True
        else:
            print("⚠️  リポジトリ作成権限が不明または不足")
            print("\n📋 権限追加方法:")
            print("  1. gh auth refresh -s repo")
            print("  2. または再認証: gh auth logout && gh auth login")
            return False
    
    def run_setup_guide(self):
        """対話型セットアップガイド"""
        print("\n🛠️  GitHub CLIセットアップガイド")
        print("=" * 50)
        
        # GitHub CLIインストール確認
        if not self.check_github_cli_installed():
            print("\n❌ GitHub CLIをインストールしてから再実行してください")
            return False
        
        # GitHub認証確認
        if not self.check_github_auth():
            response = input("\nGitHub認証を今すぐ実行しますか？ (y/N): ")
            if response.lower() == 'y':
                print("\n🔐 GitHub認証を開始します...")
                success, _, _ = self.run_command("gh auth login", capture_output=False)
                if not success:
                    print("❌ 認証に失敗しました")
                    return False
            else:
                print("❌ 認証が必要です。手動で実行してください: gh auth login")
                return False
        
        # ユーザー情報確認
        success, username = self.check_github_user_info()
        if not success:
            return False
        
        # Git設定確認
        if not self.check_git_config():
            response = input("\nGit設定を今すぐ設定しますか？ (y/N): ")
            if response.lower() == 'y':
                name = input("ユーザー名を入力してください: ")
                email = input("メールアドレスを入力してください: ")
                
                self.run_command(f'git config --global user.name "{name}"')
                self.run_command(f'git config --global user.email "{email}"')
                print("✅ Git設定完了")
        
        # リポジトリ作成権限確認
        self.check_repo_creation_permission(username)
        
        print("\n🎉 GitHub CLIセットアップチェック完了！")
        print("\n📋 今後の使用方法:")
        print("  エージェント完成時: 「エージェント完成」または「GitHub上げ」と発言")
        print("  手動アップロード: python scripts/github_uploader.py path/to/agent/")
        
        return True
    
    def run_quick_check(self):
        """クイックチェック（問題があれば詳細ガイドを促す）"""
        print("🔍 GitHub CLI クイックチェック")
        print("=" * 40)
        
        checks = [
            ("GitHub CLI", self.check_github_cli_installed()),
            ("GitHub認証", self.check_github_auth()),
            ("ユーザー情報", self.check_github_user_info()[0]), 
            ("Git設定", self.check_git_config())
        ]
        
        all_passed = all(result for _, result in checks)
        
        if all_passed:
            print("\n✅ 全チェック完了！GitHub自動アップロード準備完了")
            return True
        else:
            print("\n⚠️  いくつかの問題が見つかりました")
            response = input("詳細セットアップガイドを実行しますか？ (y/N): ")
            if response.lower() == 'y':
                return self.run_setup_guide()
            else:
                print("手動で問題を解決してから再実行してください")
                return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description='GitHub CLI Setup Checker')
    parser.add_argument('--setup', action='store_true', help='対話型セットアップガイドを実行')
    
    args = parser.parse_args()
    
    checker = GitHubSetupChecker()
    
    if args.setup:
        success = checker.run_setup_guide()
    else:
        success = checker.run_quick_check()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()