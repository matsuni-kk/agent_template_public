---
description: "双方向エージェント変換・マスターファイル更新を実行"
argument-hint: "変換オプション（省略可）"
allowed-tools: ["Bash"]
---

# Agent Update

双方向エージェント変換・マスターファイル更新スクリプトを実行します。

## 使用方法
- `/agentupdate` (cursor→agents + マスター更新)
- `/agentupdate cursor` (cursor→agents + マスター更新)  
- `/agentupdate agents` (agents→cursor + マスター更新)
- `/agentupdate --dry-run` (ドライラン)
- `/agentupdate cursor --force` (強制実行)
- `/agentupdate agents --dry-run` (agents→cursor ドライラン)

## 実行内容

1. カレントディレクトリの確認
2. scripts/update_agent_master.pyの存在確認
3. 双方向エージェント変換の実行

!pwd

!if [ -f "scripts/update_agent_master.py" ]; then
  echo "update_agent_master.pyが見つかりました。"
  
  # 更新されたファイルを検出
  echo "📋 更新状況を確認中..."
  
  # .cursor/rulesの最新更新時刻
  CURSOR_LATEST=$(find .cursor/rules -name "*.mdc" -type f -exec stat -f "%m" {} \; 2>/dev/null | sort -n | tail -1)
  
  # .claude/agentsの最新更新時刻  
  AGENTS_LATEST=$(find .claude/agents -name "*.md" -o -name "*.mdc" -type f -exec stat -f "%m" {} \; 2>/dev/null | sort -n | tail -1)
  
  # どちらが新しいかを判定
  SUGGESTED_SOURCE=""
  if [ -n "$CURSOR_LATEST" ] && [ -n "$AGENTS_LATEST" ]; then
    if [ "$CURSOR_LATEST" -gt "$AGENTS_LATEST" ]; then
      SUGGESTED_SOURCE="cursor"
      echo "🔍 .cursor/rules が最近更新されています（推奨: cursor起点）"
    elif [ "$AGENTS_LATEST" -gt "$CURSOR_LATEST" ]; then
      SUGGESTED_SOURCE="agents"
      echo "🔍 .claude/agents が最近更新されています（推奨: agents起点）"
    else
      SUGGESTED_SOURCE="cursor"
      echo "🔍 同時刻更新または検出不可（推奨: cursor起点）"
    fi
  elif [ -n "$CURSOR_LATEST" ]; then
    SUGGESTED_SOURCE="cursor"
    echo "🔍 .cursor/rules のみ存在（推奨: cursor起点）"
  elif [ -n "$AGENTS_LATEST" ]; then
    SUGGESTED_SOURCE="agents"
    echo "🔍 .claude/agents のみ存在（推奨: agents起点）"
  else
    SUGGESTED_SOURCE="cursor"
    echo "🔍 ファイル検出不可（推奨: cursor起点）"
  fi
  
  # 引数が指定されている場合はそれを使用
  if [ -n "$ARGUMENTS" ]; then
    if [[ "$ARGUMENTS" == "cursor" ]]; then
      echo "▶️ cursor起点で実行します"
      python scripts/update_agent_master.py --source cursor --force
    elif [[ "$ARGUMENTS" == "agents" ]]; then
      echo "▶️ agents起点で実行します"
      python scripts/update_agent_master.py --source agents --force
    elif [[ "$ARGUMENTS" == "--dry-run" ]]; then
      echo "▶️ ${SUGGESTED_SOURCE}起点でドライランします"
      python scripts/update_agent_master.py --source $SUGGESTED_SOURCE --dry-run
    elif [[ "$ARGUMENTS" == "cursor --force" ]]; then
      python scripts/update_agent_master.py --source cursor --force
    elif [[ "$ARGUMENTS" == "agents --dry-run" ]]; then
      python scripts/update_agent_master.py --source agents --dry-run
    elif [[ "$ARGUMENTS" == "cursor --dry-run" ]]; then
      python scripts/update_agent_master.py --source cursor --dry-run  
    elif [[ "$ARGUMENTS" == "agents --force" ]]; then
      python scripts/update_agent_master.py --source agents --force
    else
      python scripts/update_agent_master.py $ARGUMENTS
    fi
  else
    # 引数なしの場合は起点を確認
    echo ""
    echo "🤖 どちらを起点にしますか？"
    echo "1) cursor (.cursor/rules → .claude/agents) [推奨: $SUGGESTED_SOURCE]"
    echo "2) agents (.claude/agents → .cursor/rules)"
    echo ""
    read -p "選択してください (1 or 2, Enter=推奨): " choice
    
    case $choice in
      1)
        echo "▶️ cursor起点で実行します"
        python scripts/update_agent_master.py --source cursor --force
        ;;
      2)
        echo "▶️ agents起点で実行します"
        python scripts/update_agent_master.py --source agents --force
        ;;
      "")
        echo "▶️ 推奨(${SUGGESTED_SOURCE})起点で実行します"
        python scripts/update_agent_master.py --source $SUGGESTED_SOURCE --force
        ;;
      *)
        echo "❌ 無効な選択です。推奨(${SUGGESTED_SOURCE})起点で実行します"
        python scripts/update_agent_master.py --source $SUGGESTED_SOURCE --force
        ;;
    esac
  fi
else
  echo "エラー: scripts/update_agent_master.pyが見つかりません"
  echo "カレントディレクトリ: $(pwd)"
  echo "scriptsディレクトリの内容:"
  ls -la scripts/ 2>/dev/null || echo "scriptsディレクトリが存在しません"
fi