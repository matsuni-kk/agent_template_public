---
name: chatgpt-parallel-research
description: "Browser Controller拡張機能を使ってChatGPT 5.2 Thinkingで3並列以上のウェブ検索・ブレスト・情報収集を実行する。難問にはHeavy thinking（heavy/extended）を使用。指定時のみChatGPT Proで深い考察・ファクトチェック。ファイル添付にも対応。「ウェブ検索」「横断検索」「並列検索」「ブレスト」「情報収集」「リサーチ」を依頼されたときに使用する。"
---

# ChatGPT Parallel Research Workflow

## Instructions
1. Preflight:
   - 概要: Browser Controller Chrome拡張機能を使用し、ChatGPTで3並列以上の検索・ブレストを実行して横断的に情報を収集する。
   - デフォルトモデル: ChatGPT 5.2 Thinking
   - オプション: ChatGPT Pro（`--model pro` 指定時のみ）- 深い考察・ファクトチェック用
   - 前提条件:
     - Browser Controller拡張機能がChromeにインストールされていること
     - ChatGPTにログイン済みであること
     - ブリッジサーバーは自動起動（手動起動不要）
   - ドキュメント精査原則（Preflight必須）：テンプレート確認後、生成前に必ず以下を実施すること。
     - アジェンダ・依頼文に記載された参照資料を全て読み込む。
     - Flow/Stock配下の関連資料（前回議事録・要望リスト・プロジェクトREADME等）を網羅的に検索・確認する。
     - 確認できなかった資料は「未参照一覧」として成果物に明記する。
     - これらを完了するまで生成を開始しない。
   - `./assets/chatgpt_research_template.md` を先に読み、章立て・必須項目・項目順序を確認する（テンプレートファースト）。
   - `./questions/chatgpt_research_questions.md` を使って必要情報を収集する。
   - 実行モードを確定する（自由度を絞る）。
     - `search`（デフォルト）: 3クエリ以上必須（3セッション以上で実行）
     - `search1`: 単一セッション検索（1タブで複数クエリを順次実行）
   - クエリを3個以上に分割・設計する（`search` を使う場合は必須）。
   - 各クエリは独立コンテキストとして成立するように、背景情報・前提・制約などの必要情報を各クエリ本文に含める。
   - モデル/推論強度を決める（モデル名はUI更新により変更される場合があります。`python chatgpt_multi.py models` で確認）。
     - モデル選択ガイド:
       | 難易度 | モデル | Thinking | 用途 |
       |--------|--------|----------|------|
       | 簡単～普通 | ChatGPT 5.2 Thinking | light | 一般的な検索、簡単なブレスト（デフォルト） |
       | 普通～やや難 | ChatGPT 5.2 Thinking | standard | 比較分析、中程度のブレスト |
       | 難問 | ChatGPT 5.2 Thinking | heavy | 技術的な深掘り、複雑な分析 |
       | 非常に難問 | ChatGPT 5.2 Thinking | extended | 最高精度の推論、専門的分析 |
       | 指定時のみ | ChatGPT Pro | - | 深い考察、確実なファクトチェック |
       | レガシー | ChatGPT Classic | - | 旧モデルでの確認が必要な場合 |
     - モデル使い分けの指針:
       - デフォルト: ChatGPT 5.2 Thinking（モデル指定不要）
       - 難問: `--thinking heavy` または `--thinking extended` を追加
       - ファクトチェック・深い考察: `--model pro` を明示的に指定
   - 検索クエリ設計ガイドライン:
     | 用途 | クエリ例 |
     |------|----------|
     | ウェブ検索 | 「〇〇について最新情報を検索して」「△△の公式ドキュメントを調べて」 |
     | ブレスト | 「〇〇のアイデアを10個出して」「△△の課題と解決策をブレストして」 |
     | 比較分析 | 「AとBの違いを詳しく比較して」「〇〇の選択肢のメリデメを整理して」 |
     | 深掘り | 「〇〇の技術的な仕組みを詳しく解説して」「△△の設計パターンを分析して」 |

