# Agent Deploy Command

完成したエージェントをプライベートGitHubリポジトリにアップロードし、指定場所にクローンするコマンド

## 使用方法

```
/agent_deploy
```

## 実行内容

1. 現在のエージェントディレクトリでgit初期化
2. 全ファイルをコミット
3. プライベートGitHubリポジトリ作成・プッシュ
4. 指定場所（Desktop）にクローン

## 処理フロー

### Step 1: Git初期化とコミット
```bash
cd [current_agent_directory]
git init
git add .
git commit -m "エージェント完成版 - [agent_name]"
```

### Step 2: GitHubリポジトリ作成・プッシュ
```bash
gh repo create [agent-name] --private --source=. --remote=origin --push
```

### Step 3: Desktopにクローン
```bash
cd /Users/matuni__/Desktop
git clone [repository_url]
```

## 前提条件

- GitHub CLIがインストール・認証済み
- 現在のディレクトリがエージェントルートディレクトリ
- エージェントファイルが完成している

## 出力

- GitHubリポジトリURL
- ローカルクローン場所パス
- 実行完了確認