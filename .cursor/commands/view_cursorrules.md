---
description: ".cursor/rules内の全てのmdcファイルを表示"
argument-hint: "オプション（省略可）"
allowed-tools: ["Read", "LS", "Grep"]
---

# View Rules

.cursor/rules ディレクトリ内の全ての .mdc ファイルを表示します。

## 使用方法
- `/view-rules` (全ファイル表示)
- `/view-rules list` (ファイル一覧のみ)
- `/view-rules <filename>` (特定ファイルのみ)

## 実行内容

1. .cursor/rules ディレクトリの存在確認
2. .mdc ファイルの一覧取得
3. 各ファイルの内容表示

!if [ -d ".cursor/rules" ]; then
  echo "📁 .cursor/rules ディレクトリが見つかりました"
  echo ""
  
  # mdcファイルの一覧を取得
  MDC_FILES=($(ls .cursor/rules/*.mdc 2>/dev/null))
  
  if [ ${#MDC_FILES[@]} -eq 0 ]; then
    echo "❌ .mdc ファイルが見つかりません"
    exit 1
  fi
  
  echo "📋 発見された .mdc ファイル (${#MDC_FILES[@]}個):"
  for file in "${MDC_FILES[@]}"; do
    echo "  - $(basename "$file")"
  done
  echo ""
  
  # 引数の処理
  if [ -n "$ARGUMENTS" ]; then
    if [[ "$ARGUMENTS" == "list" ]]; then
      echo "✅ ファイル一覧表示完了"
      exit 0
    elif [[ "$ARGUMENTS" =~ \.mdc$ ]]; then
      TARGET_FILE=".cursor/rules/$ARGUMENTS"
      if [ -f "$TARGET_FILE" ]; then
        echo "📖 $ARGUMENTS の内容:"
        echo "════════════════════════════════════════"
        cat "$TARGET_FILE"
        echo "════════════════════════════════════════"
      else
        echo "❌ ファイル $ARGUMENTS が見つかりません"
      fi
      exit 0
    else
      # 拡張子なしでファイル名が指定された場合
      TARGET_FILE=".cursor/rules/${ARGUMENTS}.mdc"
      if [ -f "$TARGET_FILE" ]; then
        echo "📖 ${ARGUMENTS}.mdc の内容:"
        echo "════════════════════════════════════════"
        cat "$TARGET_FILE"
        echo "════════════════════════════════════════"
      else
        echo "❌ ファイル ${ARGUMENTS}.mdc が見つかりません"
      fi
      exit 0
    fi
  fi
  
  # 全ファイル表示
  echo "📖 全 .mdc ファイルの内容を表示します"
  echo ""
  
  for file in "${MDC_FILES[@]}"; do
    filename=$(basename "$file")
    echo "════════════════════════════════════════"
    echo "📄 $filename"
    echo "════════════════════════════════════════"
    cat "$file"
    echo ""
    echo ""
  done
  
  echo "✅ 全ファイル表示完了 (${#MDC_FILES[@]}個)"
  
else
  echo "❌ .cursor/rules ディレクトリが見つかりません"
  echo "カレントディレクトリ: $(pwd)"
  ls -la .cursor/ 2>/dev/null || echo ".cursor ディレクトリが存在しません"
fi