2. 実行:
   - Browser Controller拡張機能がChromeにインストールされていること。
   - ChatGPTにログイン済みであること。
   - ブリッジサーバーは自動起動（手動起動不要）。接続確認:
     - `python chatgpt_multi.py status`

   - スクリプト実行パス:
     - `./scripts/chatgpt_multi.py`
   - 実行方法:
     - このSkillの `./scripts` に移動して実行:
       - `cd .github/skills/chatgpt-parallel-research/scripts && python chatgpt_multi.py "質問1" "質問2" "質問3"`
     - リポジトリルートからフルパス指定で実行:
       - `python .github/skills/chatgpt-parallel-research/scripts/chatgpt_multi.py "質問1" "質問2" "質問3"`
   - 外部依存:
     - Browser Controller Chrome拡張機能がインストール済みであること
     - Python 3.8以上

   - 3並列以上（search: 3クエリ以上必須）:
     - `python chatgpt_multi.py "検索クエリ1" "検索クエリ2" "検索クエリ3"`
     - `python chatgpt_multi.py "Q1" "Q2" "Q3" --thinking heavy`
     - `python chatgpt_multi.py "Q1" "Q2" "Q3" --model pro`

   - 単一セッション検索（search1: 1タブで順次）:
     - `python chatgpt_multi.py search1 "検索クエリ1" "検索クエリ2"`

   - ファイル添付:
     - 並列検索に添付: `python chatgpt_multi.py "Q1" "Q2" "Q3" --files /path/to/document.pdf`
     - 既存タブに添付: `python chatgpt_multi.py attach --file /path/to/document.pdf --tab <tab_id>`

   - 出力（保存先はこのSkill内に明記する）:
     - すべて `Flow/YYYYMM/YYYY-MM-DD/<topic>/` 配下に保存される。
     - `<topic>` は先頭の検索クエリ（または先頭の追加質問）から自動生成され、ファイル名に使えない文字は置換される。
     - 並列検索: `Flow/YYYYMM/YYYY-MM-DD/<topic>/chatgpt_q{N}_{timestamp}.md`
     - チャット: `Flow/YYYYMM/YYYY-MM-DD/<topic>/chatgpt_chat_tab{id}_{timestamp}.md`

   - セッション（マルチターン継続情報）:
     - `~/.chatgpt_multi_session.json` に `tab id/url/topic` を保存する。
     - タブが閉じている場合、`chat` / `recover` は保存済みURLからタブを再オープンして継続を試みる。
       - 旧形式のセッションファイルでURLが保存されていない場合は復元できない。

   - マルチターン（同じセッションに追加質問）:
     - 自動選択: `python chatgpt_multi.py chat -m "追加質問"`
     - 複数質問を同一セッションに順次送信: `python chatgpt_multi.py chat -m "Q1" "Q2" "Q3"`
     - タブを明示指定: `python chatgpt_multi.py chat -m "質問" --tab 123`

   - 再取得（受け取り側エラー対策）:
     - MD保存あり（タブID）: `python chatgpt_multi.py recover --tab <tab_id>`
     - MD保存あり（会話URL）: `python chatgpt_multi.py recover --url "https://chatgpt.com/c/<conversation_id>"`
     - 表示のみ: `python chatgpt_multi.py response --tab <tab_id>`

   - タブ管理:
     - 一覧: `python chatgpt_multi.py tabs`
     - 閉じる: `python chatgpt_multi.py close --tab <tab_id>`

   - CLI Reference（抜粋）:
     - タブ一覧: `python chatgpt_multi.py tabs`
     - モデル一覧: `python chatgpt_multi.py models`
     - Thinking強度確認: `python chatgpt_multi.py thinking`
     - Thinking強度設定: `python chatgpt_multi.py set-thinking --level heavy`
     - 単一チャット（マルチターン）: `python chatgpt_multi.py chat -m "質問内容"`
     - ファイル添付: `python chatgpt_multi.py attach --file /path/to/file.pdf --tab <tab_id>`
     - 回答取得（表示のみ）: `python chatgpt_multi.py response --tab <tab_id>`
     - 再取得（MD保存）: `python chatgpt_multi.py recover --tab <tab_id>`
     - ブリッジ状態確認: `python chatgpt_multi.py status`
     - ブリッジ起動（フォアグラウンド）: `python chatgpt_multi.py bridge`

   - 並列検索オプション（抜粋）:
     ```bash
     python chatgpt_multi.py [質問1] [質問2] [質問3] ...
       --model        : モデル選択（例: pro）
       --thinking, -t : 推論強度（light, standard, heavy, extended）
       --files        : 添付ファイル（複数可）
       --interval     : ポーリング間隔（デフォルト: 5秒）
       --no-auto-bridge : ブリッジ自動起動を無効化
       --close-tabs   : search/search1/chat/recover 完了後にタブを閉じる
       --keep-tabs    : (Deprecated: デフォルトで保持) タブを保持
     ```

   - 制約:
     - `search` は3クエリ未満を受け付けない（3セッション未満を禁止）。
     - タイムアウトは固定1800秒（30分）で、`--timeout` を指定しても無視される。
     - エージェント側で `sleep` 等により独自の待機を足さない。

