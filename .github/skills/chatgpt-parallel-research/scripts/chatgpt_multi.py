#!/usr/bin/env python3
"""
ChatGPT Parallel Research Tool
==============================
3並列以上のChatGPT検索・ブレスト・情報収集を1つのスクリプトで実行

機能:
- 並列質問送信（3並列以上推奨）
- モデル選択（ChatGPT 5.2 Thinking等）
- Thinking強度設定（light/standard/heavy/extended）
- ファイル添付
- 確実な回答取得（本文のみ、引用リンク除外）
- タブ管理
- ブリッジサーバー内蔵（自動起動）

使用例:
  # 基本的な並列検索
  python chatgpt_multi.py "質問1" "質問2" "質問3"
  
  # Heavy thinkingで難問を解く
  python chatgpt_multi.py "難しい質問1" "難しい質問2" "難しい質問3" --thinking heavy
  
  # ファイル添付して分析
  python chatgpt_multi.py attach --file document.pdf --tab 123456
  
  # タブ一覧を確認
  python chatgpt_multi.py tabs
  
  # モデル一覧を確認
  python chatgpt_multi.py models
  
  # ブリッジサーバーのみ起動（手動）
  python chatgpt_multi.py bridge
"""

import asyncio
import json
import time
import base64
import mimetypes
import os
import sys
import socket
import subprocess
from typing import List, Dict, Optional, Any
from pathlib import Path

# WebSocketライブラリ（自動インストール）
def _ensure_websockets():
    """websocketsがなければ自動インストール"""
    try:
        import websockets
        return websockets
    except ImportError:
        print("[Auto-install] Installing websockets...")
        # --userで試し、失敗したら--break-system-packages
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "websockets", "--user", "-q"],
                stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "websockets", "--break-system-packages", "-q"],
                stderr=subprocess.DEVNULL
            )
        import websockets
        return websockets

websockets = _ensure_websockets()
from websockets.server import serve


# ========================================
# Bridge Server (内蔵)
# ========================================

