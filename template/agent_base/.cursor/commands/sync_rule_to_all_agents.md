# Sync Rule to All Agents

## Description
MDC/MDルールファイルを修正・新規作成・上書きした際に、デスクトップ上の全エージェントリポジトリに強制的に上書きし、その後各リポジトリでそのファイル単一のみを日本語コミットメッセージでコミットします。他のステージングファイルや変更ファイルには一切触れません。

## Instructions

このコマンドを実行したら、まずユーザーに対象ファイルのパスを尋ねてください。

### Step 1: 対象ファイルの指定
ユーザーに対象となるMDC/MDルールファイルのパスを尋ねる：
```
対象となるMDC/MDルールファイルのパスを入力してください：
例: .cursor/rules/99_rule_maintenance.mdc
```

ユーザーが入力したパスを `SOURCE_FILE` 変数に保存してください。

### Step 2: ファイルの存在確認と読み込み
対象ファイルが存在するか確認し、内容を一時ファイルに保存：
```bash
if [ ! -f "$SOURCE_FILE" ]; then
  echo "エラー: ファイルが見つかりません: $SOURCE_FILE"
  exit 1
fi

TEMP_FILE="/tmp/rule_sync_temp_$(basename "$SOURCE_FILE")"
cat "$SOURCE_FILE" > "$TEMP_FILE"
```

### Step 3: デスクトップ上の全エージェントリポジトリを検索
```bash
find /Users/matuni__/Desktop -name "$(basename "$SOURCE_FILE")" -type f ! -path "*/pptx_agent/*" | while read TARGET_FILE; do
  echo "処理中: $TARGET_FILE"
done
```

### Step 4: 全リポジトリに上書き
```bash
RULE_NAME=$(basename "$SOURCE_FILE")
TEMP_FILE="/tmp/rule_sync_temp_$RULE_NAME"
cat "$SOURCE_FILE" > "$TEMP_FILE"

find /Users/matuni__/Desktop -name "$RULE_NAME" -type f ! -path "*/pptx_agent/*" | while read TARGET_FILE; do
  echo "上書き中: $TARGET_FILE"
  cp "$TEMP_FILE" "$TARGET_FILE"
done

rm "$TEMP_FILE"
echo "上書き完了"
```

### Step 5: 各リポジトリでGit状態確認とコミット準備
```bash
RULE_NAME=$(basename "$SOURCE_FILE")

find /Users/matuni__/Desktop -name "$RULE_NAME" -type f ! -path "*/pptx_agent/*" | while read TARGET_FILE; do
  TARGET_DIR=$(dirname "$(dirname "$(dirname "$TARGET_FILE")")")
  cd "$TARGET_DIR" || continue
  
  echo "=========================================="
  echo "リポジトリ: $TARGET_DIR"
  echo "=========================================="
  
  git status --short "$TARGET_FILE"
done
```

### Step 6: ユーザーに確認
以下の情報を表示し、コミット実行の確認を取る：
- 対象ファイル名
- 上書きしたリポジトリ数
- 変更があるリポジトリのリスト
- 提案するコミットメッセージ

**確認メッセージ例:**
```
以下のリポジトリで $RULE_NAME を更新しました。

変更があるリポジトリ:
- /Users/matuni__/Desktop/babok_agent
- /Users/matuni__/Desktop/lifelog_agent
... (他 X 件)

提案するコミットメッセージ:
[update] $RULE_NAME を全エージェントに同期

このメッセージで各リポジトリにコミットしますか？ (yes/no)
```

### Step 7: コミット実行（ユーザー確認後）
ユーザーが "yes" と回答した場合のみ実行：

```bash
RULE_NAME=$(basename "$SOURCE_FILE")
COMMIT_MSG="[update] $RULE_NAME を全エージェントに同期"

find /Users/matuni__/Desktop -name "$RULE_NAME" -type f ! -path "*/pptx_agent/*" | while read TARGET_FILE; do
  TARGET_DIR=$(dirname "$(dirname "$(dirname "$TARGET_FILE")")")
  cd "$TARGET_DIR" || continue
  
  RELATIVE_PATH=$(echo "$TARGET_FILE" | sed "s|$TARGET_DIR/||")
  
  echo "コミット中: $TARGET_DIR"
  
  git add "$RELATIVE_PATH"
  git commit -m "$COMMIT_MSG" || echo "コミット失敗または変更なし: $TARGET_DIR"
done
```

### Step 8: コミット結果の確認
```bash
RULE_NAME=$(basename "$SOURCE_FILE")

find /Users/matuni__/Desktop -name "$RULE_NAME" -type f ! -path "*/pptx_agent/*" | while read TARGET_FILE; do
  TARGET_DIR=$(dirname "$(dirname "$(dirname "$TARGET_FILE")")")
  cd "$TARGET_DIR" || continue
  
  echo "=========================================="
  echo "リポジトリ: $TARGET_DIR"
  echo "最新コミット:"
  git log --oneline -1
  echo ""
done
```

## 重要な注意事項

1. **対象ファイルのみ操作**: 他のステージングファイルや変更ファイルには一切触れない
2. **単一ファイルのみコミット**: `git add` で対象ファイルのみを指定
3. **ユーザー確認必須**: コミット実行前に必ず確認を取る
4. **日本語コミットメッセージ**: コミットメッセージは日本語で記述
5. **エラーハンドリング**: 各リポジトリでエラーが発生しても処理を継続

## エラー時の対応

- **ファイルが見つからない**: そのリポジトリはスキップして継続
- **Gitリポジトリでない**: そのディレクトリはスキップして継続
- **コミット失敗**: エラーメッセージを表示して次のリポジトリへ
- **変更がない**: "変更なし" と表示してスキップ

## 実行権限

- `file_write`: ファイル上書きに必要
- `git_write`: Git操作に必要

## 使用例

```bash
# ユーザーが指定したファイルを全エージェントに同期
# 例1: 99_rule_maintenance.mdc
SOURCE_FILE=".cursor/rules/99_rule_maintenance.mdc"

# 例2: 03_pptx_template_management.mdc
SOURCE_FILE=".cursor/rules/03_pptx_template_management.mdc"

# 例3: 任意のMDC/MDファイル
SOURCE_FILE=".cursor/rules/任意のファイル名.mdc"

# 上記の手順を実行
```

