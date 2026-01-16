# ChatGPT/Grok 並列検索ツール - 仕様書

## 概要
Chrome拡張機能「Browser Controller」を使ったChatGPT/Grok自動操作システム。
WebSocket経由でPythonからブラウザを制御し、3並列以上の検索を実行する。

## 対応サービス

| サービス | スクリプト | 特徴 |
|----------|-----------|------|
| ChatGPT | `chatgpt_multi.py` | Thinking強度、ファイル添付対応 |
| Grok | `grok_multi.py` | DeepThink、DeepSearch対応 |

## 共通機能

### 出力形式
- **MDファイル自動保存**: 回答取得と同時にFlow配下へ保存
  - ChatGPT: 質問ごとに別ファイル `Flow/YYYYMM/YYYY-MM-DD/<topic>/chatgpt_q{n}_YYYYMMDD_HHMMSS.md`
    - `<topic>` は先頭クエリ（または先頭メッセージ）から自動生成され、ファイル名に使えない文字は置換されます
  - Grok: 単一ファイル `Flow/YYYYMM/YYYY-MM-DD/grok_search_YYYYMMDD_HHMMSS.md`

### タイムアウト・進捗表示

| 項目 | デフォルト値 | CLI指定 |
|------|-------------|---------|
| タイムアウト（ChatGPT） | 1800秒（固定） | `--timeout` は無効 |
| タイムアウト（Grok） | 1800秒（デフォルト） | `--timeout` |
| ポーリング間隔 | 5秒 | `--interval` |
| 進捗表示 | 5秒ごと | - |

**進捗表示例**:
```
  Tab 1: Generating... (15s)
  Tab 2: Waiting... (12s)
  Tab 3: Done (8.5s) → Saved to MD
```

### 回答完了判定
- 生成中判定: Stopボタン + ストリーミング要素
- 安定判定: 20秒安定 + 最終再取得
- 短文防止: 最小文字数チェック

### 共通CLIオプション

```bash
# 両スクリプト共通
--timeout <seconds>    # Grokのみ有効（ChatGPTは固定1800秒）
--interval <seconds>   # ポーリング間隔（デフォルト: 5）
--tab <tabId>          # 特定タブを指定
--keep-tabs            # 完了後もタブを閉じない
```

### 共通コマンド

| コマンド | 説明 | 例 |
|----------|------|-----|
| `bridge` | ブリッジサーバー起動 | `python xxx_multi.py bridge` |
| `status` | 接続状態確認 | `python xxx_multi.py status` |
| `tabs` | タブ一覧 | `python xxx_multi.py tabs` |
| `chat` | 単一チャット | `python xxx_multi.py chat -m "質問"` |
| `reload` | 拡張機能リロード | `python xxx_multi.py reload` |

## アーキテクチャ

### 通信方式: WebSocket（固定）
```
[Python chatgpt_multi.py] 
    ↓ WebSocket (ws://localhost:9224)
[Bridge Server（chatgpt_multi.py内蔵）]
    ↓ WebSocket
[Chrome拡張機能 background.js]
    ↓ chrome.scripting.executeScript
[ChatGPT Webページ]
```

**重要**: Native MessagingやCDPへの移行は禁止。WebSocket方式を維持すること。

## ファイル構成

```
/skills/chatgpt-parallel-research/
├── SKILL.md                   ← Skill定義
├── guide/
│   └── guide.md               ← この仕様書
├── scripts/
│   ├── chatgpt_multi.py       ← ChatGPT専用スクリプト
│   └── grok_multi.py          ← Grok専用スクリプト
├── assets/
│   └── chatgpt_research_template.md
├── questions/
│   └── chatgpt_research_questions.md
└── evaluation/
    └── evaluation_criteria.md
```

## スクリプト実行方法

### 実行場所
スクリプトは任意のディレクトリから実行可能です。

