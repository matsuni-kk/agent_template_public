---
doc_type: root_directory
project_id: chrome_extension
created_at: {{env.NOW:date:YYYY-MM-DD}}
version: v1.0
---

# Root Directory - ChromeExtension Agent

このファイルはChromeExtensionエージェントのルートディレクトリを示します。

## Root Directory Path
このエージェントは独立したリポジトリとして設計されています。
クローン先のディレクトリがルートディレクトリとなります。

- Mac/Linux: `~/workspace/chrome_extension_agent`
- Windows: `C:\workspace\chrome_extension_agent`

## Agent Information
- **Agent Name**: ChromeExtension
- **Domain**: chrome_extension
- **Description**: Chrome拡張機能開発支援エージェント - Manifest V3準拠

## Directory Structure
```
chrome_extension_agent/
├── Flow/           # 作業中のドキュメント
│   ├── Public/     # 公開可能な作業ドキュメント
│   └── Private/    # 非公開の作業ドキュメント
├── Stock/          # 確定済みドキュメント
├── Archived/       # アーカイブ
├── scripts/        # 自動化スクリプト
└── .cursor/        # Cursor設定
    └── rules/      # ルール（.mdc形式）
```

## Quick Start
1. このリポジトリをクローン
2. Cursorでこのディレクトリを開く
3. 必要に応じて `.cursor/rules/` を直接編集してルールを更新

## Specialized Features
### ChromeExtension特化機能
- ドメイン固有のワークフロー
- 専用のドキュメントテンプレート
- 自動化されたタスク管理