class BridgeServer:
    """拡張機能とPythonクライアント間のWebSocketブリッジサーバー"""
    
    PORT = 9224
    
    def __init__(self):
        self.extension_ws = None
        self.pending = {}
        self.running = False
    
    @staticmethod
    def is_running() -> bool:
        """ブリッジサーバーが起動中かチェック"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(1)
            sock.connect(('localhost', BridgeServer.PORT))
            sock.close()
            return True
        except (socket.error, socket.timeout):
            return False
    
    async def handler(self, ws):
        """WebSocket接続ハンドラー"""
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(msg)
            
            # 拡張機能からの接続
            if data.get('type') == 'extension_connected':
                print("[Bridge] Chrome extension connected")
                self.extension_ws = ws
                
                async for message in ws:
                    try:
                        resp = json.loads(message)
                        
                        # pingは無視
                        if resp.get('type') == 'ping':
                            continue
                        
                        req_id = resp.get('requestId')
                        if req_id and req_id in self.pending:
                            self.pending[req_id].set_result(resp)
                            
                    except json.JSONDecodeError:
                        pass
                
                print("[Bridge] Chrome extension disconnected")
                self.extension_ws = None
                return
            
            # Pythonクライアントからのコマンド - 最初のメッセージを処理
            async def process_command(cmd_data):
                if self.extension_ws is None:
                    await ws.send(json.dumps({'error': 'Extension not connected'}))
                    return
                
                req_id = cmd_data.get('requestId') or f"r{id(cmd_data)}"
                cmd_data['requestId'] = req_id
                
                future = asyncio.get_event_loop().create_future()
                self.pending[req_id] = future
                
                try:
                    await self.extension_ws.send(json.dumps(cmd_data))
                    response = await asyncio.wait_for(future, timeout=30.0)
                    await ws.send(json.dumps(response))
                except asyncio.TimeoutError:
                    await ws.send(json.dumps({'error': 'Timeout', 'requestId': req_id}))
                finally:
                    self.pending.pop(req_id, None)
            
            # 最初のコマンドを処理
            await process_command(data)
            
            # 以降のコマンドをループで待機
            async for message in ws:
                try:
                    cmd_data = json.loads(message)
                    await process_command(cmd_data)
                except json.JSONDecodeError:
                    pass
                
        except Exception as e:
            print(f"[Bridge] Error: {e}")
    
    async def run(self):
        """ブリッジサーバーを起動"""
        self.running = True
        print(f"[Bridge] Starting on ws://localhost:{self.PORT}")
        print("[Bridge] Waiting for Chrome extension connection...")
        print("[Bridge] Press Ctrl+C to stop\n")
        
        async with serve(self.handler, 'localhost', self.PORT):
            await asyncio.Future()  # 永久に待機
    
    @staticmethod
    def start_background():
        """バックグラウンドプロセスでブリッジサーバーを起動"""
        import subprocess
        
        # 現在のスクリプトをbridgeモードで起動
        script_path = os.path.abspath(__file__)
        process = subprocess.Popen(
            [sys.executable, script_path, 'bridge'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        # 起動完了を待つ
        for _ in range(30):  # 最大3秒待機
            time.sleep(0.1)
            if BridgeServer.is_running():
                print(f"[Bridge] Started in background (PID: {process.pid})")
                return True
        
        print("[Bridge] Failed to start")
        return False


# ========================================
# ChatGPT Controller
# ========================================

class ChatGPTController:
    """ChatGPT操作の統合コントローラー"""
    
    BRIDGE_URL = "ws://localhost:9224"
    
    def __init__(self, timeout: int = 1200, poll_interval: int = 5, auto_bridge: bool = True):
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.auto_bridge = auto_bridge
        self._ws = None
        self._request_id = 0
        self._pending = {}
        self._lock = asyncio.Lock()  # WebSocket排他制御用
        self._session_tabs = []  # セッションタブ情報のリスト（id/url）
        self._load_session_tabs()  # 前回のセッションタブを復元
    
    # ========================================
    # WebSocket通信
    # ========================================
    
    async def connect(self):
        """ブリッジサーバーに接続（必要なら自動起動）"""
        if self._ws is None or (hasattr(self._ws, 'closed') and self._ws.closed) or (hasattr(self._ws, 'state') and self._ws.state.name == 'CLOSED'):
            # ブリッジサーバーが起動していなければ起動
            if self.auto_bridge and not BridgeServer.is_running():
                print("[Bridge] Not running, starting automatically...")
                if not BridgeServer.start_background():
                    raise ConnectionError("Failed to start bridge server")
                # 少し待ってから接続
                await asyncio.sleep(0.5)
            
            try:
                self._ws = await websockets.connect(self.BRIDGE_URL)
            except Exception as e:
                raise ConnectionError(f"Failed to connect to bridge server: {e}")
    
    async def _cmd(self, **kwargs) -> Dict:
        """コマンドを送信して応答を待つ（同期方式・排他制御付き）"""
        async with self._lock:  # WebSocket操作を排他制御
            await self.connect()
            self._request_id += 1
            req_id = f"r{self._request_id}"
            kwargs['requestId'] = req_id
            
            await self._ws.send(json.dumps(kwargs))
            
            # 応答を待つ（同期的に受信）
            try:
                response = await asyncio.wait_for(self._ws.recv(), timeout=30)
                return json.loads(response)
            except asyncio.TimeoutError:
                return {'error': 'Timeout waiting for response'}
    
    # ========================================
    # タブ操作
    # ========================================
    
    async def get_tabs(self) -> List[Dict]:
        """タブ一覧を取得"""
        result = await self._cmd(type='get_tabs')
        return result.get('tabs', [])
    
    async def new_tab(self, url: str) -> Dict:
        """新しいタブを開く"""
        return await self._cmd(type='new_tab', url=url)
    
    async def close_tab(self, tab_id: int) -> Dict:
        """タブを閉じる"""
        return await self._cmd(type='close_tab', tabId=tab_id)
    
    async def switch_tab(self, tab_id: int) -> Dict:
        """タブを切り替える"""
        return await self._cmd(type='switch_tab', tabId=tab_id)
    
    # ========================================
    # セッション管理
    # ========================================
    
    def _get_session_file(self) -> Path:
        """セッションファイルのパスを取得"""
        return Path.home() / ".chatgpt_multi_session.json"
    
    def _normalize_session_tabs(self, tabs) -> List[Dict]:
        """セッションタブ情報を正規化（後方互換: intリストも受ける）"""
        normalized = []
        if not isinstance(tabs, list):
            return normalized
        
        for t in tabs:
            if isinstance(t, int):
                normalized.append({'id': t, 'url': None, 'topic': None})
            elif isinstance(t, dict):
                tid = t.get('id')
                if tid:
                    normalized.append({'id': tid, 'url': t.get('url'), 'topic': t.get('topic')})
        
        return normalized
    
    def _load_session_tabs(self):
        """前回のセッションタブを復元"""
        session_file = self._get_session_file()
        if session_file.exists():
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                    self._session_tabs = self._normalize_session_tabs(data.get('tabs', []))
            except Exception:
                self._session_tabs = []
        else:
            self._session_tabs = []
    
    def _save_session_tabs(self, tabs) -> None:
        """セッションタブを保存（tabsは[{id,url}] もしくは[int]）"""
        session_file = self._get_session_file()
        try:
            normalized = self._normalize_session_tabs(tabs)
            with open(session_file, 'w') as f:
                json.dump({'tabs': normalized}, f)
            self._session_tabs = normalized
        except Exception as e:
            print(f"[Warning] Failed to save session: {e}")
    
    def get_session_tabs(self) -> List[int]:
        """現在のセッションタブIDリストを取得"""
        return [t.get('id') for t in self._session_tabs if t.get('id')]
    
    def _get_session_tab_url(self, tab_id: int) -> Optional[str]:
        for t in self._session_tabs:
            if t.get('id') == tab_id:
                return t.get('url')
        return None
    
    def _get_session_tab_topic(self, tab_id: int) -> Optional[str]:
        for t in self._session_tabs:
            if t.get('id') == tab_id:
                return t.get('topic')
        return None
    
    def _sanitize_topic(self, topic: str, max_len: int = 60) -> str:
        import re
        if not topic:
            return 'untitled'
        
        t = str(topic).strip()
        t = re.sub(r'\s+', ' ', t)
        t = t.replace('/', '_').replace('\\', '_')
        t = t.replace(':', '_')
        t = re.sub(r'[\*\?"<>\|]', '_', t)
        t = t.strip(' ._')
        t = t.replace(' ', '_')
        if len(t) > max_len:
            t = t[:max_len]
        return t or 'untitled'
    
    def _derive_topic_from_questions(self, questions: List[str]) -> str:
        if not questions:
            return 'untitled'
        return self._sanitize_topic(questions[0])
    
    def _derive_topic_from_message(self, message: str) -> str:
        return self._sanitize_topic(message)
    
    async def _get_open_tab_url(self, tab_id: int) -> Optional[str]:
        tabs = await self.get_tabs()
        for t in tabs:
            if t.get('id') == tab_id:
                return t.get('url')
        return None
    
    async def _build_session_entries(self, tab_ids: List[int], topic: str = None) -> List[Dict]:
        tabs = await self.get_tabs()
        by_id = {t.get('id'): t for t in tabs if t.get('id')}
        entries = []
        for tid in tab_ids:
            info = by_id.get(tid, {})
            entries.append({'id': tid, 'url': info.get('url'), 'topic': topic})
        return entries
    
    async def get_active_session_tab(self) -> Optional[int]:
        """アクティブなセッションタブを取得（なければURLから再オープン）"""
        all_tabs = await self.get_tabs()
        open_by_id = {t.get('id'): t for t in all_tabs if t.get('id')}
        
        # セッションタブの中で現在も開いているものを探す
        for entry in self._session_tabs:
            tid = entry.get('id')
            if tid in open_by_id:
                current_url = open_by_id[tid].get('url')
                if current_url and current_url != entry.get('url'):
                    entry['url'] = current_url
                    self._save_session_tabs(self._session_tabs)
                return tid
        
        # すべて閉じている場合は、保存されたURLで再オープン
        for entry in self._session_tabs:
            url = entry.get('url')
            if url:
                print("[Session] Session tab is not open. Reopening from saved URL...")
                result = await self.new_tab(url)
                new_id = result.get('tab', {}).get('id')
                if new_id:
                    entry['id'] = new_id
                    await asyncio.sleep(3)
                    current_url = await self._get_open_tab_url(new_id) or url
                    entry['url'] = current_url
                    self._save_session_tabs(self._session_tabs)
                    return new_id
        
        return None
    
    # ========================================
    # 基本DOM操作
    # ========================================
    
    async def click(self, selector: str, tab_id: int = None) -> Dict:
        """要素をクリック"""
        return await self._cmd(type='click', selector=selector, tabId=tab_id)
    
    async def type_text(self, text: str, selector: str, tab_id: int = None) -> Dict:
        """テキストを入力"""
        return await self._cmd(type='type', text=text, selector=selector, tabId=tab_id)
    
    async def get_text(self, selector: str, tab_id: int = None) -> Dict:
        """テキストを取得"""
        return await self._cmd(type='get_text', selector=selector, tabId=tab_id)
    
    async def get_elements(self, tab_id: int = None) -> List[Dict]:
        """操作可能な要素一覧を取得"""
        result = await self._cmd(type='get_elements', tabId=tab_id)
        return result.get('elements', [])
    
    async def search_elements(self, query: str, tab_id: int = None) -> List[Dict]:
        """
        要素をテキストで検索
        
        Args:
            query: 検索文字列（大文字小文字を区別しない）
            tab_id: タブID
        
        Returns:
            マッチした要素のリスト
        """
        elements = await self.get_elements(tab_id)
        query_lower = query.lower()
        matches = []
        
        for i, el in enumerate(elements):
            text = (el.get('text') or '').lower()
            selector = (el.get('selector') or '').lower()
            el_type = (el.get('type') or '').lower()
            
            if query_lower in text or query_lower in selector or query_lower in el_type:
                matches.append({'index': i, **el})
        
        return matches
    
    async def get_page_text(self, tab_id: int = None, selector: str = 'body') -> str:
        """ページ全体のテキストを取得"""
        result = await self.get_text(selector, tab_id)
        return result.get('text', '')
    
    # ========================================
    # ChatGPT専用機能
    # ========================================
    
    async def get_models(self, tab_id: int = None) -> Dict:
        """利用可能なモデル一覧を取得"""
        return await self._cmd(type='chatgpt_get_models', tabId=tab_id)
    
    async def select_model(self, model: str, tab_id: int = None) -> Dict:
        """モデルを選択"""
        return await self._cmd(type='chatgpt_select_model', model=model, tabId=tab_id)
    
    async def get_thinking(self, tab_id: int = None) -> Dict:
        """現在のThinking強度を取得"""
        return await self._cmd(type='chatgpt_get_thinking', tabId=tab_id)
    
    async def enable_pro(self, tab_id: int = None) -> Dict:
        """Pro Modeを有効化"""
        return await self._cmd(type='chatgpt_enable_pro', tabId=tab_id)
    
    async def is_pro(self, tab_id: int = None) -> Dict:
        """Pro Mode状態を確認"""
        return await self._cmd(type='chatgpt_is_pro', tabId=tab_id)
    
    async def set_mode(self, mode: str, tab_id: int = None) -> Dict:
        """
        ChatGPTモードを設定
        
        Args:
            mode: 'auto' | 'instant' | 'thinking' | 'pro'
            tab_id: タブID
        """
        return await self._cmd(type='chatgpt_set_mode', mode=mode, tabId=tab_id)
    
    async def debug_dropdown(self, tab_id: int = None) -> Dict:
        """ドロップダウンを開いてdata-testid一覧を取得（デバッグ用）"""
        return await self._cmd(type='chatgpt_debug_dropdown', tabId=tab_id)
    
    async def screenshot(self, tab_id: int = None, save_path: str = None) -> Dict:
        """
        タブのスクリーンショットを撮影
        
        Args:
            tab_id: タブID（省略時はアクティブタブ）
            save_path: 保存先パス（省略時はdata URLのみ返す）
        
        Returns:
            成功時: {'success': True, 'dataUrl': '...', 'path': '...'}
        """
        result = await self._cmd(type='screenshot', tabId=tab_id)
        
        if result.get('success') and save_path and result.get('dataUrl'):
            # Base64データをファイルに保存
            import base64
            data_url = result['dataUrl']
            # data:image/png;base64,xxxxx の形式からbase64部分を抽出
            if ',' in data_url:
                base64_data = data_url.split(',')[1]
                with open(save_path, 'wb') as f:
                    f.write(base64.b64decode(base64_data))
                result['path'] = save_path
        
        return result
    
    async def screenshot_dropdown(self, tab_id: int = None, save_path: str = None) -> Dict:
        """
        ドロップダウンを開いた状態でスクリーンショットを撮影
        """
        result = await self._cmd(type='screenshot_dropdown', tabId=tab_id)
        
        if result.get('success') and save_path and result.get('dataUrl'):
            import base64
            data_url = result['dataUrl']
            if ',' in data_url:
                base64_data = data_url.split(',')[1]
                with open(save_path, 'wb') as f:
                    f.write(base64.b64decode(base64_data))
                result['path'] = save_path
        
        return result
    
    async def inspect_dom(self, tab_id: int = None, selector: str = None, mode: str = 'summary', text: str = None) -> Dict:
        """
        DOMを調査する
        
        Args:
            tab_id: タブID（省略時はアクティブタブ）
            selector: 特定セレクター（指定時はその要素を詳細調査）
            mode: 調査モード
                - summary: ページ全体のサマリー（デフォルト）
                - interactive: インタラクティブ要素一覧
                - testids: data-testid属性を持つ要素一覧
                - tree: body直下の要素ツリー
                - aria: ARIA属性を持つ要素
                - search: テキスト検索（textパラメータ必須）
            text: 検索テキスト（mode='search'時に使用）
        
        Returns:
            調査結果
        """
        options = {'mode': mode}
        if text:
            options['text'] = text
        return await self._cmd(type='inspect_dom', tabId=tab_id, selector=selector, options=options)
    
    async def set_thinking(self, level: str, tab_id: int = None) -> Dict:
        """Thinking強度を設定"""
        return await self._cmd(type='chatgpt_set_thinking', level=level, tabId=tab_id)
    
    async def is_generating(self, tab_id: int = None) -> bool:
        """生成中かどうかを確認"""
        result = await self._cmd(type='chatgpt_is_generating', tabId=tab_id)
        return result.get('generating', False)
    
    async def get_response(self, tab_id: int = None, attached_files: List[str] = None) -> str:
        """回答を取得（本文のみ、確実に）
        
        Args:
            tab_id: タブID
            attached_files: 添付ファイルパスのリスト（ファイル名除去用）
        """
        # 専用コマンドを使用
        result = await self._cmd(type='chatgpt_get_response', tabId=tab_id)
        if result.get('success') and result.get('response'):
            response = result['response']
            # 添付ファイル名の引用マーカーを除去
            response = self._clean_file_citations(response, attached_files)
            return response
        
        # フォールバック1: .markdown
        result = await self.get_text('[data-message-author-role="assistant"] .markdown', tab_id)
        if result.get('texts'):
            valid = [t for t in result['texts'] if len(t) > 0]
            if valid:
                response = valid[-1]
                return self._clean_file_citations(response, attached_files)
        
        # フォールバック2: assistant全体
        result = await self.get_text('[data-message-author-role="assistant"]', tab_id)
        if result.get('texts'):
            response = result['texts'][-1]
            return self._clean_file_citations(response, attached_files)
        return ''
    
    def _clean_file_citations(self, text: str, attached_files: List[str] = None) -> str:
        """添付ファイル名の引用マーカーを除去
        
        ChatGPTはファイル添付時に回答内にファイル名のバッジ（filename）を挿入する。
        これらはinnerTextで取得すると「filename」というテキストとして混入するため除去する。
        
        パターン:
        - 「...接続できる状態」です。test_architecture」→「...接続できる状態」です。」
        - 段落末尾のインラインファイル名
        - 単独行のファイル名
        """
        import re
        
        if not text:
            return text
        
        # 添付ファイル名からパターンを生成
        if attached_files:
            from pathlib import Path
            
            for file_path in attached_files:
                filename = Path(file_path).name      # 例: test_architecture.md
                stem = Path(file_path).stem          # 例: test_architecture
                
                # 除去対象の名前リスト（長い順にソートして先にマッチ）
                names_to_remove = sorted([filename, stem], key=len, reverse=True)
                
                for name in names_to_remove:
                    escaped = re.escape(name)
                    
                    # パターン1: 句読点・閉じカッコの直後のファイル名
                    # 例: 「です。test_architecture」→「です。」
                    text = re.sub(
                        rf'([。、！？）\)」】\.,:;])\s*{escaped}(?=[\s\n「（\(]|$)',
                        r'\1',
                        text
                    )
                    
                    # パターン2: 単独行のファイル名
                    # 例: 「test_architecture\n」→ 空行
                    text = re.sub(
                        rf'^\s*{escaped}\s*$',
                        '',
                        text,
                        flags=re.MULTILINE
                    )
                    
                    # パターン3: 行末の孤立したファイル名（句読点なし）
                    # 例: 「〜を説明します test_architecture」→「〜を説明します」
                    text = re.sub(
                        rf'\s+{escaped}\s*$',
                        '',
                        text,
                        flags=re.MULTILINE
                    )
                    
                    # パターン4: 連続出現するファイル名
                    # 例: 「test_architecture test_architecture」→ 空白
                    text = re.sub(
                        rf'(\s*{escaped}\s*){{2,}}',
                        ' ',
                        text
                    )
                    
                    # パターン5: 文頭のファイル名（次に空白がある場合）
                    # 例: 「test_architecture この設計書では」→「この設計書では」
                    text = re.sub(
                        rf'^{escaped}\s+',
                        '',
                        text,
                        flags=re.MULTILINE
                    )
        
        # 連続空白・空行を正規化
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'^\s*\n', '\n', text, flags=re.MULTILINE)
        
        return text.strip()
    
    async def send_message(self, message: str, tab_id: int = None) -> Dict:
        """メッセージを送信（応答は待たない）"""
        # 入力欄の準備を待機（最大30秒）
        await self._wait_for_input_ready(tab_id, timeout=30)
        
        # Browser Controllerの専用送信コマンドを使用（UI変更に強い）
        last_error = None
        for _ in range(5):
            send_result = await self._cmd(type='chatgpt_send_message', message=message, tabId=tab_id)
            if send_result.get('success'):
                return {'success': True, 'message': message, 'tab_id': tab_id}
            last_error = send_result.get('error', 'Failed to send message')
            await asyncio.sleep(1.5)
        
        return {'success': False, 'error': last_error or 'Failed to send message'}
    
    async def _wait_for_input_ready(self, tab_id: int, timeout: int = 30) -> bool:
        """入力欄が利用可能になるまで待機"""
        selectors = [
            '#prompt-textarea',
            'div[contenteditable="true"][data-placeholder]',
            'div[contenteditable="true"]'
        ]
        start = time.time()
        
        while time.time() - start < timeout:
            for sel in selectors:
                result = await self._cmd(type='inspect_dom', tabId=tab_id, selector=sel)
                if result.get('matchCount', 0) > 0:
                    elements = result.get('elements', [])
                    if not elements or any(el.get('visible') for el in elements):
                        return True
            await asyncio.sleep(1.0)
        
        return False
    
    async def attach_file(self, file_path: str, tab_id: int = None) -> Dict:
        """ファイルを添付"""
        path = Path(file_path)
        if not path.exists():
            return {'success': False, 'error': f'File not found: {file_path}'}
        
        with open(path, 'rb') as f:
            file_data = base64.b64encode(f.read()).decode('utf-8')
        
        mime_type, _ = mimetypes.guess_type(str(path))
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        return await self._cmd(
            type='chatgpt_attach_file',
            fileData=file_data,
            fileName=path.name,
            mimeType=mime_type,
            tabId=tab_id
        )
    
    async def attach_files(self, file_paths: List[str], tab_id: int = None) -> List[Dict]:
        """複数ファイルを添付"""
        results = []
        for path in file_paths:
            result = await self.attach_file(path, tab_id)
            results.append({'path': path, **result})
            await asyncio.sleep(0.5)
        return results
    
    async def _wait_for_attachment_ready(self, tab_id: int, timeout: int = 30) -> bool:
        """ファイル添付が完了し送信可能になるまで待機（固定3秒待機）"""
        # ChatGPTの添付処理は通常1-3秒で完了するため、固定待機で対応
        await asyncio.sleep(3.0)
        return True
    
    # ========================================
    # 並列検索
    # ========================================
    
    async def parallel_search(
        self,
        questions: List[str],
        model: str = None,
        thinking: str = None,
        files: List[str] = None,
        close_tabs: bool = False
    ) -> List[Dict]:
        """
        複数の質問を並列で送信し、全ての応答を取得
        
        Args:
            questions: 質問リスト（3個以上必須、最大10個）
            model: 使用するモデル（例: 'ChatGPT 5.2 Thinking'）
            thinking: 推論強度（light/standard/heavy/extended）
            files: 添付するファイルパスのリスト（全タブに同じファイルを添付）
            close_tabs: 回答取得後にタブを閉じるか（デフォルト: False - マルチターン対応のため保持）
        
        Returns:
            各質問に対する結果のリスト
        """
        MAX_PARALLEL = 10
        MIN_PARALLEL = 3
        n = len(questions)
        
        if n < MIN_PARALLEL:
            print(f"Error: 'search' requires at least {MIN_PARALLEL} questions (opens {MIN_PARALLEL}+ sessions).")
            print("Use 'search1' for single-session search.")
            return [{
                'success': False,
                'error': f"search requires at least {MIN_PARALLEL} questions",
                'index': 0,
                'question': questions[0] if questions else '',
                'tab_id': None,
                'response': '',
                'elapsed': 0
            }]
        
        if n > MAX_PARALLEL:
            print(f"Warning: Maximum {MAX_PARALLEL} parallel queries allowed. Truncating from {n}.")
            questions = questions[:MAX_PARALLEL]
            n = MAX_PARALLEL
        
        print(f"\n{'='*60}")
        print(f"ChatGPT Parallel Search: {n} questions")
        print('='*60)
        if model:
            print(f"Model: {model}")
        if thinking:
            print(f"Thinking: {thinking}")
        if files:
            print(f"Files: {', '.join(files)}")
        print()
        
        # 1. タブを開く
        print(f"[1/4] Opening {n} ChatGPT tabs...")
        tab_ids = []
        for i in range(n):
            result = await self.new_tab('https://chatgpt.com/')
            if result.get('tab', {}).get('id'):
                tab_ids.append(result['tab']['id'])
                print(f"  Tab {i+1}: ID={result['tab']['id']}")
            await asyncio.sleep(1)
        
        if len(tab_ids) != n:
            return [{'success': False, 'error': f'Failed to open tabs: {len(tab_ids)}/{n}'}]
        
        print("  Waiting for pages to load...")
        await asyncio.sleep(3)
        
        # 2. モデル/Thinking設定
        if model:
            print(f"\n[1.5] Selecting model: {model}...")
            for i, tid in enumerate(tab_ids):
                r = await self.select_model(model, tid)
                status = "OK" if r.get('success') else f"FAIL: {r.get('error', '')}"
                print(f"  Tab {i+1}: {status}")
                await asyncio.sleep(0.5)
        
        if thinking:
            print(f"\n[1.6] Setting thinking: {thinking}...")
            for i, tid in enumerate(tab_ids):
                r = await self.set_thinking(thinking, tid)
                status = "OK" if r.get('success') else f"FAIL: {r.get('error', '')}"
                print(f"  Tab {i+1}: {status}")
                await asyncio.sleep(0.5)
        
        # 2.5 ファイル添付（オプション）
        if files:
            print(f"\n[1.7] Attaching files...")
            for i, tid in enumerate(tab_ids):
                for f in files:
                    r = await self.attach_file(f, tid)
                    status = "OK" if r.get('success') else f"FAIL: {r.get('error', '')}"
                    print(f"  Tab {i+1}: {Path(f).name} - {status}")
                
                # 添付完了まで待機（送信ボタンがenabledになるまで）
                print(f"  Tab {i+1}: Waiting for attachment ready...")
                ready = await self._wait_for_attachment_ready(tid)
                if ready:
                    print(f"  Tab {i+1}: Attachment ready")
                else:
                    print(f"  Tab {i+1}: Warning - attachment may not be ready")
        
        # 3. 質問を送信
        print(f"\n[2/4] Sending questions...")
        for i, (tid, q) in enumerate(zip(tab_ids, questions)):
            send_result = await self.send_message(q, tid)
            status = "OK" if send_result.get('success') else f"FAIL: {send_result.get('error', '')}"
            print(f"  Tab {i+1}: Sent '{q[:50]}...' ({status})")
            await asyncio.sleep(0.5)
        
        # 4. 回答を待機（非同期・各クエリごとに別MDファイル保存）
        print(f"\n[3/4] Waiting for responses (timeout: {self.timeout}s)...")
        
        topic = self._derive_topic_from_questions(questions)
        
        # 各クエリごとのMDファイルパスを生成
        md_paths = self._init_individual_mds(questions, model, thinking, topic=topic)
        print(f"[Output] Writing to {len(md_paths)} separate MD files:")
        for i, p in enumerate(md_paths):
            print(f"  Q{i+1}: {p}")
        
        results = [None] * n  # 結果格納用
        completed = [False] * n  # 完了フラグ
        
        async def wait_for_response(tid: int, idx: int, question: str) -> Dict:
            start = time.time()
            last_response = ""
            stable_count = 0
            MIN_RESPONSE_LEN = 100  # 最低回答長（短すぎる回答は完了とみなさない）
            STABLE_THRESHOLD = 4   # 安定判定回数（5秒 x 4 = 20秒）
            
            while True:
                elapsed = time.time() - start
                if elapsed > self.timeout:
                    url = await self._get_open_tab_url(tid)
                    result = {
                        'success': False, 'error': 'Timeout',
                        'index': idx, 'question': question, 'tab_id': tid,
                        'url': url,
                        'response': last_response, 'elapsed': elapsed
                    }
                    # タイムアウト時も個別MDに書き込み
                    self._write_individual_md(md_paths[idx], result)
                    results[idx] = result
                    completed[idx] = True
                    print(f"  Tab {idx+1}: Timeout ({elapsed:.1f}s)")
                    return result
                
                generating = await self.is_generating(tid)
                response = await self.get_response(tid, attached_files=files)
                
                if response and len(response) > 5:
                    if not generating:
                        if response == last_response:
                            stable_count += 1
                            # stable_count >= STABLE_THRESHOLD で安定確認
                            if stable_count >= STABLE_THRESHOLD:
                                # 回答が短すぎる場合は待機継続
                                if len(response) < MIN_RESPONSE_LEN:
                                    print(f"  Tab {idx+1}: Response too short ({len(response)} chars), waiting...")
                                    stable_count = 0
                                    await asyncio.sleep(self.poll_interval)
                                    continue
                                
                                # 完了確定後、DOM確定のため追加で3秒待機
                                print(f"  Tab {idx+1}: Finalizing response...")
                                await asyncio.sleep(3)
                                
                                # 最終取得（DOM完全確定後）
                                final_response = await self.get_response(tid, attached_files=files)
                                
                                # 最終取得で回答が変わっていたら、安定待機をリセット
                                if final_response and final_response != response:
                                    print(f"  Tab {idx+1}: Response still changing, resetting...")
                                    last_response = final_response
                                    stable_count = 0
                                    await asyncio.sleep(self.poll_interval)
                                    continue
                                
                                if final_response and len(final_response) >= len(response):
                                    response = final_response
                                
                                url = await self._get_open_tab_url(tid)
                                result = {
                                    'success': True, 'index': idx,
                                    'question': question, 'response': response,
                                    'tab_id': tid, 'url': url, 'elapsed': elapsed
                                }
                                # 取得した瞬間に個別MDに書き込み
                                self._write_individual_md(md_paths[idx], result)
                                results[idx] = result
                                completed[idx] = True
                                print(f"  Tab {idx+1}: Done ({elapsed:.1f}s) → {Path(md_paths[idx]).name}")
                                return result
                        else:
                            stable_count = 0
                    else:
                        stable_count = 0
                    last_response = response
                
                status = "Generating..." if generating else "Waiting..."
                print(f"  Tab {idx+1}: {status} ({int(elapsed)}s)")
                await asyncio.sleep(self.poll_interval)
        
        # 非同期で並列実行（各タスクが独立して完了）
        tasks = [asyncio.create_task(wait_for_response(tid, i, q)) 
                 for i, (tid, q) in enumerate(zip(tab_ids, questions))]
        
        # 全タスク完了を待つ
        await asyncio.gather(*tasks)
        
        # 5. 結果サマリー表示
        print(f"\n{'='*60}")
        print("[4/4] Summary")
        print('='*60)
        
        for r in results:
            if r is None:
                continue
            idx = r.get('index', 0)
            status = "OK" if r.get('success') else f"FAIL ({r.get('error')})"
            print(f"  Q{idx+1}: {status} ({r.get('elapsed', 0):.1f}s)")
        
        print(f"\n[Output] Saved to {len(md_paths)} files:")
        for p in md_paths:
            print(f"  - {p}")
        
        # 6.5 セッションタブを保存（マルチターン対応）
        if not close_tabs:
            session_entries = await self._build_session_entries(tab_ids, topic=topic)
            self._save_session_tabs(session_entries)
            print(f"\n[Session] Saved {len(tab_ids)} tabs for multi-turn conversation")
            print(f"  Use 'python chatgpt_multi.py chat -m \"your question\"' to continue")
        
        # 7. タブを閉じる（1往復のみの場合）
        if close_tabs:
            print(f"\n[Cleanup] Closing {len(tab_ids)} tabs...")
            for tid in tab_ids:
                await self.close_tab(tid)
            print("  Done.")
        
        return results
    
    # ========================================
    # 単一セッション検索（1タブで複数質問を順次送信）
    # ========================================
    
    async def single_session_search(
        self,
        questions: List[str],
        model: str = None,
        thinking: str = None,
        files: List[str] = None,
        tab_id: int = None,
        close_tab: bool = False
    ) -> List[Dict]:
        """単一タブで複数の質問を順次送信し、応答を取得
        
        Args:
            questions: 質問リスト（1個以上、最大10個）
            model: 使用するモデル
            thinking: 推論強度（light/standard/heavy/extended）
            files: 添付するファイルパスのリスト（このタブに添付）
            tab_id: 既存タブID（省略時は新規タブを作成）
            close_tab: 完了後にタブを閉じるか
        
        Returns:
            各質問に対する結果のリスト
        """
        MAX_QUERIES = 10
        n = len(questions)
        
        if n == 0:
            return [{'success': False, 'error': 'No questions provided'}]
        
        if n > MAX_QUERIES:
            print(f"Warning: Maximum {MAX_QUERIES} queries allowed. Truncating from {n}.")
            questions = questions[:MAX_QUERIES]
            n = MAX_QUERIES
        
        print(f"\n{'='*60}")
        print(f"ChatGPT Single-Session Search: {n} questions")
        print('='*60)
        if model:
            print(f"Model: {model}")
        if thinking:
            print(f"Thinking: {thinking}")
        if files:
            print(f"Files: {', '.join(files)}")
        print()
        
        # 1. タブを用意
        if tab_id is None:
            print("[1/4] Opening 1 ChatGPT tab...")
            new_tab_result = await self.new_tab('https://chatgpt.com/')
            tab_id = new_tab_result.get('tab', {}).get('id')
            if not tab_id:
                return [{'success': False, 'error': 'Failed to open tab'}]
            print(f"  Tab: ID={tab_id}")
            print("  Waiting for page to load...")
            await asyncio.sleep(3)
        else:
            print(f"[1/4] Using existing tab: ID={tab_id}")
        
        # 2. モデル/Thinking設定
        if model:
            print(f"\n[1.5] Selecting model: {model}...")
            r = await self.select_model(model, tab_id)
            status = "OK" if r.get('success') else f"FAIL: {r.get('error', '')}"
            print(f"  Tab: {status}")
        
        if thinking:
            print(f"\n[1.6] Setting thinking: {thinking}...")
            r = await self.set_thinking(thinking, tab_id)
            status = "OK" if r.get('success') else f"FAIL: {r.get('error', '')}"
            print(f"  Tab: {status}")
        
        # 2.5 ファイル添付（オプション）
        if files:
            print(f"\n[1.7] Attaching files...")
            for f in files:
                r = await self.attach_file(f, tab_id)
                status = "OK" if r.get('success') else f"FAIL: {r.get('error', '')}"
                print(f"  {Path(f).name} - {status}")
            print("  Waiting for attachment ready...")
            await self._wait_for_attachment_ready(tab_id)
            print("  Attachment ready")
        
        # 3. 質問送信 + 応答待機（順次）
        print(f"\n[2/4] Sending questions sequentially...")
        topic = self._derive_topic_from_questions(questions)
        md_paths = self._init_individual_mds(questions, model, thinking, topic=topic)
        print(f"[Output] Writing to {len(md_paths)} separate MD files:")
        for i, p in enumerate(md_paths):
            print(f"  Q{i+1}: {p}")
        
        results: List[Dict] = []
        
        for idx, question in enumerate(questions):
            print(f"\n[3/4] Q{idx+1}/{n}: {question[:60]}...")
            
            pre_result = await self._cmd(type='chatgpt_get_response', tabId=tab_id)
            pre_count = pre_result.get('responseCount', 0)
            
            send_result = await self.send_message(question, tab_id)
            if not send_result.get('success'):
                url = await self._get_open_tab_url(tab_id)
                result = {
                    'success': False,
                    'error': send_result.get('error', 'Send failed'),
                    'index': idx,
                    'question': question,
                    'tab_id': tab_id,
                    'url': url,
                    'response': '',
                    'elapsed': 0
                }
                self._write_individual_md(md_paths[idx], result)
                results.append(result)
                break
            
            start = time.time()
            last_response = ""
            stable_count = 0
            MIN_RESPONSE_LEN = 100
            STABLE_THRESHOLD = 4
            
            while True:
                elapsed = time.time() - start
                if elapsed > self.timeout:
                    url = await self._get_open_tab_url(tab_id)
                    result = {
                        'success': False,
                        'error': 'Timeout',
                        'index': idx,
                        'question': question,
                        'tab_id': tab_id,
                        'url': url,
                        'response': last_response,
                        'elapsed': elapsed
                    }
                    self._write_individual_md(md_paths[idx], result)
                    results.append(result)
                    print(f"  Q{idx+1}: Timeout ({elapsed:.1f}s)")
                    break
                
                generating = await self.is_generating(tab_id)
                response = await self.get_response(tab_id, attached_files=files)
                current_count = (await self._cmd(type='chatgpt_get_response', tabId=tab_id)).get('responseCount', 0)
                
                if current_count > pre_count and response and len(response) > 5:
                    if not generating:
                        if response == last_response:
                            stable_count += 1
                            if stable_count >= STABLE_THRESHOLD:
                                if len(response) < MIN_RESPONSE_LEN:
                                    stable_count = 0
                                    await asyncio.sleep(self.poll_interval)
                                    continue
                                
                                print("  Finalizing response...")
                                await asyncio.sleep(3)
                                
                                final_response = await self.get_response(tab_id, attached_files=files)
                                if final_response and final_response != response:
                                    last_response = final_response
                                    stable_count = 0
                                    await asyncio.sleep(self.poll_interval)
                                    continue
                                
                                if final_response and len(final_response) >= len(response):
                                    response = final_response
                                
                                url = await self._get_open_tab_url(tab_id)
                                result = {
                                    'success': True,
                                    'index': idx,
                                    'question': question,
                                    'response': response,
                                    'tab_id': tab_id,
                                    'url': url,
                                    'elapsed': elapsed
                                }
                                self._write_individual_md(md_paths[idx], result)
                                result['md_path'] = md_paths[idx]
                                results.append(result)
                                print(f"  Q{idx+1}: Done ({elapsed:.1f}s)")
                                break
                        else:
                            stable_count = 0
                    else:
                        stable_count = 0
                    last_response = response
                
                await asyncio.sleep(self.poll_interval)
        
        # 4. セッションタブを保存（chatコマンドで継続できるようにする）
        if not close_tab and tab_id:
            session_entries = await self._build_session_entries([tab_id], topic=topic)
            self._save_session_tabs(session_entries)
        
        if close_tab and tab_id:
            await self.close_tab(tab_id)
        
        return results
    
    def _get_flow_path(self, filename: str, topic: str = None) -> Path:
        """Flowディレクトリ内のパスを取得"""
        from datetime import datetime
        
        now = datetime.now()
        yymm = now.strftime("%Y%m")
        yyyymmdd = now.strftime("%Y-%m-%d")
        
        # Flowディレクトリを特定（スクリプトの場所から遡って探す）
        script_dir = Path(__file__).resolve().parent
        flow_dir = None
        
        for parent in script_dir.parents:
            candidate = parent / "Flow"
            if candidate.exists() and candidate.is_dir():
                flow_dir = candidate
                break
        
        if flow_dir is None:
            return Path(filename)
        
        day_dir = flow_dir / yymm / yyyymmdd
        day_dir.mkdir(parents=True, exist_ok=True)
        
        if topic:
            topic_dir = day_dir / self._sanitize_topic(topic)
            topic_dir.mkdir(parents=True, exist_ok=True)
            return topic_dir / filename
        
        return day_dir / filename
    
    def _init_results_md(self, questions: List[str], model: str = None, thinking: str = None) -> str:
        """MDファイルを初期化（ヘッダーのみ書き込み）"""
        from datetime import datetime
        
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        filename = f"chatgpt_search_{timestamp}.md"
        save_path = self._get_flow_path(filename)
        
        lines = [
            f"# ChatGPT Parallel Search Results",
            f"",
            f"**実行日時**: {now.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**モデル**: {model or 'ChatGPT 5.2 Thinking (default)'}",
            f"**Thinking**: {thinking or 'default'}",
            f"**質問数**: {len(questions)}",
            f"",
            "## 質問一覧",
            ""
        ]
        
        for i, q in enumerate(questions):
            lines.append(f"{i+1}. {q}")
        
        lines.extend(["", "---", "", "## 回答", ""])
        
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        
        return str(save_path)
    
    def _append_result_md(self, md_path: str, result: Dict) -> None:
        """MDファイルに結果を追記"""
        idx = result.get('index', 0) + 1
        question = result.get('question', '')
        success = result.get('success', False)
        elapsed = result.get('elapsed', 0)
        response = result.get('response', '')
        error = result.get('error', '')
        tab_id = result.get('tab_id', 'N/A')
        
        lines = [
            f"### Q{idx}: {question}",
            ""
        ]
        
        if success and response:
            lines.append(f"**ステータス**: OK ({elapsed:.1f}s)")
            lines.append("")
            lines.append(response)
        elif not success:
            lines.append(f"**ステータス**: FAIL - {error}")
            lines.append(f"**Tab ID**: {tab_id}")
            if response:
                lines.append("")
                lines.append(f"**部分回答**: {response[:500]}")
            else:
                lines.append("")
                lines.append("ERROR: 応答取得失敗 - 取得できた内容はありません")
            lines.append("")
            lines.append(f"**デバッグ**: 再取得: `python chatgpt_multi.py recover --tab {tab_id}` / 表示のみ: `python chatgpt_multi.py response --tab {tab_id}`")
        else:
            # successだが responseが空
            lines.append(f"**ステータス**: WARN - 応答が空です")
            lines.append(f"**Tab ID**: {tab_id}")
            lines.append("")
            lines.append("WARN: 応答が取得できませんでした")
            lines.append(f"**デバッグ**: 再取得: `python chatgpt_multi.py recover --tab {tab_id}` / 表示のみ: `python chatgpt_multi.py response --tab {tab_id}`")
        
        lines.extend(["", "---", ""])
        
        with open(md_path, 'a', encoding='utf-8') as f:
            f.write("\n".join(lines))
    
    def _init_individual_mds(self, questions: List[str], model: str = None, thinking: str = None, topic: str = None) -> List[str]:
        """各クエリごとのMDファイルを初期化し、パスリストを返す"""
        from datetime import datetime
        
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        md_paths = []
        
        for i, question in enumerate(questions):
            filename = f"chatgpt_q{i+1}_{timestamp}.md"
            save_path = self._get_flow_path(filename, topic)
            
            # ヘッダーを書き込み
            lines = [
                f"# ChatGPT Search Result - Q{i+1}",
                f"",
                f"**実行日時**: {now.strftime('%Y-%m-%d %H:%M:%S')}",
                f"**モデル**: {model or 'default'}",
                f"**Thinking**: {thinking or 'default'}",
                f"",
                f"## 質問",
                f"",
                f"{question}",
                f"",
                f"---",
                f"",
                f"## 回答",
                f"",
                f"(waiting...)",
                f""
            ]
            
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines))
            
            md_paths.append(str(save_path))
        
        return md_paths
    
    def _write_individual_md(self, md_path: str, result: Dict) -> None:
        """個別MDファイルに結果を書き込み（上書き）"""
        from datetime import datetime
        
        question = result.get('question', '')
        success = result.get('success', False)
        elapsed = result.get('elapsed', 0)
        response = result.get('response', '')
        error = result.get('error', '')
        tab_id = result.get('tab_id', 'N/A')
        
        url = result.get('url', '')
        
        lines = [
            f"# ChatGPT Search Result",
            f"",
            f"**実行日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**ステータス**: {'OK' if success else 'FAIL'}",
            f"**応答時間**: {elapsed:.1f}s",
            f"**Tab ID**: {tab_id}",
            f"**URL**: {url}" if url else "",
            f"",
            f"## 質問",
            f"",
            f"{question}",
            f"",
            f"---",
            f"",
            f"## 回答",
            f""
        ]
        
        if success and response:
            lines.append(response)
        elif not success:
            lines.append(f"ERROR: 応答取得失敗")
            lines.append(f"")
            lines.append(f"**エラー**: {error}")
            lines.append(f"")
            if response:
                lines.append(f"**部分回答**:")
                lines.append(f"```")
                lines.append(response[:500])
                lines.append(f"```")
            else:
                lines.append(f"**取得できた内容**: なし")
            lines.append(f"")
            lines.append(f"### デバッグ情報")
            lines.append(f"")
            lines.append(f"- ChatGPTのタブが正しく開いているか確認してください")
            lines.append(f"- ChatGPTでエラーメッセージが表示されていないか確認してください")
            lines.append(f"- Rate limit等の制限に達していないか確認してください")
            lines.append(f"- 手動でタブを確認: `python chatgpt_multi.py tabs`")
            lines.append(f"- 再取得: `python chatgpt_multi.py recover --tab {tab_id}`")
            lines.append(f"- 表示のみ: `python chatgpt_multi.py response --tab {tab_id}`")
        else:
            # successだが responseが空の場合
            lines.append(f"WARN: 応答が空です")
            lines.append(f"")
            lines.append(f"### デバッグ情報")
            lines.append(f"")
            lines.append(f"- ChatGPTが応答を生成中の可能性があります")
            lines.append(f"- 再取得: `python chatgpt_multi.py recover --tab {tab_id}`")
            lines.append(f"- 表示のみ: `python chatgpt_multi.py response --tab {tab_id}`")
            lines.append(f"- タブを確認: `python chatgpt_multi.py tabs`")
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
    
    # ========================================
    # 単一チャット
    # ========================================
    
    async def close(self):
        """WebSocket接続を閉じる"""
        if self._ws:
            await self._ws.close()
            self._ws = None
    
    async def recover(self, tab_id: int = None, url: str = None, files: List[str] = None) -> Dict:
        """タブIDまたは会話URLを指定して内容を再取得してMDに保存
        
        まれにChatGPT側では回答が出ているのに受け取り側の一時エラーで取得できないことがあるため、
        タブIDを指定して再取得できるようにする。

        また、セッションファイルが無い/タブIDが分からない場合に備え、会話URL（chatgpt.com/c/...）から
        タブを開いて再取得できるようにする。
        """
        # URL指定の場合は、URLでタブを開いて取得
        if url:
            topic = self._derive_topic_from_message(url)
            result = await self.new_tab(url)
            new_id = result.get('tab', {}).get('id')
            if not new_id:
                result_dict = {
                    'success': False,
                    'error': 'Failed to open tab from URL',
                    'response': '',
                    'elapsed': 0,
                    'tab_id': None,
                    'url': url,
                    'topic': topic,
                    'question': f"[RECOVER] URL {url}"
                }
                md_path = self._save_chat_response(result_dict, result_dict['question'], files)
                result_dict['md_path'] = md_path
                return result_dict
            
            await asyncio.sleep(3)
            opened_url = await self._get_open_tab_url(new_id) or url
            result_dict = await self.recover(tab_id=new_id, url=None, files=files)
            # URLとtopicを上書きしてMDにも残す
            result_dict['url'] = opened_url
            result_dict['topic'] = result_dict.get('topic') or topic
            return result_dict
        
        if tab_id is None:
            return {
                'success': False,
                'error': 'Either --tab or --url is required',
                'response': '',
                'elapsed': 0,
                'tab_id': None,
                'question': '[RECOVER]'
            }
        
        requested_tab_id = tab_id
        topic = self._get_session_tab_topic(tab_id) or 'recover'
        url = await self._get_open_tab_url(tab_id)
        
        # タブが閉じている場合は、セッションに保存されたURLから再オープン
        if not url:
            saved_url = self._get_session_tab_url(tab_id)
            if saved_url:
                print("[Recover] Tab is not open. Reopening from saved URL...")
                result = await self.new_tab(saved_url)
                new_id = result.get('tab', {}).get('id')
                if not new_id:
                    result_dict = {
                        'success': False,
                        'error': 'Failed to reopen tab',
                        'response': '',
                        'elapsed': 0,
                        'tab_id': requested_tab_id,
                        'url': saved_url,
                        'topic': topic,
                        'question': f"[RECOVER] Tab {requested_tab_id}"
                    }
                    md_path = self._save_chat_response(result_dict, result_dict['question'], files)
                    result_dict['md_path'] = md_path
                    return result_dict
                
                await asyncio.sleep(3)
                url = await self._get_open_tab_url(new_id) or saved_url
                
                # セッション情報を更新（tab_idを差し替え）
                for entry in self._session_tabs:
                    if entry.get('id') == requested_tab_id:
                        entry['id'] = new_id
                        entry['url'] = url
                        self._save_session_tabs(self._session_tabs)
                        break
                
                tab_id = new_id
            else:
                result_dict = {
                    'success': False,
                    'error': 'Tab is not open and no URL found in session file',
                    'response': '',
                    'elapsed': 0,
                    'tab_id': requested_tab_id,
                    'topic': topic,
                    'question': f"[RECOVER] Tab {requested_tab_id}"
                }
                md_path = self._save_chat_response(result_dict, result_dict['question'], files)
                result_dict['md_path'] = md_path
                return result_dict
        
        question = f"[RECOVER] Tab {requested_tab_id}"
        start = time.time()
        last_response = ""
        stable_count = 0
        MIN_RESPONSE_LEN = 100
        STABLE_THRESHOLD = 4
        
        while True:
            elapsed = time.time() - start
            if elapsed > self.timeout:
                result_dict = {
                    'success': False,
                    'error': 'Timeout',
                    'response': last_response,
                    'elapsed': elapsed,
                    'tab_id': tab_id,
                    'url': url,
                    'topic': topic,
                    'question': question
                }
                md_path = self._save_chat_response(result_dict, question, files)
                result_dict['md_path'] = md_path
                return result_dict
            
            generating = await self.is_generating(tab_id)
            response = await self.get_response(tab_id, attached_files=files)
            
            if response and len(response) > 5:
                if not generating:
                    if response == last_response:
                        stable_count += 1
                        if stable_count >= STABLE_THRESHOLD:
                            if len(response) < MIN_RESPONSE_LEN:
                                stable_count = 0
                                await asyncio.sleep(self.poll_interval)
                                continue
                            
                            await asyncio.sleep(3)
                            final_response = await self.get_response(tab_id, attached_files=files)
                            if final_response and final_response != response:
                                last_response = final_response
                                stable_count = 0
                                await asyncio.sleep(self.poll_interval)
                                continue
                            
                            if final_response and len(final_response) >= len(response):
                                response = final_response
                            
                            result_dict = {
                                'success': True,
                                'response': response,
                                'elapsed': elapsed,
                                'tab_id': tab_id,
                                'url': url,
                                'question': question
                            }
                            md_path = self._save_chat_response(result_dict, question, files)
                            result_dict['md_path'] = md_path
                            return result_dict
                    else:
                        stable_count = 0
                else:
                    stable_count = 0
                last_response = response
            
            await asyncio.sleep(self.poll_interval)
     
    async def chat(self, messages: List[str], tab_id: int = None, wait: bool = True, files: List[str] = None) -> List[Dict]:
        """
        複数のメッセージを同じセッションに順次送信（マルチターン用）
        
        Args:
            messages: 送信するメッセージのリスト（単一文字列も受け入れ可能）
            tab_id: タブID（省略時はセッションタブから自動選択）
            wait: 応答を待つかどうか
            files: 添付ファイルパスのリスト（ファイル名除去用）
        
        Returns:
            結果のリスト（各応答含む、MDファイルパスを含む）
        """
        # 下位互換性: 単一文字列の場合はリストに変換
        if isinstance(messages, str):
            messages = [messages]
        
        # タブIDが指定されていない場合、セッションタブから自動選択
        if tab_id is None:
            tab_id = await self.get_active_session_tab()
            if tab_id is None:
                return [{
                    'success': False, 
                    'error': 'No session tabs found. Run parallel_search first or specify --tab option.',
                    'response': '',
                    'question': messages[0] if messages else ''
                }]
            print(f"[Session] Using tab ID: {tab_id}")
        
        # 指定されたタブが閉じている場合は、セッションURLから再オープン
        open_url = await self._get_open_tab_url(tab_id)
        if not open_url:
            saved_url = self._get_session_tab_url(tab_id)
            if saved_url:
                print("[Session] Tab is not open. Reopening from saved URL...")
                result = await self.new_tab(saved_url)
                new_id = result.get('tab', {}).get('id')
                if new_id:
                    await asyncio.sleep(3)
                    current_url = await self._get_open_tab_url(new_id) or saved_url
                    for entry in self._session_tabs:
                        if entry.get('id') == tab_id:
                            entry['id'] = new_id
                            entry['url'] = current_url
                            self._save_session_tabs(self._session_tabs)
                            break
                    tab_id = new_id
            
        topic = self._get_session_tab_topic(tab_id)
        if not topic:
            topic = self._derive_topic_from_message(messages[0] if messages else 'untitled')
            for entry in self._session_tabs:
                if entry.get('id') == tab_id:
                    entry['topic'] = topic
                    self._save_session_tabs(self._session_tabs)
                    break
        
        # 各メッセージを順次送信
        results = []
        for i, message in enumerate(messages, 1):
            print(f"\n[Chat {i}/{len(messages)}] Sending: {message[:60]}...")
            result = await self._chat_single(message, tab_id, wait, files, topic=topic)
            results.append(result)
            
            if not result.get('success'):
                print(f"[Chat {i}/{len(messages)}] Failed: {result.get('error')}")
                # エラー時は以降のメッセージをスキップ
                break
            else:
                print(f"[Chat {i}/{len(messages)}] Success ({result.get('elapsed', 0):.1f}s)")
        
        return results
    
    async def _chat_single(self, message: str, tab_id: int, wait: bool = True, files: List[str] = None, topic: str = None) -> Dict:
        """
        単一のメッセージを送信（内部用）
        
        Args:
            message: 送信するメッセージ
            tab_id: タブID
            wait: 応答を待つかどうか
            files: 添付ファイルパスのリスト（ファイル名除去用）
        
        Returns:
            結果（応答含む、MDファイルパスを含む）
        """
        # 送信前の回答数を記録
        pre_result = await self._cmd(type='chatgpt_get_response', tabId=tab_id)
        pre_count = pre_result.get('responseCount', 0)
        
        send_result = await self.send_message(message, tab_id)
        if not send_result.get('success'):
            return send_result
        
        if not wait:
            return send_result
        
        # 応答を待機（新しい回答が追加されるまで）
        start = time.time()
        last_response = ""
        stable_count = 0
        MIN_RESPONSE_LEN = 100
        STABLE_THRESHOLD = 4  # 20秒安定
        
        while True:
            elapsed = time.time() - start
            if elapsed > self.timeout:
                url = await self._get_open_tab_url(tab_id)
                if url:
                    for entry in self._session_tabs:
                        if entry.get('id') == tab_id and entry.get('url') != url:
                            entry['url'] = url
                            self._save_session_tabs(self._session_tabs)
                            break
                result_dict = {'success': False, 'error': 'Timeout', 'response': last_response, 
                              'elapsed': elapsed, 'tab_id': tab_id, 'url': url, 'topic': topic, 'question': message}
                # タイムアウト時もMD保存
                md_path = self._save_chat_response(result_dict, message, files)
                result_dict['md_path'] = md_path
                return result_dict
            
            generating = await self.is_generating(tab_id)
            response = await self.get_response(tab_id, attached_files=files)
            current_count = (await self._cmd(type='chatgpt_get_response', tabId=tab_id)).get('responseCount', 0)
            
            # 新しい回答が追加されている場合
            if current_count > pre_count and len(response) > 5:
                if not generating:
                    if response == last_response:
                        stable_count += 1
                        if stable_count >= STABLE_THRESHOLD:
                            # 短すぎる回答は待機継続
                            if len(response) < MIN_RESPONSE_LEN:
                                stable_count = 0
                                await asyncio.sleep(self.poll_interval)
                                continue
                            
                            # DOM確定待機
                            await asyncio.sleep(3)
                            
                            # 最終取得
                            final_response = await self.get_response(tab_id, attached_files=files)
                            if final_response and final_response != response:
                                last_response = final_response
                                stable_count = 0
                                await asyncio.sleep(self.poll_interval)
                                continue
                            
                            if final_response and len(final_response) >= len(response):
                                response = final_response
                            
                            url = await self._get_open_tab_url(tab_id)
                            if url:
                                for entry in self._session_tabs:
                                    if entry.get('id') == tab_id and entry.get('url') != url:
                                        entry['url'] = url
                                        self._save_session_tabs(self._session_tabs)
                                        break
                            result_dict = {'success': True, 'response': response, 'elapsed': elapsed,
                                          'tab_id': tab_id, 'url': url, 'topic': topic, 'question': message}
                            # MD保存
                            md_path = self._save_chat_response(result_dict, message, files)
                            result_dict['md_path'] = md_path
                            return result_dict
                    else:
                        stable_count = 0
                else:
                    stable_count = 0
                last_response = response
            
            await asyncio.sleep(self.poll_interval)
    
    def _save_chat_response(self, result: Dict, question: str, files: List[str] = None) -> str:
        """chatコマンドの回答をMDファイルに保存
        
        Args:
            result: 回答結果
            question: 送信した質問
            files: 添付ファイルリスト
        
        Returns:
            保存したMDファイルのパス
        """
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        tab_id = result.get('tab_id', 'unknown')
        topic = result.get('topic')
        if not topic:
            topic = self._derive_topic_from_message(question)
        
        filename = f"chatgpt_chat_tab{tab_id}_{timestamp}.md"
        md_path = self._get_flow_path(filename, topic=topic)
        
        success = result.get('success', False)
        response = result.get('response', '')
        error = result.get('error', '')
        url = result.get('url', '')
        
        lines = [
            f"# ChatGPT Chat Response",
            f"",
            f"**Tab ID**: {tab_id}",
            f"**URL**: {url}" if url else "",
            f"**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Elapsed**: {result.get('elapsed', 0):.1f}s",
            f"**Status**: {'Success' if success else 'Failed'}",
        ]
        
        if files:
            lines.append(f"**Attached Files**: {', '.join(files)}")
        
        lines.extend([
            f"",
            f"## Question",
            f"",
            question,
            f"",
            f"## Response",
            f"",
        ])
        
        if success and response:
            lines.append(response)
        elif not success:
            lines.append(f"ERROR: 応答取得失敗")
            lines.append(f"")
            lines.append(f"**エラー**: {error}")
            lines.append(f"")
            if response:
                lines.append(f"**部分回答**:")
                lines.append(f"```")
                lines.append(response[:500])
                lines.append(f"```")
            else:
                lines.append(f"**取得できた内容**: なし")
            lines.append(f"")
            lines.append(f"### デバッグ情報")
            lines.append(f"")
            lines.append(f"- ChatGPTのタブが正しく開いているか確認してください")
            lines.append(f"- ChatGPTでエラーメッセージが表示されていないか確認してください")
            lines.append(f"- Rate limit等の制限に達していないか確認してください")
            lines.append(f"- 手動でタブを確認: `python chatgpt_multi.py tabs`")
            lines.append(f"- 再取得: `python chatgpt_multi.py recover --tab {tab_id}`")
            lines.append(f"- 表示のみ: `python chatgpt_multi.py response --tab {tab_id}`")
        else:
            # successだが responseが空の場合
            lines.append(f"WARN: 応答が空です")
            lines.append(f"")
            lines.append(f"### デバッグ情報")
            lines.append(f"")
            lines.append(f"- ChatGPTが応答を生成中の可能性があります")
            lines.append(f"- 再取得: `python chatgpt_multi.py recover --tab {tab_id}`")
            lines.append(f"- 表示のみ: `python chatgpt_multi.py response --tab {tab_id}`")
            lines.append(f"- タブを確認: `python chatgpt_multi.py tabs`")
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        
        return str(md_path)


# ========================================
# CLI
# ========================================

def run_bridge_only():
    """ブリッジサーバーのみをフォアグラウンドで起動"""
    server = BridgeServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("\n[Bridge] Stopped")


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='ChatGPT Parallel Research Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # === ChatGPT ===
  # 並列検索（3並列以上必須）
  python chatgpt_multi.py "質問1" "質問2" "質問3"
  
  # Heavy thinkingで難問を解く
  python chatgpt_multi.py "難問1" "難問2" "難問3" --thinking heavy
  
  # ファイル添付して並列分析
  python chatgpt_multi.py "技術分析して" "ビジネス価値を評価" "改善案を10個" --files doc.pdf
  
  # 単一セッション検索（1タブで複数質問を順次送信）
  python chatgpt_multi.py search1 "質問1" "質問2"
  
  # タブ一覧
  python chatgpt_multi.py tabs
  
  # モデル一覧
  python chatgpt_multi.py models
  
  # 単一チャット（自動セッション選択）
  python chatgpt_multi.py chat -m "質問内容"
  
  # マルチターン（複数質問を同じセッションに順次送信）
  python chatgpt_multi.py chat -m "追加質問1" "追加質問2" "追加質問3"
  
  # 再取得（受け取り側エラー時など）
  python chatgpt_multi.py recover --tab 123
  
  # 会話URLから再取得（セッションが無い場合など）
  python chatgpt_multi.py recover --url "https://chatgpt.com/c/xxxx"
  
  # === 共通 ===
  # ブリッジサーバーのみ起動
  python chatgpt_multi.py bridge
  
  # 接続状態確認
  python chatgpt_multi.py status
"""
    )
    
    parser.add_argument('command', nargs='?', default='search',
                        help='Command: search, search1, tabs, models, thinking, attach, chat, recover, response, bridge')
    parser.add_argument('questions', nargs='*', help='Questions for parallel search')
    parser.add_argument('--timeout', type=int, default=1800,
                        help='Timeout in seconds (fixed at 1800; option ignored)')
    parser.add_argument('--interval', type=int, default=5, help='Poll interval in seconds')
    parser.add_argument('--thinking', '-t', help='Thinking level: light/standard/heavy/extended')
    parser.add_argument('--model', help='Model to use')
    parser.add_argument('--files', nargs='+', help='Files to attach')
    parser.add_argument('--file', '-f', help='Single file to attach')
    parser.add_argument('--tab', type=int, help='Tab ID')
    parser.add_argument('--url', help='Conversation URL (for recover)')
    parser.add_argument('--message', '-m', nargs='+', help='Message(s) for chat command (multiple messages will be sent sequentially)')
    parser.add_argument('--level', '-l', help='Thinking level to set')
    parser.add_argument('--no-auto-bridge', action='store_true', 
                        help='Disable automatic bridge server startup')
    parser.add_argument('--close-tabs', action='store_true',
                        help='Close tab(s) after operation (search/search1/chat/recover)')
    parser.add_argument('--keep-tabs', action='store_true',
                        help='(Deprecated: tabs are kept by default) Keep tabs open after search')
    
    args = parser.parse_args()
    
    # タイムアウトは固定（30分）
    fixed_timeout = 1800
    if args.timeout != fixed_timeout:
        print(f"[Info] Timeout is fixed at {fixed_timeout}s. Ignoring provided value: {args.timeout}")
    args.timeout = fixed_timeout
    
    # 既知のコマンド一覧
    KNOWN_COMMANDS = [
        'search', 'search1', 'tabs', 'models', 'thinking', 'set-thinking', 'enable-pro',
        'is-pro', 'set-mode', 'attach', 'chat', 'recover', 'response', 'debug-dropdown',
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
    
    ctrl = ChatGPTController(
        timeout=args.timeout, 
        poll_interval=args.interval,
        auto_bridge=not args.no_auto_bridge
    )
    
    # questionsがあればsearch/search1コマンド
    if args.questions and cmd == 'search':
        if len(args.questions) < 3:
            print("Error: 'search' requires at least 3 questions (opens 3+ sessions).")
            print("Use 'search1' for single-session search.")
            return
        
        results = await ctrl.parallel_search(
            args.questions,
            model=args.model,
            thinking=args.thinking,
            files=args.files,
            close_tabs=args.close_tabs  # デフォルトでタブを保持（False）
        )
        print("\n=== Summary ===")
        for r in results:
            status = "OK" if r.get('success') else "FAIL"
            print(f"[{status}] Q{r.get('index', 0)+1}: {r.get('elapsed', 0):.1f}s")
    
    elif args.questions and cmd == 'search1':
        results = await ctrl.single_session_search(
            args.questions,
            model=args.model,
            thinking=args.thinking,
            files=args.files,
            tab_id=args.tab,
            close_tab=args.close_tabs
        )
        print("\n=== Summary ===")
        for r in results:
            status = "OK" if r.get('success') else "FAIL"
            print(f"[{status}] Q{r.get('index', 0)+1}: {r.get('elapsed', 0):.1f}s")
    
    elif cmd == 'recover':
        if not args.tab and not args.url:
            print("Error: --tab or --url required")
            return
        files = getattr(args, 'files', None)
        result = await ctrl.recover(tab_id=args.tab, url=args.url, files=files)
        if result.get('success'):
            print(f"\n[Recovered] ({result.get('elapsed', 0):.1f}s)")
            print(result.get('response', ''))
            md_path = result.get('md_path')
            if md_path:
                print(f"\n[Saved] {md_path}")
        else:
            print(f"Error: {result.get('error')}")
            md_path = result.get('md_path')
            if md_path:
                print(f"\n[Saved] {md_path}")
        
        if args.close_tabs:
            effective_tab_id = result.get('tab_id')
            if effective_tab_id:
                await ctrl.close_tab(effective_tab_id)
    
    elif cmd == 'tabs':
        tabs = await ctrl.get_tabs()
        print(f"Open tabs: {len(tabs)}")
        for t in tabs:
            marker = '*' if t.get('active') else ' '
            print(f" {marker} [{t['id']}] {t.get('title', '')[:60]}")
            print(f"     {t.get('url', '')[:70]}")
    
    elif cmd == 'models':
        result = await ctrl.get_models(args.tab)
        print(f"Current model: {result.get('currentModel', 'Unknown')}")
        if result.get('models'):
            print("\nAvailable models:")
            for m in result['models']:
                print(f"  - {m.get('name', m)}")
    
    elif cmd == 'thinking':
        result = await ctrl.get_thinking(args.tab)
        print(f"Current thinking: {result.get('currentLevel', 'Unknown')}")
        if result.get('levels'):
            print("\nAvailable levels:")
            for l in result['levels']:
                sel = " (selected)" if l.get('selected') else ""
                print(f"  - {l.get('name', l)}{sel}")
    
    elif cmd == 'set-thinking':
        level = args.level or args.thinking
        if not level:
            print("Error: --level or --thinking required")
            return
        result = await ctrl.set_thinking(level, args.tab)
        if result.get('success'):
            print(f"Thinking set to: {result.get('selectedLevel', level)}")
        else:
            print(f"Error: {result.get('error')}")
    
    elif cmd == 'enable-pro':
        # Pro Modeを有効化
        result = await ctrl.enable_pro(args.tab)
        if result.get('success'):
            print(f"[Pro Mode] Enabled successfully")
            if result.get('selectedMode'):
                print(f"  Mode: {result.get('selectedMode')}")
        else:
            print(f"[Pro Mode] Failed: {result.get('error', 'Unknown error')}")
    
    elif cmd == 'is-pro':
        # Pro Mode状態を確認
        result = await ctrl.is_pro(args.tab)
        if result.get('success'):
            is_pro = result.get('isPro', False)
            current = result.get('currentMode', 'unknown')
            print(f"[Pro Mode] {'ENABLED' if is_pro else 'DISABLED'}")
            print(f"  Current mode: {current}")
        else:
            print(f"[Pro Mode] Check failed: {result.get('error', 'Unknown error')}")
    
    elif cmd == 'set-mode':
        # モード切り替え（auto/instant/thinking/pro）
        mode = args.questions[0] if args.questions else None
        if not mode:
            print("Usage: python chatgpt_multi.py set-mode <mode>")
            print("  Modes: auto, instant, thinking, pro")
            return
        
        valid_modes = ['auto', 'instant', 'thinking', 'pro']
        if mode.lower() not in valid_modes:
            print(f"Error: Invalid mode '{mode}'")
            print(f"  Valid modes: {', '.join(valid_modes)}")
            return
        
        result = await ctrl.set_mode(mode.lower(), args.tab)
        if result.get('success'):
            print(f"[Mode] Set to: {result.get('selectedMode', mode)}")
        else:
            print(f"[Mode] Failed: {result.get('error', 'Unknown error')}")
    
    elif cmd == 'attach':
        file_path = args.file
        if not file_path:
            print("Error: --file required")
            return
        result = await ctrl.attach_file(file_path, args.tab)
        if result.get('success'):
            print(f"Attached: {result.get('fileName')} ({result.get('fileSize')} bytes)")
        else:
            print(f"Error: {result.get('error')}")
    
    elif cmd == 'chat':
        messages = args.message
        if not messages:
            print("Error: --message / -m required")
            return
        # ファイル添付情報を取得（args.filesがあれば）
        files = getattr(args, 'files', None)
        results = await ctrl.chat(messages, args.tab, files=files)
        
        # 結果を表示
        for i, result in enumerate(results, 1):
            if result.get('success'):
                print(f"\n[Response {i}/{len(results)}] ({result.get('elapsed', 0):.1f}s)")
                print(result.get('response', ''))
                md_path = result.get('md_path')
                if md_path:
                    print(f"[Saved] {md_path}")
            else:
                print(f"\n[Error {i}/{len(results)}] {result.get('error')}")
                md_path = result.get('md_path')
                if md_path:
                    print(f"[Saved] {md_path}")
        
        # サマリー表示（複数メッセージの場合）
        if len(results) > 1:
            success_count = sum(1 for r in results if r.get('success'))
            print(f"\n=== Summary ===")
            print(f"Total: {len(results)}, Success: {success_count}, Failed: {len(results) - success_count}")
        
        # 追加質問が終わったらタブを閉じる（任意）
        if args.close_tabs:
            effective_tab_id = args.tab
            if effective_tab_id is None and results:
                effective_tab_id = results[-1].get('tab_id')
            if effective_tab_id:
                await ctrl.close_tab(effective_tab_id)
    
    elif cmd == 'response':
        # 既存タブから回答を取得
        response = await ctrl.get_response(args.tab)
        if response:
            print(response)
        else:
            print("No response found")
    
    elif cmd == 'debug-dropdown' or cmd == 'dd':
        # ドロップダウンを開いてdata-testid一覧を取得（デバッグ用）
        result = await ctrl.debug_dropdown(args.tab)
        if result.get('success'):
            print(f"=== Model Selector Button ===")
            print(f"  Current: {result.get('buttonText', 'unknown')}")
            
            menu_info = result.get('menuInfo', {})
            print(f"\n=== Dropdown Detection ===")
            print(f"  role='menu': {menu_info.get('roleMenu', False)}")
            print(f"  role='listbox': {menu_info.get('roleListbox', False)}")
            print(f"  [popover]: {menu_info.get('popover', False)}")
            print(f"  [data-radix-popper]: {menu_info.get('radixPopper', False)}")
            print(f"  aria-expanded (before→after): {menu_info.get('ariaExpandedBefore')} → {menu_info.get('ariaExpandedAfter')}")
            
            if menu_info.get('found'):
                print(f"\n=== Active Menu Element ===")
                print(f"  Parent: {menu_info.get('parentTag', 'unknown')}")
                print(f"  Children: {menu_info.get('childCount', 0)}")
                print(f"  Class: {menu_info.get('className', '')[:80]}")
            
            menu_html = result.get('menuHTML')
            if menu_html:
                print(f"\n=== Menu HTML (first 300 chars) ===")
                print(f"  {menu_html[:300]}...")
            
            print(f"\n=== Menu Items ({result.get('menuItemCount', 0)} items) ===")
            for item in result.get('menuItems', []):
                testid = item.get('testId') or '(no testId)'
                tag = item.get('tag', '')
                print(f"  [{tag}] {testid}: {item.get('text', '')}")
            
            print(f"\n=== Switcher Elements ({result.get('switcherCount', 0)} items) ===")
            for item in result.get('switcherElements', []):
                role = item.get('role') or 'no-role'
                print(f"  [{role}] {item.get('testId')}: {item.get('text', '')}")
            
            body_children = result.get('bodyLastChildren', [])
            if body_children:
                print(f"\n=== Body Last Children ({len(body_children)} items) ===")
                for child in body_children:
                    mi_count = child.get('hasMenuitem', 0)
                    print(f"  <{child.get('tag')}> role={child.get('role')} menuitems={mi_count} class={child.get('className', '')[:40]}")
        else:
            print(f"Error: {result.get('error')}")
    
    elif cmd == 'screenshot' or cmd == 'ss':
        # スクリーンショットを撮影
        # デフォルトの保存先
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_path = f'/tmp/screenshot_{timestamp}.png'
        save_path = args.file or default_path
        
        result = await ctrl.screenshot(args.tab, save_path)
        if result.get('success'):
            print(f"[Screenshot] Saved to: {result.get('path', save_path)}")
            print(f"  Tab: {result.get('title', '')}")
            print(f"  URL: {result.get('url', '')}")
        else:
            print(f"[Screenshot] Failed: {result.get('error')}")
    
    elif cmd == 'screenshot-dropdown' or cmd == 'ssd':
        # ドロップダウンを開いた状態でスクリーンショット
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_path = f'/tmp/screenshot_dropdown_{timestamp}.png'
        save_path = args.file or default_path
        
        result = await ctrl.screenshot_dropdown(args.tab, save_path)
        if result.get('success'):
            print(f"[Screenshot Dropdown] Saved to: {result.get('path', save_path)}")
            print(f"  Tab: {result.get('title', '')}")
            print(f"  URL: {result.get('url', '')}")
        else:
            print(f"[Screenshot Dropdown] Failed: {result.get('error')}")
    
    elif cmd == 'inspect' or cmd == 'dom':
        # DOM調査
        # モードを引数から取得
        mode = 'summary'
        selector = None
        search_text = None
        
        # 引数解析（args.questionsから取得）
        if hasattr(args, 'questions') and args.questions:
            first_arg = args.questions[0] if args.questions else None
            if first_arg in ['summary', 'interactive', 'testids', 'tree', 'aria', 'search']:
                mode = first_arg
                if mode == 'search' and len(args.questions) > 1:
                    search_text = args.questions[1]
            elif first_arg and first_arg.startswith(('[', '.', '#', '*', 'button')):
                # セレクターっぽい場合
                selector = first_arg
            elif first_arg:
                # テキスト検索として扱う
                mode = 'search'
                search_text = first_arg
        
        result = await ctrl.inspect_dom(args.tab, selector, mode, search_text)
        
        if result.get('success'):
            print(f"=== DOM Inspection: {result.get('url', '')} ===")
            print(f"  Title: {result.get('title', '')}")
            
            # 特定セレクターの結果
            if selector and 'elements' in result:
                print(f"\n=== Selector: {selector} ({result.get('matchCount', 0)} matches) ===")
                for el in result.get('elements', []):
                    vis = 'visible' if el.get('visible') else 'hidden'
                    print(f"  [{el.get('index')}] <{el.get('tag')}> {vis} id={el.get('id')} class={el.get('className', '')[:50]}")
                    print(f"      text: {el.get('text', '')[:80]}")
                    attrs = el.get('attributes', {})
                    important_attrs = ['data-testid', 'role', 'aria-expanded', 'aria-haspopup']
                    attr_str = ' '.join([f"{k}={attrs[k]}" for k in important_attrs if k in attrs])
                    if attr_str:
                        print(f"      attrs: {attr_str}")
            
            # サマリー結果
            if 'summary' in result:
                s = result['summary']
                print(f"\n=== Page Summary ===")
                print(f"  Total elements: {s.get('totalElements', 0)}")
                print(f"  Buttons: {s.get('buttons', 0)}, Links: {s.get('links', 0)}, Inputs: {s.get('inputs', 0)}")
                print(f"  role='menu': {s.get('roleMenus', 0)}, role='menuitem': {s.get('roleMenuitems', 0)}")
                print(f"  role='dialog': {s.get('roleDialogs', 0)}, role='button': {s.get('roleButtons', 0)}")
                print(f"  data-testid: {s.get('dataTestIds', 0)}, contenteditable: {s.get('contentEditables', 0)}")
                print(f"  aria-expanded: {s.get('ariaExpanded', 0)}, aria-haspopup: {s.get('ariaHaspopup', 0)}")
            
            # インタラクティブ要素
            if 'interactive' in result:
                print(f"\n=== Interactive Elements ({len(result['interactive'])}) ===")
                for el in result.get('interactive', [])[:50]:
                    disabled = '[disabled]' if el.get('disabled') else ''
                    testid = f"testid={el.get('testId')}" if el.get('testId') else ''
                    exp = f"expanded={el.get('ariaExpanded')}" if el.get('ariaExpanded') else ''
                    print(f"  [{el.get('index')}] <{el.get('tag')}> {el.get('text', '')[:40]} {testid} {exp} {disabled}")
            
            # data-testid一覧
            if 'testIds' in result:
                print(f"\n=== data-testid Elements ({len(result['testIds'])}) ===")
                for el in result.get('testIds', []):
                    print(f"  [{el.get('tag')}] {el.get('testId')}: {el.get('text', '')[:50]}")
            
            # ツリー
            if 'tree' in result:
                print(f"\n=== Body Children ({len(result['tree'])}) ===")
                for el in result.get('tree', []):
                    print(f"  <{el.get('tag')}> id={el.get('id')} role={el.get('role')} children={el.get('childCount')} menuitems={el.get('hasMenuitem')} testids={el.get('hasTestId')}")
            
            # ARIA要素
            if 'ariaElements' in result:
                print(f"\n=== ARIA Elements ({len(result['ariaElements'])}) ===")
                for el in result.get('ariaElements', []):
                    print(f"  <{el.get('tag')}> testid={el.get('testId')} expanded={el.get('ariaExpanded')} haspopup={el.get('ariaHaspopup')} controls={el.get('ariaControls')}")
                    print(f"      text: {el.get('text', '')[:60]}")
            
            # 検索結果
            if 'matches' in result:
                print(f"\n=== Search Results ({len(result['matches'])}) ===")
                for el in result.get('matches', []):
                    print(f"  <{el.get('tag')}> testid={el.get('testId')} role={el.get('role')}")
                    print(f"      text: {el.get('text', '')[:80]}")
        else:
            print(f"Error: {result.get('error')}")
    
    elif cmd == 'status':
        # ブリッジサーバーの状態確認
        if BridgeServer.is_running():
            print("[Bridge] Running on ws://localhost:9224")
        else:
            print("[Bridge] Not running")
    
    elif cmd == 'reload':
        # Chrome拡張機能をリロード
        result = await ctrl._cmd(type='reload_extension')
        if result.get('success'):
            print("[Extension] Reloading... Please wait a few seconds.")
            print("[Extension] You may need to restart the bridge if connection is lost.")
        else:
            print(f"[Extension] Reload failed: {result.get('error', 'Unknown error')}")
    
    elif cmd == 'elements':
        # 操作可能な要素一覧を取得
        elements = await ctrl.get_elements(args.tab)
        print(f"Found {len(elements)} elements")
        for i, el in enumerate(elements[:100]):  # 最大100個表示
            text = (el.get('text') or '')[:50]
            selector = (el.get('selector') or '')[:50]
            el_type = el.get('type') or ''
            print(f"  [{i:3d}] {el_type:8s} | {text:50s} | {selector}")
        if len(elements) > 100:
            print(f"  ... and {len(elements) - 100} more")
    
    elif cmd == 'search-elements' or cmd == 'se':
        # 要素をテキストで検索
        query = args.message or (args.questions[0] if args.questions else None)
        if not query:
            print("Usage: python chatgpt_multi.py search-elements -m 'Pro'")
            print("   or: python chatgpt_multi.py se 'Pro'")
            return
        
        matches = await ctrl.search_elements(query, args.tab)
        print(f"Found {len(matches)} elements matching '{query}'")
        for el in matches:
            idx = el.get('index', 0)
            text = (el.get('text') or '')[:60]
            selector = (el.get('selector') or '')[:60]
            el_type = el.get('type') or ''
            print(f"  [{idx:3d}] {el_type:8s} | {text}")
            if selector:
                print(f"         selector: {selector}")
    
    elif cmd == 'page-text' or cmd == 'pt':
        # ページ全体のテキストを取得し検索
        query = args.message or (args.questions[0] if args.questions else None)
        text = await ctrl.get_page_text(args.tab)
        
        if query:
            # 検索モード
            lines = text.split('\n')
            query_lower = query.lower()
            matches = [l for l in lines if query_lower in l.lower()]
            print(f"Found {len(matches)} lines containing '{query}':")
            for line in matches[:50]:
                print(f"  {line[:100]}")
            if len(matches) > 50:
                print(f"  ... and {len(matches) - 50} more")
        else:
            # 全文表示モード（最大200行）
            lines = text.split('\n')[:200]
            for line in lines:
                print(line[:100])
            if len(text.split('\n')) > 200:
                print(f"... truncated (total {len(text.split(chr(10)))} lines)")
    
    elif cmd == 'inspect':
        # タブの詳細情報を表示
        tabs = await ctrl.get_tabs()
        
        # 対象タブを特定
        if args.tab:
            target_tabs = [t for t in tabs if t['id'] == args.tab]
        else:
            # ChatGPTタブを探す
            target_tabs = [t for t in tabs if 'chatgpt.com' in t.get('url', '')]
        
        if not target_tabs:
            print("No target tab found")
            return
        
        tab = target_tabs[0]
        tab_id = tab['id']
        
        print(f"=== Tab Inspection ===")
        print(f"ID: {tab_id}")
        print(f"URL: {tab.get('url', '')}")
        print(f"Title: {tab.get('title', '')}")
        
        # モデル情報
        models = await ctrl.get_models(tab_id)
        print(f"\nCurrent Model: {models.get('currentModel', 'Unknown')}")
        
        # Thinking情報
        thinking = await ctrl.get_thinking(tab_id)
        print(f"Thinking Level: {thinking.get('currentLevel', 'Unknown')}")
        
        # Pro関連要素を検索
        print(f"\n=== Pro/Model Related Elements ===")
        for query in ['Pro', 'model', 'thinking']:
            matches = await ctrl.search_elements(query, tab_id)
            if matches:
                print(f"\n'{query}' ({len(matches)} matches):")
                for el in matches[:5]:
                    text = (el.get('text') or '')[:60]
                    print(f"  [{el.get('index')}] {text}")
    
    else:
        # デフォルト: 引数を質問として並列検索
        questions = [cmd] + (args.questions or [])
        if len(questions) < 3:
            # 質問が足りない場合はデフォルト
            questions = [
                "日本の首都はどこですか？一言で答えて。",
                "1+2+3は何ですか？数字だけで答えて。",
                "今日は何曜日ですか？曜日だけ答えて。"
            ]
        
        results = await ctrl.parallel_search(
            questions=questions,
            model=args.model,
            thinking=args.thinking,
            files=args.files
        )
        print("\n=== Summary ===")
        for r in results:
            status = "OK" if r.get('success') else "FAIL"
            print(f"[{status}] Q{r.get('index', 0)+1}: {r.get('elapsed', 0):.1f}s")


if __name__ == '__main__':
    # bridgeコマンドは特別扱い（asyncio.run()の前に処理）
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'bridge':
        run_bridge_only()
    else:
        asyncio.run(main())