```bash
# 方法1: フルパスで実行（推奨）
python /skills/chatgpt-parallel-research/scripts/chatgpt_multi.py "質問1" "質問2" "質問3"

# 方法2: scriptsディレクトリに移動して実行
cd /skills/chatgpt-parallel-research/scripts
python chatgpt_multi.py "質問1" "質問2" "質問3"

# 方法3: エイリアス設定（.bashrc/.zshrcに追加）
alias chatgpt='python /skills/chatgpt-parallel-research/scripts/chatgpt_multi.py'
chatgpt "質問1" "質問2" "質問3"
```

### 前提条件チェック
```bash
# Python バージョン確認（3.8以上が必要）
python --version

# websocketsライブラリ確認（なければ自動インストールされる）
python -c "import websockets; print(websockets.__version__)"

# Chrome拡張の接続確認
python /skills/chatgpt-parallel-research/scripts/chatgpt_multi.py status
```

### ブリッジサーバーについて
- **自動起動**: コマンド実行時にブリッジが起動していなければ自動で起動
- **手動起動不要**: 通常は意識する必要なし
- **手動起動が必要な場合**: デバッグ時やログ確認時
  ```bash
  python chatgpt_multi.py bridge  # フォアグラウンドで起動（ログ確認用）
  ```

**前提条件**:
- Python 3.8以上（websocketsは初回実行時に自動インストール）
- Browser Controller Chrome拡張機能がインストール済み
- ChatGPT/Grokにログイン済み

## コンポーネント詳細

### 1. Bridge Server（chatgpt_multi.py内蔵）

**役割**: Chrome拡張機能とPythonクライアント間のWebSocket中継

**ポート**: 9224

**動作**:
1. `ws://localhost:9224` でWebSocketサーバーを起動
2. Chrome拡張機能からの接続を待機（`extension_connected`メッセージ）
3. Pythonクライアントからのコマンドを拡張機能に転送
4. 拡張機能からの応答をクライアントに返却

**起動方法**:
```bash
# フォアグラウンド
python chatgpt_multi.py bridge

# バックグラウンド（自動起動される）
# コマンド実行時にブリッジが起動していなければ自動で起動
```

### 2. Chrome拡張機能（background.js）

**接続先**: `ws://localhost:9224`

**接続時の動作**:
1. WebSocket接続を確立
2. `{ type: 'extension_connected' }` を送信
3. 以降、コマンドを待機

**Keep-alive**:
- 20秒ごとにpingを送信
- chrome.alarmsで24秒ごとにService Workerを維持

**対応コマンド（24種）**:

| type | 説明 | パラメータ |
|------|------|-----------|
| **基本** |||
| `ping` | 疎通確認 | - |
| `get_tabs` | タブ一覧取得 | - |
| `get_active_tab` | アクティブタブ取得 | - |
| `new_tab` | 新規タブ | url |
| `close_tab` | タブを閉じる | tabId |
| `switch_tab` | タブ切替 | tabId |
| `navigate` | URL移動 | url, tabId? |
| **DOM操作** |||
| `click` | 要素クリック | selector, tabId?, index? |
| `type` | テキスト入力 | text, selector, tabId?, index? |
| `get_text` | テキスト取得 | selector, tabId? |
| `press_enter` | Enterキー送信 | selector?, tabId? |
| `scroll` | スクロール | direction, amount, tabId? |
| `get_elements` | 操作可能要素一覧 | tabId? |
| `execute_script` | スクリプト実行 | script, tabId? |
| `screenshot` | スクリーンショット | tabId? |
| **ChatGPT専用** |||
| `chatgpt_get_models` | モデル一覧 | tabId? |
| `chatgpt_select_model` | モデル選択 | model, tabId? |
| `chatgpt_get_thinking` | Thinking強度取得 | tabId? |
| `chatgpt_set_thinking` | Thinking強度設定 | level, tabId? |
| `chatgpt_is_generating` | 生成中か確認 | tabId? |
| `chatgpt_get_response` | 回答取得 | tabId? |
| `chatgpt_send_message` | メッセージ送信 | message, tabId? |
| `chatgpt_attach_file` | ファイル添付 | fileData, fileName, mimeType, tabId? |
| **Grok専用** |||
| `grok_send_message` | メッセージ送信 | message, tabId? |
| `grok_get_response` | 回答取得 | tabId? |
| `grok_is_generating` | 生成中か確認 | tabId? |
| `grok_get_models` | モデル一覧 | tabId? |
| `grok_select_model` | モデル選択 | model, tabId? |
| `grok_set_mode` | モード設定 | mode, tabId? |
| `grok_is_deepthink` | DeepThink状態確認 | tabId? |
| `grok_enable_deepthink` | DeepThink有効化 | tabId? |
| `grok_disable_deepthink` | DeepThink無効化 | tabId? |
| `grok_enable_deepsearch` | DeepSearch有効化 | tabId? |
| **管理** |||
| `reload_extension` | 拡張機能リロード | - |