3. 結果統合:
   - 各タブの応答（個別MD）を収集し、`./assets/chatgpt_research_template.md` 形式で統合する。
   - 情報源・信頼性・矛盾点を整理し、結論と推奨アクションを明確化する。

4. Troubleshooting:
   - 症状: MDが `## 回答` の `(waiting...)` から更新されない。
     - 原因: 応答取得に失敗している。
     - 手順:
       - タブID確認: `python chatgpt_multi.py tabs`
       - 再取得（MD保存）: `python chatgpt_multi.py recover --tab <tab_id>`
       - 表示のみ: `python chatgpt_multi.py response --tab <tab_id>`
       - ChatGPT側のエラーメッセージや制限（Rate limit等）を確認する。

5. QC（必須）:
   - `recommended_subagents` のQC Subagentに評価を委譲する。
   - Subagentは `./evaluation/evaluation_criteria.md` に基づきQCを実施する。
   - 指摘があれば追加検索（`search` または `search1`）や `recover` を実行する。
   - 最大3回まで繰り返し確定する。

6. バックログ反映:
   - 追加調査が必要な項目、未解決の論点、次アクションをバックログへ反映する。

subagent_policy:
  - 品質ループ（QC/チェック/フィードバック）は必ずサブエージェントへ委譲する
  - 指摘の反映は最小差分で行う
  - 指摘に対し「修正した/しない」と理由を最終成果物に残す

recommended_subagents:
  - qa-skill-qc: 3並列要件、クエリ多様性、統合内容、欠損の有無を検査

## Resources
- questions: ./questions/chatgpt_research_questions.md
- assets: ./assets/chatgpt_research_template.md
- evaluation: ./evaluation/evaluation_criteria.md
- scripts: ./scripts/chatgpt_multi.py
- guide: ./guide/guide.md

## Next Action
- 統合結果をもとに、設計・実装・追加調査の次アクションへ進む。
- 指摘が出た場合は、追加検索または再取得を実行して再QCする。

## Subagent Execution
このSkillはサブエージェントとして独立実行可能。
- サブエージェント: `agents/chatgpt-parallel-research-agent.md`
- 用途: 並列ウェブ検索、ブレインストーミング、横断情報収集、ファクトチェック
- 入力: `search_queries`（3個以上必須）, `model`（pro等）, `thinking`（light/standard/heavy/extended）
- 出力: 統合された検索結果レポート（chatgpt_research_template.md形式）
