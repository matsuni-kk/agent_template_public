# ChromeExtension Agent

Chrome拡張機能開発支援エージェント - Manifest V3準拠

## 概要

このリポジトリは、ChromeExtensionドメインに特化したLLMエージェントシステムです。
Cursor IDEと統合して、chrome_extension関連のタスクを効率的に実行します。

## 主な機能

### ChromeExtension特化機能
- ドメイン固有のワークフロー
- 専用のドキュメントテンプレート
- 自動化されたタスク管理

## セットアップ

### 1. リポジトリのクローン
```bash
git clone <repository-url> chrome_extension_agent
cd chrome_extension_agent
```

### 2. Cursor IDEでの利用
1. Cursor IDEでこのディレクトリを開く
2. `.cursor/rules/`ディレクトリに変換済みのルールが配置されています
3. エージェントが自動的に有効になります

### 3. ルールの更新（必要に応じて）
`.cursor/rules/` 配下の`.mdc`を直接編集してください。

## 使い方

### 基本的なトリガー
- `chrome_extension初期化`: プロジェクトをセットアップ

### ディレクトリ構成
- `Flow/`: 作業中のドキュメント
- `Stock/`: 確定済みドキュメント
- `.cursor/rules/`: ルール（Cursor用）

## カスタマイズ

### ルールの追加・編集
1. `.cursor/rules/`内の`.mdc`ファイルを編集
2. Cursorを再起動

### 新しいワークフローの追加
`.cursor/rules/`に新しいルールファイルを作成し、必要なトリガーとアクションを定義してください。

## ライセンス

[ライセンス情報を追加]

## 貢献

[貢献ガイドラインを追加]