### chatgpt_get_response の戻り値

```javascript
{
  success: true,
  response: "最後の回答テキスト",
  allResponses: ["回答1", "回答2", ...],  // 全回答の配列
  responseCount: 5,                        // 回答数
  citations: [                             // <a>タグから抽出したリンク
    { text: "リンクテキスト", url: "https://..." }
  ],
  urls: ["https://...", ...]               // テキストから正規表現で抽出したURL
}
```

**注意**: 
- `citations`: ChatGPTの現在のUI実装では`<a>`タグが使われていないことが多く、空になる場合がある
- `urls`: テキストに含まれるURLを正規表現で抽出。ChatGPTに「URLを直接テキストに含めて回答して」と指示すると確実に取得可能

### 3. Python CLI（chatgpt_multi.py）

**使用例**:
```bash
# ブリッジサーバー起動（フォアグラウンド）
python chatgpt_multi.py bridge

# 接続状態確認
python chatgpt_multi.py status

# タブ一覧
python chatgpt_multi.py tabs

# モデル一覧
python chatgpt_multi.py models

  # 単一チャット
  python chatgpt_multi.py chat -m "質問内容"
  
  # 要素一覧を取得
  python chatgpt_multi.py elements
  python chatgpt_multi.py elements --tab 123456
  
  # 要素をテキストで検索（Pro, model等）
  python chatgpt_multi.py search-elements -m "Pro"
  python chatgpt_multi.py se "Pro" --tab 123456
  
  # ページテキストを検索
  python chatgpt_multi.py page-text -m "Pro"
  python chatgpt_multi.py pt "model"
  
  # タブを詳細検査（モデル、Thinking、Pro関連要素）
  python chatgpt_multi.py inspect
  python chatgpt_multi.py inspect --tab 123456
  ```

### 4. Python CLI（grok_multi.py）

**使用例**:
```bash
# ブリッジサーバー起動（フォアグラウンド）
python grok_multi.py bridge

# 接続状態確認
python grok_multi.py status

# タブ一覧
python grok_multi.py tabs

# モデル一覧
python grok_multi.py models

# 単一チャット
python grok_multi.py chat -m "質問内容"
python grok_multi.py chat -m "質問内容" --tab 123456

# 並列検索（3並列以上推奨）
python grok_multi.py "質問1" "質問2" "質問3"

# DeepThinkで難問を解く
python grok_multi.py "難問1" "難問2" "難問3" --deepthink

# DeepSearchで検索強化
python grok_multi.py "検索1" "検索2" "検索3" --deepsearch

# DeepThink有効化（既存タブ）
python grok_multi.py deepthink --tab 123456

# DeepSearch有効化（既存タブ）
python grok_multi.py deepsearch --tab 123456

# 最新回答を取得
python grok_multi.py response --tab 123456
```

### grok_get_response の戻り値

```javascript
{
  success: true,
  response: "最後の回答テキスト",
  allResponses: ["回答1", ...],
  responseCount: 1,
  citations: [{ text: "リンクテキスト", url: "https://..." }],
  urls: ["https://...", ...],
  debug: {
    thinkingLine: "14秒間シンキングしました",
    thinkingLineIndex: 48,
    foundResponseLines: 3
  }
}
```

