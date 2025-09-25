# Agent Template Generator

このリポジトリは「エージェントを作るためのエージェント」を提供するテンプレート実装です。Cursor / Claude などの対話型 IDE で、企画・業務ドメインに特化したカスタム AI エージェントを短時間で生成・展開することを目的としています。

---

## 1. What you get / 提供価値
- `.cursor/rules` 以下に汎用化されたマスタールールと機能別ルール雛形
- Flow / Stock ディレクトリ構成を自動で生成するスクリプト群
- 参照資料・Gate 判定・Flow→Stock 移行など、実務ワークフローを汎用化した mdc テンプレート
- エージェント生成後もチャット経由で追加ルールを量産できる運用ガイド

このテンプレート自身が「エージェント生成エージェント」として動作し、ユーザーは名前・ドメイン・目的を伝えるだけで専用リポジトリを出力できます。

---

## 2. Repository Layout
```
agent_template/
├── scripts/                    # 生成・更新補助スクリプト
│   └── enhanced_generate_agent.py
├── template/agent_base/        # エージェント共通ベース（Flow/Stock 構成や基本ルール）
├── output/                     # 生成されたドメインエージェントが格納される場所
├── CODE_OF_CONDUCT.md          # 英日併記の行動規範
├── LICENSE                     # 本テンプレートの使用許諾契約
└── README.md                   # このドキュメント
```

---

## 3. How to generate a new agent
1. **要件を伝える**: 「企画エージェントを作りたい」「法務レビュー用に」など、エージェント名・ドメイン・期待成果をチャットに入力
2. **スクリプト実行（エージェントがキック）**: `python3 scripts/enhanced_generate_agent.py --agent-name <name> --domain <domain> --description "..."` ※ 実行は対話エージェント側で行われ、ユーザーはコマンドを口頭で指示するだけでOK
3. **出力確認**: `output/<domain>_agent/` 以下に Flow/Stock、`.cursor/rules`、テンプレートが出力される
4. **ルール調整**: 生成された mdc ファイルをチャットで読み込みつつ、質問票・テンプレート・ワークフローをカスタマイズ
5. **動作検証**: Flow にドラフトを作成 → 確定反映コマンドで Stock へ移行 → 必要に応じてルール追加

---

## 4. Included rule templates
| 番号 | ファイル | 目的 |
|------|----------|------|
| 00   | 00_master_rules.mdc | トリガーと Flow→Stock オーケストレーション |
| 01-06| ドメイン固有テンプレ | 企画・分析・実装など、要件に応じて差し替え可能な雛形 |
| 90   | 90_task_management.mdc | 日次タスク作成など共通ユーティリティ |
| 97   | 97_flow_to_stock_rules.mdc | Flow→Stock 移行手順 |
| 98   | 98_flow_assist.mdc | ブレインストーム支援 |
| 99   | 99_rule_maintenance.mdc | ルールメンテナンス用ガイド |

個別のドメインエージェントを生成した後、該当 mdc ファイルに質問項目・テンプレート・ワークフローを実装します。

---

## 5. Customization tips
- `planning_paths.mdc` のようなパス辞書を各ドメイン向けに複製し、Flow/Stock/Archived の保存先を定義
- 質問票 (`*_questions`) に「参照資料」を必須項目として設定し、既存ドキュメントとの差分管理を徹底
- Gate 判定や KPI 管理など、チーム固有のレビューポリシーをテンプレートに埋め込む

---

## 6. License & contact
- 使用許諾: `LICENSE` を参照してください（個人・社内利用は無償、商用利用は要連絡）。
- 著作権: © 2025 國松 憂魁 (Yukai Kunimatsu)
- 連絡先: yukai.kunimatsu@explaza.jp / X: [@yugen_matuni](https://x.com/yugen_matuni)

---

## 7. 行動規範 / Code of Conduct
- Contributor Covenant v2.1（英日併記）を採用しています。`CODE_OF_CONDUCT.md` を参照してください。

---

## 8. 免責事項
本テンプレートは「現状有姿」で提供されます。利用に伴ういかなる損害についても作者は責任を負いません。利用者は関連法令・契約・社内規程を自己の責任で遵守してください。

---

## 9. 謝辞
テンプレート設計に際しフィードバックをくださったコミュニティメンバーとパートナーに感謝します。
