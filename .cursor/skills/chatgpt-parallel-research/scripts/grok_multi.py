#!/usr/bin/env python3
"""
Grok Parallel Research Tool
============================
3並列以上のGrok検索・ブレスト・情報収集を1つのスクリプトで実行

機能:
- 並列質問送信（3並列以上推奨）
- モデル選択
- DeepThink/DeepSearch設定
- 確実な回答取得
- タブ管理
- ブリッジサーバー内蔵（自動起動）

使用例:
  # 基本的な並列検索
  python grok_multi.py "質問1" "質問2" "質問3"
  
  # DeepThinkで難問を解く
  python grok_multi.py "難しい質問1" "難しい質問2" --deepthink
  
  # DeepSearchで検索
  python grok_multi.py "検索1" "検索2" --deepsearch
  
  # タブ一覧を確認
  python grok_multi.py tabs
  
  # モデル一覧を確認
  python grok_multi.py models
  
  # 単一チャット
  python grok_multi.py chat -m "質問内容"
  
  # ブリッジサーバーのみ起動（手動）
  python grok_multi.py bridge
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


## httpx/html2text は不要（Chrome拡張経由でDOM取得するため削除）


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
            
            if data.get('type') == 'extension_connected':
                print("[Bridge] Chrome extension connected")
                self.extension_ws = ws
                
                async for message in ws:
                    try:
                        resp = json.loads(message)
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
            
            await process_command(data)
            
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
            await asyncio.Future()
    
    @staticmethod
    def start_background():
        """バックグラウンドプロセスでブリッジサーバーを起動"""
        script_path = os.path.abspath(__file__)
        process = subprocess.Popen(
            [sys.executable, script_path, 'bridge'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        for _ in range(30):
            time.sleep(0.1)
            if BridgeServer.is_running():
                print(f"[Bridge] Started in background (PID: {process.pid})")
                return True
        
        print("[Bridge] Failed to start")
        return False


# ========================================
# Grok Controller
# ========================================

class GrokController:
    """Grok操作の統合コントローラー"""
    
    BRIDGE_URL = "ws://localhost:9224"
    GROK_URL = "https://x.com/i/grok"
    
    def __init__(self, timeout: int = 1200, poll_interval: int = 5, auto_bridge: bool = True):
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.auto_bridge = auto_bridge
        self._ws = None
        self._request_id = 0
        self._lock = asyncio.Lock()
    
    async def connect(self):
        """ブリッジサーバーに接続（必要なら自動起動）"""
        if self._ws is None or (hasattr(self._ws, 'closed') and self._ws.closed) or (hasattr(self._ws, 'state') and self._ws.state.name == 'CLOSED'):
            if self.auto_bridge and not BridgeServer.is_running():
                print("[Bridge] Not running, starting automatically...")
                if not BridgeServer.start_background():
                    raise ConnectionError("Failed to start bridge server")
                await asyncio.sleep(0.5)
            
            try:
                self._ws = await websockets.connect(self.BRIDGE_URL)
            except Exception as e:
                raise ConnectionError(f"Failed to connect to bridge server: {e}")
    
    async def _cmd(self, **kwargs) -> Dict:
        """コマンドを送信して応答を待つ"""
        async with self._lock:
            await self.connect()
            self._request_id += 1
            req_id = f"r{self._request_id}"
            kwargs['requestId'] = req_id
            
            await self._ws.send(json.dumps(kwargs))
            
            try:
                response = await asyncio.wait_for(self._ws.recv(), timeout=30)
                return json.loads(response)
            except asyncio.TimeoutError:
                return {'error': 'Timeout waiting for response'}
    
    async def close(self):
        """WebSocket接続を閉じる"""
        if self._ws:
            await self._ws.close()
            self._ws = None
    
    # ========================================
    # タブ操作
    # ========================================
    
    async def get_tabs(self) -> List[Dict]:
        """タブ一覧を取得"""
        result = await self._cmd(type='get_tabs')
        return result.get('tabs', [])
    
    async def new_tab(self, url: str = None) -> Dict:
        """新しいGrokタブを開く"""
        return await self._cmd(type='new_tab', url=url or self.GROK_URL)
    
    async def close_tab(self, tab_id: int) -> Dict:
        """タブを閉じる"""
        return await self._cmd(type='close_tab', tabId=tab_id)
    
    async def switch_tab(self, tab_id: int) -> Dict:
        """タブを切り替える"""
        return await self._cmd(type='switch_tab', tabId=tab_id)
    
    # ========================================
    # 基本DOM操作（共通機能）
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
    # スクリーンショット（共通機能）
    # ========================================
    
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
            data_url = result['dataUrl']
            if ',' in data_url:
                base64_data = data_url.split(',')[1]
                with open(save_path, 'wb') as f:
                    f.write(base64.b64decode(base64_data))
                result['path'] = save_path
        
        return result
    
    # ========================================
    # DOM調査（共通機能）
    # ========================================
    
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
    
    # ========================================
    # ファイル添付（共通機能）
    # ========================================
    
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
            type='attach_file',
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
    
    # ========================================
    # Grok専用機能
    # ========================================
    
    async def send_message(self, message: str, tab_id: int = None) -> Dict:
        """メッセージを送信"""
        return await self._cmd(type='grok_send_message', message=message, tabId=tab_id)
    
    async def get_response(self, tab_id: int = None) -> str:
        """回答を取得"""
        result = await self._cmd(type='grok_get_response', tabId=tab_id)
        return result.get('response', '')
    
    async def is_generating(self, tab_id: int = None) -> bool:
        """生成中かどうかを確認"""
        result = await self._cmd(type='grok_is_generating', tabId=tab_id)
        return result.get('generating', False)
    
    async def get_models(self, tab_id: int = None) -> Dict:
        """利用可能なモデル一覧を取得"""
        return await self._cmd(type='grok_get_models', tabId=tab_id)
    
    async def select_model(self, model: str, tab_id: int = None) -> Dict:
        """モデルを選択"""
        return await self._cmd(type='grok_select_model', model=model, tabId=tab_id)
    
    async def set_mode(self, mode: str, tab_id: int = None) -> Dict:
        """モードを設定（think/search等）"""
        return await self._cmd(type='grok_set_mode', mode=mode, tabId=tab_id)
    
    async def is_deepthink(self, tab_id: int = None) -> Dict:
        """DeepThink状態を確認"""
        return await self._cmd(type='grok_is_deepthink', tabId=tab_id)
    
    async def enable_deepthink(self, tab_id: int = None) -> Dict:
        """DeepThinkを有効化"""
        return await self._cmd(type='grok_enable_deepthink', tabId=tab_id)
    
    async def disable_deepthink(self, tab_id: int = None) -> Dict:
        """DeepThinkを無効化"""
        return await self._cmd(type='grok_disable_deepthink', tabId=tab_id)
    
    async def enable_deepsearch(self, tab_id: int = None) -> Dict:
        """DeepSearchを有効化"""
        return await self._cmd(type='grok_enable_deepsearch', tabId=tab_id)
    
    # ========================================
    # 並列検索
    # ========================================
    
    async def parallel_search(
        self,
        questions: List[str],
        model: str = None,
        deepthink: bool = False,
        deepsearch: bool = False,
        close_tabs: bool = True
    ) -> List[Dict]:
        """
        複数の質問を並列で送信し、全ての応答を取得
        
        Args:
            questions: 質問リスト
            model: 使用するモデル
            deepthink: DeepThinkを有効化するか
            deepsearch: DeepSearchを有効化するか
            close_tabs: 回答取得後にタブを閉じるか
        """
        MAX_PARALLEL = 10
        n = len(questions)
        
        if n > MAX_PARALLEL:
            print(f"Warning: Maximum {MAX_PARALLEL} parallel queries allowed. Truncating from {n}.")
            questions = questions[:MAX_PARALLEL]
            n = MAX_PARALLEL
        
        print(f"\n{'='*60}")
        print(f"Grok Parallel Search: {n} questions")
        print('='*60)
        if model:
            print(f"Model: {model}")
        if deepthink:
            print("DeepThink: Enabled")
        if deepsearch:
            print("DeepSearch: Enabled")
        print()
        
        # 1. タブを開く
        print(f"[1/4] Opening {n} Grok tabs...")
        tab_ids = []
        for i in range(n):
            result = await self.new_tab()
            if result.get('tab', {}).get('id'):
                tab_ids.append(result['tab']['id'])
                print(f"  Tab {i+1}: ID={result['tab']['id']}")
            await asyncio.sleep(1)
        
        if len(tab_ids) != n:
            return [{'success': False, 'error': f'Failed to open tabs: {len(tab_ids)}/{n}'}]
        
        print("  Waiting for pages to load...")
        await asyncio.sleep(3)
        
        # 2. モデル/モード設定
        if model:
            print(f"\n[1.5] Selecting model: {model}...")
            for i, tid in enumerate(tab_ids):
                r = await self.select_model(model, tid)
                status = "OK" if r.get('success') else f"FAIL: {r.get('error', '')}"
                print(f"  Tab {i+1}: {status}")
                await asyncio.sleep(0.5)
        
        if deepthink:
            print(f"\n[1.6] Enabling DeepThink...")
            for i, tid in enumerate(tab_ids):
                r = await self.enable_deepthink(tid)
                status = "OK" if r.get('success') else f"FAIL: {r.get('error', '')}"
                print(f"  Tab {i+1}: {status}")
                await asyncio.sleep(0.5)
        
        if deepsearch:
            print(f"\n[1.7] Enabling DeepSearch...")
            for i, tid in enumerate(tab_ids):
                r = await self.enable_deepsearch(tid)
                status = "OK" if r.get('success') else f"FAIL: {r.get('error', '')}"
                print(f"  Tab {i+1}: {status}")
                await asyncio.sleep(0.5)
        
        # 3. 質問を送信
        print(f"\n[2/4] Sending questions...")
        for i, (tid, q) in enumerate(zip(tab_ids, questions)):
            await self.send_message(q, tid)
            print(f"  Tab {i+1}: Sent '{q[:50]}...'")
            await asyncio.sleep(0.5)
        
        # 4. 回答を待機
        print(f"\n[3/4] Waiting for responses (timeout: {self.timeout}s)...")
        
        md_path = self._init_results_md(questions, model, deepthink, deepsearch)
        print(f"[Output] Writing to: {md_path}")
        
        results = [None] * n
        
        async def wait_for_response(tid: int, idx: int, question: str) -> Dict:
            start = time.time()
            last_response = ""
            stable_count = 0
            fallback_attempted = False
            
            while True:
                elapsed = time.time() - start
                if elapsed > self.timeout:
                    # タイムアウト時にChrome拡張経由でDOM再取得を試行
                    if not fallback_attempted:
                        fallback_attempted = True
                        print(f"  Tab {idx+1}: Timeout - trying DOM fallback via extension...")
                        fallback_response = await self._get_full_page_content(tid)
                        if fallback_response and len(fallback_response) > 50:
                            result = {
                                'success': True, 'index': idx,
                                'question': question, 'response': fallback_response,
                                'tab_id': tid, 'elapsed': elapsed,
                                'fallback': True
                            }
                            self._append_result_md(md_path, result)
                            results[idx] = result
                            print(f"  Tab {idx+1}: Recovered via DOM fallback ({elapsed:.1f}s) → Saved to MD")
                            return result
                    
                    result = {
                        'success': False, 'error': 'Timeout',
                        'index': idx, 'question': question, 'tab_id': tid,
                        'response': last_response, 'elapsed': elapsed
                    }
                    self._append_result_md(md_path, result)
                    results[idx] = result
                    print(f"  Tab {idx+1}: Timeout ({elapsed:.1f}s)")
                    return result
                
                generating = await self.is_generating(tid)
                response = await self.get_response(tid)
                
                if response and len(response) > 5:
                    if not generating:
                        if response == last_response:
                            stable_count += 1
                            if stable_count >= 2:
                                result = {
                                    'success': True, 'index': idx,
                                    'question': question, 'response': response,
                                    'tab_id': tid, 'elapsed': elapsed
                                }
                                self._append_result_md(md_path, result)
                                results[idx] = result
                                print(f"  Tab {idx+1}: Done ({elapsed:.1f}s) → Saved to MD")
                                return result
                        else:
                            stable_count = 0
                    else:
                        stable_count = 0
                    last_response = response
                
                status = "Generating..." if generating else "Waiting..."
                print(f"  Tab {idx+1}: {status} ({int(elapsed)}s)")
                await asyncio.sleep(self.poll_interval)
        
        tasks = [asyncio.create_task(wait_for_response(tid, i, q)) 
                 for i, (tid, q) in enumerate(zip(tab_ids, questions))]
        
        await asyncio.gather(*tasks)
        
        # 5. 結果サマリー
        print(f"\n{'='*60}")
        print("[4/4] Summary")
        print('='*60)
        
        for r in results:
            if r is None:
                continue
            idx = r.get('index', 0)
            status = "OK" if r.get('success') else f"FAIL ({r.get('error')})"
            print(f"  Q{idx+1}: {status} ({r.get('elapsed', 0):.1f}s)")
        
        print(f"\n[Output] Saved to: {md_path}")
        
        if close_tabs:
            print(f"\n[Cleanup] Closing {len(tab_ids)} tabs...")
            for tid in tab_ids:
                await self.close_tab(tid)
            print("  Done.")
        
        return results
    
    def _get_flow_path(self, filename: str) -> Path:
        """Flowディレクトリ内のパスを取得"""
        from datetime import datetime
        
        now = datetime.now()
        yymm = now.strftime("%Y%m")
        yyyymmdd = now.strftime("%Y-%m-%d")
        
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
        return day_dir / filename
    
    def _init_results_md(self, questions: List[str], model: str = None, deepthink: bool = False, deepsearch: bool = False) -> str:
        """MDファイルを初期化"""
        from datetime import datetime
        
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        filename = f"grok_search_{timestamp}.md"
        save_path = self._get_flow_path(filename)
        
        lines = [
            f"# Grok Parallel Search Results",
            f"",
            f"**実行日時**: {now.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**モデル**: {model or 'default'}",
            f"**DeepThink**: {'Enabled' if deepthink else 'Disabled'}",
            f"**DeepSearch**: {'Enabled' if deepsearch else 'Disabled'}",
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
        
        lines = [
            f"### Q{idx}: {question}",
            ""
        ]
        
        if success:
            lines.append(f"**ステータス**: OK ({elapsed:.1f}s)")
            lines.append("")
            lines.append(response)
        else:
            lines.append(f"**ステータス**: FAIL - {error}")
            if response:
                lines.append("")
                lines.append(f"**部分回答**: {response[:500]}")
        
        lines.extend(["", "---", ""])
        
        with open(md_path, 'a', encoding='utf-8') as f:
            f.write("\n".join(lines))
    
    async def _get_full_page_content(self, tab_id: int) -> Optional[str]:
        """
        Chrome拡張経由でページ全体のコンテンツを取得（フォールバック用）
        
        ログイン済みセッションでDOMから直接テキストを取得するため、
        httpx等の外部フェッチよりも確実に回答を取得できる。
        
        Args:
            tab_id: タブID
        
        Returns:
            ページコンテンツ、または失敗時はNone
        """
        try:
            # まず通常の回答取得を再試行
            response = await self.get_response(tab_id)
            if response and len(response) > 50:
                return response
            
            # 失敗した場合、より広範なセレクタで取得
            # Grokの回答領域を取得
            selectors = [
                '[data-testid="tweetText"]',  # ツイート形式の回答
                '[data-testid="messageText"]',  # メッセージ形式
                'article',  # 記事領域
                'main',  # メインコンテンツ
            ]
            
            for selector in selectors:
                result = await self.get_text(selector, tab_id)
                if result.get('texts'):
                    texts = [t for t in result['texts'] if len(t) > 50]
                    if texts:
                        # 最後の回答を返す
                        return texts[-1]
                elif result.get('text') and len(result.get('text', '')) > 50:
                    return result['text']
            
            # 最終手段: ページ全体のテキスト
            page_text = await self.get_page_text(tab_id)
            if page_text and len(page_text) > 100:
                return page_text
            
            return None
            
        except Exception as e:
            print(f"  [DOM Fallback] Failed: {e}")
            return None
    
    # ========================================
    # 単一チャット
    # ========================================
    
    async def chat(self, message: str, tab_id: int = None, wait: bool = True) -> Dict:
        """単一のメッセージを送信"""
        send_result = await self.send_message(message, tab_id)
        if not send_result.get('success'):
            return send_result
        
        # 送信に使用したタブIDを取得（タブ指定がない場合でも正しいタブを追跡）
        used_tab_id = send_result.get('tabId') or tab_id
        
        if not wait:
            return send_result
        
        start = time.time()
        last_response = ""
        stable_count = 0
        
        while True:
            elapsed = time.time() - start
            if elapsed > self.timeout:
                return {'success': False, 'error': 'Timeout', 'response': last_response}
            
            generating = await self.is_generating(used_tab_id)
            response = await self.get_response(used_tab_id)
            
            # 回答があり、生成中でない場合
            if response and len(response) > 0 and not generating:
                if response == last_response:
                    stable_count += 1
                    if stable_count >= 2:
                        return {'success': True, 'response': response, 'elapsed': elapsed}
                else:
                    stable_count = 0
                last_response = response
            
            await asyncio.sleep(self.poll_interval)


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
        description='Grok Parallel Research Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 並列検索（3並列以上推奨）
  python grok_multi.py "質問1" "質問2" "質問3"
  
  # DeepThinkで難問を解く
  python grok_multi.py "難問1" "難問2" "難問3" --deepthink
  
  # DeepSearchで検索
  python grok_multi.py "検索1" "検索2" "検索3" --deepsearch
  
  # タブ一覧
  python grok_multi.py tabs
  
  # モデル一覧
  python grok_multi.py models
  
  # 単一チャット
  python grok_multi.py chat -m "質問内容"
  
  # DeepThink有効化
  python grok_multi.py deepthink
  
  # DeepSearch有効化
  python grok_multi.py deepsearch
  
  # 状態確認
  python grok_multi.py status
  
  # === 共通機能 ===
  # ファイル添付
  python grok_multi.py attach --file document.pdf --tab 123456
  
  # スクリーンショット
  python grok_multi.py screenshot --tab 123456
  
  # 要素一覧
  python grok_multi.py elements --tab 123456
  
  # 要素検索
  python grok_multi.py search-elements "送信" --tab 123456
  
  # ページテキスト取得
  python grok_multi.py page-text --tab 123456
  
  # DOM調査
  python grok_multi.py inspect summary --tab 123456
  
  # ブリッジサーバーのみ起動
  python grok_multi.py bridge
"""
    )
    
    parser.add_argument('command', nargs='?', default='search',
                        help='Command: search, tabs, models, chat, deepthink, deepsearch, status, attach, screenshot, elements, search-elements, page-text, inspect, bridge')
    parser.add_argument('questions', nargs='*', help='Questions for parallel search')
    parser.add_argument('--timeout', type=int, default=1800, help='Timeout in seconds')
    parser.add_argument('--interval', type=int, default=10, help='Poll interval')
    parser.add_argument('--model', help='Model to use')
    parser.add_argument('--tab', type=int, help='Tab ID')
    parser.add_argument('--message', '-m', help='Message for chat command')
    parser.add_argument('--file', '-f', help='File to attach')
    parser.add_argument('--files', nargs='+', help='Files to attach')
    parser.add_argument('--no-auto-bridge', action='store_true', 
                        help='Disable automatic bridge server startup')
    parser.add_argument('--keep-tabs', action='store_true',
                        help='Keep tabs open after search')
    parser.add_argument('--deepthink', action='store_true',
                        help='Enable DeepThink mode')
    parser.add_argument('--deepsearch', action='store_true',
                        help='Enable DeepSearch mode')
    
    args = parser.parse_args()
    
    cmd = args.command.lower() if args.command else 'search'
    
    ctrl = GrokController(
        timeout=args.timeout, 
        poll_interval=args.interval,
        auto_bridge=not args.no_auto_bridge
    )
    
    # questionsがあればsearchコマンド
    if args.questions and cmd == 'search':
        results = await ctrl.parallel_search(
            questions=args.questions,
            model=args.model,
            deepthink=args.deepthink,
            deepsearch=args.deepsearch,
            close_tabs=not args.keep_tabs
        )
        print("\n=== Summary ===")
        for r in results:
            status = "OK" if r.get('success') else "FAIL"
            print(f"[{status}] Q{r.get('index', 0)+1}: {r.get('elapsed', 0):.1f}s")
    
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
    
    elif cmd == 'chat':
        msg = args.message
        if not msg:
            print("Error: --message / -m required")
            return
        result = await ctrl.chat(msg, args.tab)
        if result.get('success'):
            print(f"\n[Grok Response] ({result.get('elapsed', 0):.1f}s)")
            print(result.get('response', ''))
        else:
            print(f"Error: {result.get('error')}")
    
    elif cmd == 'deepthink':
        result = await ctrl.enable_deepthink(args.tab)
        if result.get('success'):
            print("[Grok] DeepThink enabled")
        else:
            print(f"[Grok] DeepThink failed: {result.get('error', 'Unknown error')}")
    
    elif cmd == 'deepsearch':
        result = await ctrl.enable_deepsearch(args.tab)
        if result.get('success'):
            print("[Grok] DeepSearch enabled")
        else:
            print(f"[Grok] DeepSearch failed: {result.get('error', 'Unknown error')}")
    
    elif cmd == 'status':
        # ブリッジ状態
        if BridgeServer.is_running():
            print("[Bridge] Running on ws://localhost:9224")
        else:
            print("[Bridge] Not running")
        
        # DeepThink状態
        dt_result = await ctrl.is_deepthink(args.tab)
        print(f"[Grok DeepThink] {'Enabled' if dt_result.get('enabled') else 'Disabled'}")
        
        # モデル情報
        models = await ctrl.get_models(args.tab)
        print(f"[Grok Model] {models.get('currentModel', 'Unknown')}")
    
    elif cmd == 'response':
        response = await ctrl.get_response(args.tab)
        if response:
            print(response)
        else:
            print("No response found")
    
    # ========================================
    # 共通機能: ファイル添付
    # ========================================
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
    
    # ========================================
    # 共通機能: スクリーンショット
    # ========================================
    elif cmd == 'screenshot' or cmd == 'ss':
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_path = f'/tmp/grok_screenshot_{timestamp}.png'
        save_path = args.file or default_path
        
        result = await ctrl.screenshot(args.tab, save_path)
        if result.get('success'):
            print(f"[Screenshot] Saved to: {result.get('path', save_path)}")
            print(f"  Tab: {result.get('title', '')}")
            print(f"  URL: {result.get('url', '')}")
        else:
            print(f"[Screenshot] Failed: {result.get('error')}")
    
    # ========================================
    # 共通機能: 要素一覧
    # ========================================
    elif cmd == 'elements':
        elements = await ctrl.get_elements(args.tab)
        print(f"Found {len(elements)} interactive elements:")
        for i, el in enumerate(elements[:50]):  # 最初の50件のみ表示
            el_type = el.get('type', 'unknown')
            text = (el.get('text') or '')[:40]
            selector = (el.get('selector') or '')[:50]
            print(f"  [{i}] {el_type}: {text}")
            print(f"       {selector}")
        if len(elements) > 50:
            print(f"  ... and {len(elements) - 50} more elements")
    
    # ========================================
    # 共通機能: 要素検索
    # ========================================
    elif cmd == 'search-elements':
        query = args.questions[0] if args.questions else None
        if not query:
            print("Error: search query required")
            print("Usage: python grok_multi.py search-elements \"検索文字列\"")
            return
        
        matches = await ctrl.search_elements(query, args.tab)
        print(f"Found {len(matches)} elements matching '{query}':")
        for el in matches:
            idx = el.get('index', '?')
            el_type = el.get('type', 'unknown')
            text = (el.get('text') or '')[:40]
            selector = (el.get('selector') or '')[:50]
            print(f"  [{idx}] {el_type}: {text}")
            print(f"       {selector}")
    
    # ========================================
    # 共通機能: ページテキスト取得
    # ========================================
    elif cmd == 'page-text':
        text = await ctrl.get_page_text(args.tab)
        print(text[:5000] if text else "No text found")
        if text and len(text) > 5000:
            print(f"\n... truncated ({len(text)} total chars)")
    
    # ========================================
    # 共通機能: DOM調査
    # ========================================
    elif cmd == 'inspect' or cmd == 'dom':
        mode = 'summary'
        selector = None
        search_text = None
        
        if args.questions:
            first_arg = args.questions[0]
            if first_arg in ['summary', 'interactive', 'testids', 'tree', 'aria', 'search']:
                mode = first_arg
                if mode == 'search' and len(args.questions) > 1:
                    search_text = args.questions[1]
            elif first_arg.startswith(('[', '.', '#', '*')):
                selector = first_arg
            else:
                mode = 'search'
                search_text = first_arg
        
        result = await ctrl.inspect_dom(args.tab, selector, mode, search_text)
        
        if result.get('success'):
            print(f"=== DOM Inspection: {result.get('url', '')} ===")
            print(f"  Title: {result.get('title', '')}")
            
            if 'summary' in result:
                s = result['summary']
                print(f"\n=== Page Summary ===")
                print(f"  Total elements: {s.get('totalElements', 0)}")
                print(f"  Interactive: {s.get('interactiveCount', 0)}")
                print(f"  With data-testid: {s.get('testIdCount', 0)}")
            
            if 'elements' in result:
                print(f"\n=== Elements ({len(result['elements'])}) ===")
                for el in result['elements'][:20]:
                    vis = 'visible' if el.get('visible') else 'hidden'
                    print(f"  <{el.get('tag')}> {vis} - {el.get('text', '')[:50]}")
        else:
            print(f"Error: {result.get('error')}")
    
    else:
        # デフォルト: 引数を質問として並列検索
        questions = [cmd] + (args.questions or [])
        if len(questions) < 3:
            questions = [
                "日本の首都はどこですか？一言で答えて。",
                "1+2+3は何ですか？数字だけで答えて。",
                "今日は何曜日ですか？曜日だけ答えて。"
            ]
        
        results = await ctrl.parallel_search(
            questions=questions,
            model=args.model,
            deepthink=args.deepthink,
            deepsearch=args.deepsearch,
            close_tabs=not args.keep_tabs
        )
        print("\n=== Summary ===")
        for r in results:
            status = "OK" if r.get('success') else "FAIL"
            print(f"[{status}] Q{r.get('index', 0)+1}: {r.get('elapsed', 0):.1f}s")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'bridge':
        run_bridge_only()
    else:
        asyncio.run(main())