**Grok回答取得の特徴**:
- 「X秒間シンキングしました」の後のテキストを回答として抽出
- フォローアップ提案（「〜について詳しく」「〜を教えて」等）は自動除外
- 最後のシンキング行を基準にするため、会話履歴があっても最新の回答のみ取得

## 設定

### デフォルト値
| 項目 | ChatGPT | Grok |
|------|---------|------|
| タイムアウト | 1200秒（20分） | 1200秒（20分） |
| CLIデフォルトtimeout | 1800秒（30分） | 1800秒（30分） |
| ポーリング間隔 | 5秒 | 5秒 |
| WebSocketポート | 9224 | 9224（共通） |
| デフォルトモデル | ChatGPT 5.2 Thinking | - |

### ChatGPT Thinking強度
| レベル | 説明 |
|--------|------|
| light | 軽い推論 |
| standard | 標準 |
| heavy | 重い推論（難問向け） |
| extended | 拡張推論 |

### Grok モード
| モード | 説明 |
|--------|------|
| DeepThink | 深い思考モード（回答前に「X秒間シンキングしました」表示） |
| DeepSearch | 検索強化モード（外部ソースを参照） |

## URLフォールバック機能

タブからDOM経由で回答を取得できない場合（DOM構造変更、認証エラー等）に、URLを直接フェッチしてMarkdownに変換するフォールバック機能。

### 動作フロー
1. **通常取得**: ポーリングで`chatgpt_get_response`/`grok_get_response`を監視
2. **タイムアウト発生**: 設定時間内に回答が取得できない
3. **フォールバック実行**: タブのURLを取得し、`httpx`で直接フェッチ
4. **Markdown変換**: `html2text`でHTMLをMarkdownに変換
5. **MD保存**: 変換結果をFlowディレクトリに保存

### 依存ライブラリ（自動インストール）
- `httpx`: 非同期HTTPクライアント
- `html2text`: HTML→Markdown変換

### 制限事項
- ログイン必須ページ（ChatGPT/Grok）はクッキーなしでフェッチできないため、フォールバックは限定的
- 公開URLや共有リンクには有効

## トラブルシューティング

### 接続できない場合

1. **ブリッジサーバーが起動しているか確認**
   ```bash
   python chatgpt_multi.py status
   lsof -i :9224
   ```

2. **Chrome拡張機能を再ロード**
   - `chrome://extensions/` を開く
   - Browser Controllerの更新ボタンをクリック
   - Service Workerのリンクをクリックしてログ確認

3. **ブリッジサーバーを再起動**
   ```bash
   # 既存プロセスを終了
   pkill -f "chatgpt_multi.*bridge"
   
   # 再起動
   python chatgpt_multi.py bridge &
   ```

### websockets v14+の並列処理制限

**問題**: 同じWebSocket接続で同時にsend/recvするとエラー

**対策**: `asyncio.Lock()`による排他制御を実装済み（chatgpt_multi.py内）

### Service Workerのライフサイクル

**問題**: Chromeは30秒でService Workerを停止する

**対策**:
- chrome.alarmsで24秒ごとにkeep-alive
- WebSocket pingで20秒ごとに通信

## ユーザーの好み

- Python 1ファイルで完結（可能な限り）
- 手動操作を最小化
- WebSocket方式を維持（Native Messaging/CDPは使わない）
- デフォルトモデル: ChatGPT 5.2 Thinking

## 変更履歴

