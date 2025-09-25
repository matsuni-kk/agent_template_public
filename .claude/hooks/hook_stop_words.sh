#!/bin/bash

# 標準入力からJSONを読み取る
INPUT=$(cat) || { echo '{"decision": "approve"}'; exit 0; }

HOOK_STOP_WORDS_PATH=".claude/hooks/rules/hook_stop_words_rules.json"

# トランスクリプトを処理（.jsonl形式に対応）
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path' 2>/dev/null || echo "")
if [ -f "$TRANSCRIPT_PATH" ]; then
    # 最後のアシスタントメッセージのみを取得
    LAST_MESSAGE=$(tail -r "$TRANSCRIPT_PATH" 2>/dev/null | while IFS= read -r line; do
        if echo "$line" | jq -e '.type == "assistant"' >/dev/null 2>&1; then
            # すべてのテキストコンテンツを結合
            echo "$line" | jq -r '.message.content[]? | select(.type == "text") | .text' 2>/dev/null | tr '\n' ' '
            break
        fi
    done || true)

    # デバッグ: メッセージ内容をログ出力
    echo "DEBUG: LAST_MESSAGE='$LAST_MESSAGE'" >&2 2>/dev/null || true
    
    # hook_stop_words.jsonが存在する場合のみ処理
    if [ -f "$HOOK_STOP_WORDS_PATH" ]; then
        # 各ルールをループ処理
        RULES=$(jq -r 'keys[]' "$HOOK_STOP_WORDS_PATH" 2>/dev/null || echo "")
        for RULE_NAME in $RULES; do
            # キーワード配列を取得
            KEYWORDS=$(jq -r ".\"$RULE_NAME\".keywords[]" "$HOOK_STOP_WORDS_PATH" 2>/dev/null || echo "")
            MESSAGE=$(jq -r ".\"$RULE_NAME\".message" "$HOOK_STOP_WORDS_PATH" 2>/dev/null || echo "")

            # 各キーワードをチェック
            for keyword in $KEYWORDS; do
                if echo "$LAST_MESSAGE" | grep -q "$keyword" 2>/dev/null; then
                    # エラーメッセージを構成（文字化け対策）
                    ERROR_MESSAGE="禁止語句「${keyword}」が検出されました。ルール: ${RULE_NAME}。メッセージ: ${MESSAGE}"

                    # blockレスポンスを返す（JSONエスケープ）
                    ESCAPED_MESSAGE=$(echo "$ERROR_MESSAGE" | sed 's/"/\\"/g' 2>/dev/null || echo "Error processing message")
                    cat << EOF
{
  "decision": "block",
  "reason": "$ESCAPED_MESSAGE"
}
EOF
                    exit 0
                fi
            done
        done
    fi
fi

# キーワードが見つからなければ正常終了
echo '{"decision": "approve"}' 2>/dev/null || true
exit 0