| 日付 | 変更内容 |
|------|----------|
| 2026-01-12 | 仕様書作成 |
| 2026-01-12 | 疎通確認完了。ブリッジサーバー起動（PID: 98414）→ Chrome拡張機能が自動接続 → get_tabsコマンドでタブ一覧取得成功 |
| 2026-01-12 | ChatGPTプロンプト送信成功。background.jsのバグ修正（args配列のundefined問題、回答取得の文字数閾値問題） |
| 2026-01-12 | SPEC.md → guide/guide.md に移動・リネーム |
| 2026-01-12 | ポーリング間隔を10秒→5秒に変更 |
| 2026-01-12 | chatgpt_multi.pyのフォールバックフィルタ修正（50文字→0文字） |
| 2026-01-12 | 3並列×3応答の会話テスト成功 |
| 2026-01-12 | URL/citation取得機能追加（background.js） |
| 2026-01-12 | CLI要素検索コマンド追加（elements, search-elements, page-text, inspect） |
| 2026-01-12 | Grok操作機能追加: background.jsにGrokコマンド11種、grok_multi.py新規作成 |
| 2026-01-12 | スクリプト分離: chatgpt_multi.py（ChatGPT専用）とgrok_multi.py（Grok専用） |
| 2026-01-12 | guide.md更新: 共通機能セクション追加、ChatGPT/Grok比較形式に統一 |
| 2026-01-13 | chatgpt_multi.py: chatメソッド改善（responseCount比較方式で2往復目の回答区別に対応） |
| 2026-01-13 | grok_multi.py: 共通機能追加（DOM操作、ファイル添付、スクリーンショット、CLI） |
| 2026-01-13 | ファイル添付+2往復テスト成功: 1350円計算、ぶどう回答を正しく取得 |
| 2026-01-13 | URLフォールバック機能追加: タブから回答取得できない場合にhttpx+html2textで直接フェッチ |
| 2026-01-13 | CLI引数解析バグ修正: 第1引数が既知コマンド以外の場合は質問として扱うよう修正（KNOWN_COMMANDS判定追加） |
| 2026-01-13 | 回答途中切れ問題修正: stable_count閾値を2→4に増加、最小文字数判定と3秒のDOM確定待機を追加、最終取得で変化時はリセット |
| 2026-01-13 | 送信処理をchatgpt_send_messageに統一し、入力欄待機＋リトライで安定化 |

## 作業ログ

### 2026-01-12 疎通確認

#### 実施内容
1. ブリッジサーバーの起動状態を確認 → 停止していた
2. ブリッジサーバーをバックグラウンドで起動
   ```bash
   # Skillのscriptsディレクトリで実行
   nohup python3 chatgpt_multi.py bridge > /tmp/bridge.log 2>&1 &
   ```
3. ポート9224の使用確認 → Python PID 98414 で起動中
4. statusコマンドで確認 → `[Bridge] Running on ws://localhost:9224`
5. WebSocket直接テストでget_tabsコマンド送信 → 成功、50+タブの情報取得

#### 結果
- ブリッジサーバー: 正常起動
- Chrome拡張機能: 自動接続済み
- 通信: 正常（get_tabs成功）

#### 注意事項
- macOSには`timeout`コマンドがないため、Pythonでタイムアウト処理を行う必要あり
- websockets v14+のDeprecationWarningが出るが動作に影響なし

### 2026-01-12 ChatGPTプロンプト送信修正

#### 問題
1. `type`コマンドでタイムアウト → args配列に`undefined`が含まれシリアライズエラー
2. `chatgpt_get_response`で回答が取得できない → 50文字以下の回答が除外されていた

#### 修正内容（background.js）
1. **args配列のundefined問題**
   ```javascript
   // Before
   args: [selector, text, index]
   
   // After
   args: [selector, text, index ?? null]
   ```
   - `click`, `type`, `pressEnter`, `getText`などの関数で修正

2. **回答取得の文字数閾値**
   ```javascript
   // Before
   .filter(t => t.length > 50)
   
   // After
   .filter(t => t.length > 0)
   ```

3. **エラーハンドリング強化**
   ```javascript
   async function handleCommand(msg) {
     try {
       // switch文...
     } catch (e) {
       console.error('[BrowserController] Command error:', type, e);
       return { type: 'error', error: e.message, command: type };
     }
   }
   ```

#### テスト結果
```
New tab: 1104714167
Type: True
Click: True
Waiting...
Done after 3s
Answer: 東京
```

- 新規タブ開く: 成功
- テキスト入力: 成功
- 送信ボタンクリック: 成功
- 回答待機: 成功（3秒で完了）
- 回答取得: 成功（「東京」）

### 2026-01-12 3並列×3応答の会話テスト

#### 実施内容
1. 3つのChatGPTタブを並列で開く
2. 各タブに異なる質問を送信（Round 1）
3. 5秒間隔でポーリングして回答完了を検知
4. フォローアップ質問を送信（Round 2, 3）
5. 全ての回答を取得

#### テスト結果
- Round 1: 3並列で質問送信 → 全回答取得成功
- Round 2: フォローアップ質問送信 → 全回答取得成功
- Round 3: フォローアップ質問送信 → 全回答取得成功

#### 結論
5秒ポーリングで3並列×3ラウンドの会話が正常に動作することを確認。

### 2026-01-12 URL/citation取得機能追加

#### 実施内容
background.jsの`chatgptGetResponse`関数に以下を追加：

1. **citations**: `<a>`タグから抽出
   ```javascript
   el.querySelectorAll('a[href]').forEach(a => {
     const href = a.href;
     if (href && !href.includes('chatgpt.com')) {
       citations.push({ text: a.innerText.trim(), url: href });
     }
   });
   ```

2. **urls**: テキストから正規表現で抽出
   ```javascript
   const urlRegex = /https?:\/\/[^\s<>"{}|\\^`\[\]]+/g;
   const foundUrls = lastResponse.match(urlRegex) || [];
   urls = [...new Set(foundUrls)];
   ```

#### テスト結果
- `citations`: ChatGPTの現在のUI実装では`<a>`タグが使われていないため空
- `urls`: テキストに含まれるURLは正常に抽出可能

#### 対処法
ChatGPTに「URLを直接テキストに含めて回答して」と指示すれば確実に取得可能。

### 2026-01-12 モデル切替コマンド追加

#### 実施内容
ChatGPTのモデルセレクタードロップダウンを自動操作するコマンドを追加。

#### 新規コマンド

**set-mode**: モデルモード切替（auto/instant/thinking/pro）
```bash
python chatgpt_multi.py set-mode thinking --tab <tabId>
python chatgpt_multi.py set-mode pro --tab <tabId>
python chatgpt_multi.py set-mode auto --tab <tabId>
python chatgpt_multi.py set-mode instant --tab <tabId>
```

**enable-pro**: Pro Modeを有効化
```bash
python chatgpt_multi.py enable-pro --tab <tabId>
```

**is-pro**: 現在のモード確認
```bash
python chatgpt_multi.py is-pro --tab <tabId>
# 出力例:
# [Pro Mode] ENABLED
#   Current mode: pro
```

**debug-dropdown**: ドロップダウンのデバッグ情報取得
```bash
python chatgpt_multi.py debug-dropdown --tab <tabId>
python chatgpt_multi.py dd --tab <tabId>  # エイリアス
```

**DOM調査コマンド**: ページのDOM構造を調査
```bash
# サマリー（デフォルト）
python chatgpt_multi.py dom --tab <tabId>

# data-testid一覧
python chatgpt_multi.py dom testids --tab <tabId>

# インタラクティブ要素一覧
python chatgpt_multi.py dom interactive --tab <tabId>

# ARIA属性要素
python chatgpt_multi.py dom aria --tab <tabId>

# ツリー構造
python chatgpt_multi.py dom tree --tab <tabId>

# テキスト検索
python chatgpt_multi.py dom "Pro" --tab <tabId>

# セレクター指定
python chatgpt_multi.py dom '[data-testid="model-switcher"]' --tab <tabId>
```

**スクリーンショットコマンド**:
```bash
# スクリーンショット取得
python chatgpt_multi.py screenshot --tab <tabId>
python chatgpt_multi.py ss --tab <tabId>  # エイリアス

# ドロップダウン開いた状態でスクリーンショット
python chatgpt_multi.py screenshot-dropdown --tab <tabId>
python chatgpt_multi.py ssd --tab <tabId>  # エイリアス
```

#### 技術的詳細

**ドロップダウン操作の課題と解決策**:
ChatGPTはRadix UIを使用しており、`dispatchEvent`で送信したイベントがReactの状態管理に正しく反映されない問題があった。

**解決策**: 複数のクリック方式を順次試行
1. `button.click()` - 最もシンプル
2. Enterキーイベント - キーボードアクセシビリティ対応
3. PointerEvent - マウスイベントのシミュレーション

**MutationObserverでメニュー出現を検知**:
```javascript
const observer = new MutationObserver(() => {
  const modeButton = document.querySelector(`[data-testid="${testId}"]`);
  if (modeButton) {
    observer.disconnect();
    modeButton.click();
  }
});
observer.observe(document.body, { childList: true, subtree: true });
```

#### data-testidマッピング
| モード | data-testid |
|--------|-------------|
| Auto | `model-switcher-gpt-5-2` |
| Instant | `model-switcher-gpt-5-2-instant` |
| Thinking | `model-switcher-gpt-5-2-thinking` |
| Pro | `model-switcher-gpt-5-2-pro` |

**注意**: Autoモードは`-auto`サフィックスなし（2026年1月時点）。

### 2026-01-13 回答途中切れ問題の修正

#### 問題
ChatGPTの長文回答（225行）が途中で切れて121行しか取得できない問題が発生。

#### 原因分析
1. `stable_count >= 2` の完了判定が早すぎた（5秒×2回=10秒で完了判定）
2. ストリーミング完了直後のDOM更新が間に合っていなかった

#### 修正内容（chatgpt_multi.py 646-679行目付近）

**Before**:
```python
if stable_count >= 2:
    result = {...}
```

**After**:
```python
if stable_count >= 4:  # 5秒×4=20秒待機
    if len(response) < MIN_RESPONSE_LEN:
        stable_count = 0
        continue
    
    # 完了確定後、DOM確定のため追加で3秒待機
    print(f"  Tab {idx+1}: Finalizing response...")
    await asyncio.sleep(3)
    
    # 最終取得（DOM完全確定後）
    final_response = await self.get_response(tid)
    if final_response and final_response != response:
        stable_count = 0
        last_response = final_response
        continue
    if final_response and len(final_response) >= len(response):
        response = final_response
    
    result = {...}
```

#### テスト結果
```bash
python chatgpt_multi.py "Pythonでシングルトンパターンを実装する方法を3つ挙げて..."
```
- 修正前: 121行で途中切れ
- 修正後: 225行の完全な回答を取得

### 2026-01-13 CLI引数解析バグの修正

#### 問題
`python chatgpt_multi.py "質問"` と実行すると、質問が`command`として認識され、searchが実行されなかった。

#### 原因
argparseの設計で最初の引数が`command`に入り、`questions`が空になっていた。

#### 修正内容（chatgpt_multi.py 1008-1023行目付近）
```python
# 既知のコマンド一覧
KNOWN_COMMANDS = [
    'search', 'tabs', 'models', 'thinking', 'set-thinking', 'enable-pro',
    'is-pro', 'set-mode', 'attach', 'chat', 'response', 'debug-dropdown',
    'dd', 'screenshot', 'ss', 'screenshot-dropdown', 'ssd', 'inspect',
    'dom', 'bridge', 'status'
]

# コマンド判定：最初の引数が既知コマンドでなければ質問として扱う
cmd = args.command.lower() if args.command else 'search'

if cmd not in KNOWN_COMMANDS:
    # 既知コマンドでなければ、最初の引数も質問リストに追加
    all_questions = [args.command] + (args.questions or [])
    args.questions = all_questions
    cmd = 'search'
```

#### 動作確認
```bash
# 修正前: "質問1"がcommandに入りsearchが実行されない
python chatgpt_multi.py "質問1" "質問2" "質問3"

# 修正後: "質問1"も質問として扱われ、3並列検索が実行される
python chatgpt_multi.py "質問1" "質問2" "質問3"
```
