<!-- FILE: 00_master_rules.mdc START -->
# ==========================================================
# Agent Template - ドメイン特化エージェント生成フレームワーク
# ==========================================================

framework_overview:
  name: "Agent Template"
  description: "高品質な業務特化エージェントを生成するテンプレートベースフレームワーク。"
  focus_areas:
    - "業界標準準拠"
    - "実務即応性"
    - "手作り品質"


# =========================
# 設計思想
# =========================

design_principles:
  - id: "industry_standard_alignment"
    label: "業界標準準拠"
    description: "BABOK、AMA Marketing BOKなどの認知されたフレームワークに準拠する。"
  - id: "operational_readiness"
    label: "実務即応性"
    description: "現場で直ちに使える詳細なワークフローを提供する。"
  - id: "crafted_quality"
    label: "手作り品質"
    description: "専門知識に基づいた高品質テンプレートを維持する。"


# =========================
# エージェント作成ワークフロー
# =========================

agent_creation_tasks:
  description: "ヒアリングで蓄積した要件と合意事項を基にエージェント作成工程を管理する進捗タスクリスト。ユーザーと共有し、必要に応じて項目を追加・削除する。保存場所は日次Flow階層に統一（例: Flow/{{meta.year_month}}/{{meta.today}}/{{meta.agent_dir}}/{{meta.today}}_agent_creation_tasklist.md）。要件定義ファイルは常に create_markdown_file で生成・更新し、以降の作業で参照・同期する。生成後のエージェントが独立運用する際も同一パス方針を維持する。"
  default_items:
    - id: "update_tasklist_file"
      detail: "作業開始直後に Flow/{{meta.year_month}}/{{meta.today}}/{{meta.agent_dir}}/{{meta.today}}_agent_creation_tasklist.md を create_markdown_file で生成し、以降の工程管理と承認事項を記録する。保存場所は日次Flow配下に統一する。"
    - id: "create_requirements_file"
      detail: "タスクリスト生成と同時に {{patterns.flow_day_dir}}/draft_requirements.md（例: Flow/{{meta.year_month}}/{{meta.today}}/{{meta.agent_dir}}/draft_requirements.md）を create_markdown_file で作成し、ヒアリング結果と合意事項の記録先を確保する。外部タスク機能利用時も必須とし、以降の作業で常に参照・更新する。"
    - id: "sync_tasklist_with_requirements"
      detail: "各タスク完了時に Flow/{{meta.year_month}}/{{meta.today}}/{{meta.agent_dir}}/{{meta.today}}_agent_creation_tasklist.md と {{patterns.draft_requirements}} の双方へ反映内容・判断・未決事項を追記し、ステータスと要件メモの差分を残さないよう同期する。"
    - id: "configure_root_path"
      detail: "`{domain}_paths.mdc` の `root: \"{{templates.root_dir}}/{{agent_name}}\"` を、実際にエージェントフォルダを配置するフルパス（例: `/Users/you/workspace/{{agent_info.domain}}_agent`）へ書き換える。タスクリストに設定したパスを記録し、# ---- 0. ルートディレクトリ コメントに同じ値を残す。"
    - id: "collect_requirements"
      detail: "ヒアリングで得た要件を {{patterns.draft_requirements}} に整理し、タスクリストと同期を取る。"
    - id: "confirm_initial_structure"
      detail: "Flow / Stock / Archived を初期構成として説明し、エージェント要件とフォルダ設計の双方について承認を得る。承認が得られない場合は後続工程へ進まない。"
    - id: "directory_alignment"
      detail: "ディレクトリ構成と {domain}_paths.mdc の整合を確認・調整する。"
    - id: "draft_domain_rules"
      detail: "01_{domain}_initialization.mdc を起点に番号順で NN_{domain}_*.mdc を整備し、質問・テンプレート・アクション・保存先の候補を確定させる。この段階では {domain}_paths.mdc / 00_master_rules.mdc に手を入れず、必要なキーとトリガーをメモしておく。"
    - id: "rule_customization"
      detail: "01番以降のルール整備を終えてから 00_master_rules.mdc と {domain}_paths.mdc を更新し、マスタートリガーとパス定義を反映する。"
    - id: "finalize_master_and_paths"
      detail: "すべての 01〜NN ルールで保存パターンとトリガーが確定した最終局面で {domain}_paths.mdc と 00_master_rules.mdc を一括で整備し、Flow/{{meta.year_month}}/{{meta.today}}/{{meta.agent_dir}} タスクリストに完了記録を残す。"
    - id: "cleanup_sample_rules"
      detail: "テンプレートコピー後に残ったサンプルルールファイル（01_sample_*.mdc など）を削除する。"
    - id: "post_completion_choice"
      detail: "ブラッシュアップ継続か、生成フォルダ単体のプライベートGit化かを確認する。"
agent_creation_workflow:
  overview:
    phase_sequence:
      - order: 1
        name: "Discovery"
        purpose: "ヒアリングと要件定義を実施し、合意内容をドキュメント化する。"
      - order: 2
        name: "Build"
        purpose: "スクリプトとテンプレートを用いてルール・パス・ドラフトを整備する。"
      - order: 3
        name: "Validation"
        purpose: "`scripts/validate_rules.py` で構文・パスの整合を確認し、エラーを修正したうえで結果をログ化する。"
      - order: 4
        name: "Release"
        purpose: "バリデーション結果を反映した状態でエージェントを運用に移行するか、追加改善を計画するかを決定する。"
    final_adjustment_note: "output/{{agent_info.domain}}_agent/.cursor/rules/ で最終調整を行い、Flow→Stock移行を準備する。Flow / Stock / Archived 以外の構成が必要な場合は、この段階でディレクトリと `{domain}_paths.mdc` の同期を確認し、合意した階層に揃える。"
  scenarios:
    - id: "scenario_standard"
      condition: "初回ヒアリングからエージェント生成までを一気通貫で進める標準フロー"
      steps:
        - order: 1
          name: "ヒアリング準備"
          tasks:
            - "作業開始直後に create_markdown_file を用いて Flow/{{meta.year_month}}/{{meta.today}}/{{meta.agent_dir}}/{{meta.today}}_agent_creation_tasklist.md と {{patterns.draft_requirements}} を生成し、初回ヒアリング内容と承認事項の記録基盤を整える。"
            - "{{patterns.flow_day_dir}}/agent_discovery_brief.md を作成し、課題・対象ユーザー・期待成果を整理する。"
            - "既存資料があれば gather_existing_info を実行し、参照元リンクと取得日時を記録する。"
            - "関連ドメインの業界標準フレームワークを確認し、Flow/{{meta.year_month}}/{{meta.today}}/{{meta.agent_dir}}/framework_research.md を作成・記入する（出典URL・取得日時・要点・適用方針）。完了後、タスクリストに framework_research_done=true を記録する。未完了の場合は次工程へ進まない。"
        - order: 2
          name: "要件定義セッション"
      tasks:
        - "目的・KPI・成功条件を質問し記録する。"
        - "想定利用シナリオと成果物フォーマットを確認する。"
        - "利用予定データソース・外部システム・権限条件を確認する。"
        - "不確定事項を TODO: 形式で列挙し、合意時刻（例: {{meta.timestamp}}）を明記する。"
        - "ヒアリング内容を補完するため、業界標準フレームワークや最新トレンドを Web検索・文献調査で再確認し、出典と取得日時を {{patterns.draft_requirements}} に記録する。"
        - order: 3
          name: "仮設計ドキュメント化"
          tasks:
            - "{{patterns.draft_requirements}} に要件をまとめる。"
            - "必要に応じて {{patterns.draft_project_plan}} を作成する。"
            - "トリガー名称・テンプレート構造・主要ステップ案を整理し、コメントは {{patterns.flow_day_dir}} に残す。"
        - order: 4
          name: "ビルド準備と実行前チェック"
          tasks:
            - "目的・主要利用者・成果物・ドメイン用語が確定しているか確認する。"
            - "要件とフォルダ構成への承認が得られているか確認し、未承認の場合はこのステップで調整を完了させる。"
            - "scripts/enhanced_generate_agent.py を必ず使用して生成する（引数: --agent-name, --domain, --description）。"
            - "output/{agent_name}_agent/ が既存プロジェクトと競合しないことを確認する。"
            - "Flow / Stock / Archived を初期構成として案内し、この構成でドキュメント管理を進めてよいかユーザーに確認する。別構成案があればその要件を整理しタスクリストへ登録する。"
            - "フォルダ構成やエージェント要件について承認が得られない場合は、01_initialization で生成するディレクトリが最初のアクションになることを説明し承認を得る。"
        - order: 5
          name: "スケルトン生成"
          command:
            language: "bash"
            snippet: |
              scripts/enhanced_generate_agent.py --agent-name "Movie" --domain "movie" --description "映画調査・レビュー・サジェストエージェント"
        - order: 6
          name: "生成直後の必須作業"
          tasks:
            - "output/{agent_name}_agent/.cursor/rules/ に移動して作業を開始する。"
            - ".cursor/rules/agent_paths.mdc を {domain}_paths.mdc にリネームする。"
            - "template_paths.mdc を削除して参照衝突を防ぐ。"
            - "`templates.root_dir` および `root: \"{{templates.root_dir}}/{{agent_name}}\"` が実行環境の出力先を指すよう更新し、設定値をタスクリストに記録する。"
            - "要件定義で合意したフォルダ構成を {domain}_paths.mdc のコメントにメモし、保存先キーは 01〜ルールの確定後に本編集することを宣言する。"
            - "Stock 配下に `programs/{{project}}/documents/{{document_genre}}/` と `programs/{{project}}/images/{{image_category}}/` を初期生成（例: {{patterns.stock_documents_dir}} / {{patterns.stock_images_dir}}）し、エージェント要件に合わせてジャンルや画像カテゴリを柔軟に設定できる箱を整備する。"
            - "生成済みの Flow/{{meta.year_month}}/{{meta.today}}/{{meta.agent_dir}}/{{meta.today}}_agent_creation_tasklist.md に root設定や確認事項を追記し、進捗管理を継続する。"
            - "作成済み {{patterns.draft_requirements}} にヒアリング内容と仮設計を逐次追記する。"
            - "01_{domain}_initialization.mdc から順に NN_{domain}_*.mdc を整備し、質問・テンプレート・アクション・出力パターンを確定させる。"
            - "02番以降のルールは初期化完了後に要件へ沿って順次設計・実装する計画を立て、タスクリストへ反映する。"
            - "02番以降で扱う成果物ごとに、保存パターンを 01〜NN ルールで確定させてから `{domain}_paths.mdc` の patterns セクションへ追加する。"
            - "01〜NN が揃った段階で 00_master_rules.mdc と {domain}_paths.mdc をまとめて更新し、説明・globs・master_triggers・パス定義を最終反映する。"
            - "99_rule_maintenance.mdc のログ/スケルトン/タスクリスト参照パターンを生成エージェントの Flow/Stock 構造に合わせて編集し、対応キーを {domain}_paths.mdc に追加する（旧パスの参照はここで除去する）。"
            - "master_triggers を含むマスタールール全体の整形・不要トリガー削除・番号整合を完了させてから次工程に進む。"
            - "97_flow_to_stock_rules.mdc / 98_flow_assist.mdc / 99_rule_maintenance.mdc を対象エージェントのパス・質問・運用プロセスで上書きする。"
            - "テンプレートに同梱されているサンプルルール（01_sample_*.mdc 等）が残っている場合は、このタイミングで削除する。"
            - "初期の Flow / Stock / Archived 構成で問題ないかユーザーに再確認し、調整が必要なら階層と `{domain}_paths.mdc` を更新し、タスクリストの進捗を完了にする。"
        - order: 7
          name: "バリデーション実行"
          tasks:
            - "output/{{agent_info.domain}}_agent/ に移動し、` scripts/validate_rules.py` を実行してエラー内容を確認する。"
            - "検証結果を {{patterns.rule_check_log}} に記録し、必要な修正があれば該当ルールを更新する。"
            - "修正後は再度 `scripts/validate_rules.py` を実行し、エラー解消状況をログに追記する。"
        - order: 8
          name: "改善タスク整理"
          tasks:
            - "検証結果とヒアリングメモを突き合わせ、{{patterns.backlog_root}} 等の管理票へ改善タスクを登録する。"
            - "重要な判断・未決事項を Flow/{{meta.year_month}}/{{meta.today}}/{{meta.agent_dir}}/{{meta.today}}_agent_creation_tasklist.md と {{patterns.draft_requirements}} の双方へ同期する。"
            - "必要に応じて 00_master_rules.mdc や NN_{domain}_{function}.mdc を更新し、変更理由と反映日をコメントに残す。"
        - order: 9
          name: "完了判定と運用移行"
          tasks:
            - "ドラフトが整った成果物を Flow から Stock へ移行するか判断し、97番台ルールを用いて確定版を保存する。"
            - "ユーザーと協議し、ブラッシュアップ継続か生成フォルダ単体のプライベートGit運用かを決定する。"
            - "選択した運用方針をタスクリストと {{patterns.draft_requirements}} に記録し、次サイクルで参照できるようにする。"
  task_tracking:
    description: "進捗を可視化するためのチェックリスト。ユーザーと共有しながら、Cursor などタスクリスト機能を持つ環境ではそちらを活用する。"
    items:
      - id: "root_path_configured"
        detail: "`templates.root_dir` と `root: \"{{templates.root_dir}}/{{agent_name}}\"` が実行環境に合わせて設定され、タスクリストに記録されているか。"
      - id: "tasklist_confirmation"
        detail: "Flow / Stock / Archived 初期構成の承認を得たか。"
      - id: "directory_setup"
        detail: "{domain}_paths.mdc とディレクトリ構成の整合を取ったか。"
      - id: "requirements_doc_ready"
        detail: "要件定義ファイルが create_markdown_file で生成され、最新のヒアリング内容が反映されているか。"
      - id: "tasklist_requirements_synced"
        detail: "各タスク更新時にタスクリストと {{patterns.draft_requirements}} の内容が同期され、差分が残っていないか。"
      - id: "rule_customization"
        detail: "00/01-99 のルールをドメイン仕様に合わせて更新したか。"
      - id: "feedback_actions"
        detail: "評価・改善タスク・完了後の運用方針確認まで実施したか。"
      - id: "validation_log_created"
        detail: "` scripts/validate_rules.py` を実行し、結果を {{patterns.rule_check_log}} に記録したか。"
      - id: "framework_research_logged"
        detail: "Flow/{{meta.year_month}}/{{meta.today}}/{{meta.agent_dir}}/framework_research.md を作成・記入し、タスクリストに framework_research_done=true を記録したか。未完了なら次工程へ進まない。"
  feedback_cycle:
    steps:
      - id: "validation_script"
        name: "ルールバリデーション"
        tasks:
      - "出力されたエージェントフォルダ（例: `output/{{agent_info.domain}}_agent/`）に移動し、` scripts/validate_rules.py` を実行して結果を確認する。"
          - "出力内容を {{patterns.rule_check_log}} に記録し、エラーが出た場合は該当ファイルを修正したうえで再実行する。"
      - id: "improvement_tasks"
        name: "改善タスク管理"
        tasks:
          - "{{patterns.backlog_root}} 等の管理票に改善タスクを登録し、完了条件と期限を明示する。"
          - "再発する課題は Flow の該当日付ディレクトリに原因分析メモを残す。"
      - id: "rule_update"
        name: "ルール更新と再配布"
        tasks:
          - "00_master_rules.mdc と該当する NN_{domain}_{function}.mdc を改訂し、変更理由と反映日を記録する。"
          - "Flow→Stock ルール（97番台）を用いて確定ドキュメントへ移行し、97/98/99番台の内容がエージェント固有の要件と整合するか確認する。"
      - id: "post_completion_decision"
        name: "完了後の運用方針確認"
        tasks:
          - "ユーザーに、再対話によるブラッシュアップ継続か `output/` 配下に生成されたエージェントフォルダ（例: `output/movie_agent/`）のみを用いたプライベートGitリポジトリ作成のどちらを希望するか確認する。"
          - "ブラッシュアップを選択した場合は対話を続け、反映内容を Flow 側ドラフトに落とし込む。"
          - "プライベートリポジトリを選択した場合は対象フォルダのみを新規リポジトリとして初期化し、リモートをプライベート設定で作成・push する。"
  master_trigger_registration:
    guidelines:
      - "トリガーは # ========================= / 1–N. Domain Rules (01–89) / ========================= 配下に追加する。"
      - "開始メッセージ・既存情報収集・質問呼び出し・成果物作成・完了メッセージの5ステップを最低構成とする。"
      - "Discoveryで確定した命名規則を反映し、pathは {{patterns.xxx}}、template_reference は NN_{domain}_{function}.mdc => セクション名 に統一する。"
    example:
      language: "yaml"
      snippet: |-
        master_triggers:
          # -----
          # 映画分析フェーズ (A-01. movie_analysis)
          # -----
          - trigger: "(映画分析|映画調査|映画レビュー|movie analysis)"
            priority: high
            steps:
              - name: "start_movie_analysis"
                action: "message"
                content: "**映画分析フェーズを開始します。**\n\n必要な情報を順次お聞きしますので、具体的にご回答ください。"
              - name: "collect_existing_info"
                action: "gather_existing_info"
              - name: "ask_movie_analysis_questions"
                action: "call 01_movie_analysis.mdc => movie_analysis_questions"
              - name: "create_analysis_draft"
                action: "create_markdown_file"
                path: "{{patterns.draft_movie_analysis}}"
                template_reference: "01_movie_analysis.mdc => movie_analysis_template"
              - name: "completion_message"
                action: "message"
                content: "**映画分析フェーズを完了しました。**\n\n保存場所: `{{patterns.draft_movie_analysis}}`\nレビュー後に必要な対応を実施してください。"


# =========================
# 生成されるエージェント構造（配置の統一）
# =========================


repo_root/                                 # このリポジトリ直下
├── Flow/                                  # 作業中ドラフト（年月日＋エージェント名で階層管理）
│   └── YYYYMM/
│       └── YYYYMMDD/
│           └── {agent_dir}/               # 例: vtuber_agent
│               ├── draft_requirements.md  # 要件定義（初期必須）
│               ├── draft_*.md             # 01〜ルールで生成されるドラフト
│               └── rule_check_*.md        # 構造チェックログなど
└── output/
    └── {domain}_agent/                    # エージェント本体（確定物＋ルール）
        ├── .cursor/
        │   ├── rules/                     # .mdc追加先（新規ルールはここへ追加・編集）
        │   │   ├── 00_master_rules.mdc    # ドメイン用マスター（トリガー定義・編集先）
        │   │   ├── {domain}_paths.mdc     # パス辞書（例: vtuber_paths.mdc）
        │   │   ├── 01_{domain}_initialization.mdc
        │   │   ├── 02_{domain}_{function}.mdc
        │   │   └── ...                    # 03〜89_{domain}_{function}.mdc を追加
        │   └── templates/
        ├── Stock/                         # 確定版ドキュメント
        │   └── programs/{project}/
        │       ├── documents/{document_genre}/
        │       ├── images/{image_category}/
        │       ├── audio/{audio_category}/
        │       ├── videos/{video_category}/
        │       ├── data/{dataset_category}/
        │       └── archives/{archive_category}/
        ├── Archived/                      # アーカイブ（履歴保管）
        │   └── keep
        ├── scripts/
        └── README.md

方針
- Flowは常にリポジトリ直下の`Flow/`で日次管理する（要件定義・ドラフト・検証ログを含む）。
- ルール(.mdc)は常に`output/{domain}_agent/.cursor/rules/`で作成・編集する（テンプレ側との混在禁止）。
- Stock/Archivedは`output/{domain}_agent/`配下に保持し、Flow確定後に移行する。


# =========================
# アーキテクチャ
# =========================

### ルール番号体系
architecture:
  rule_numbering:
    categories:
      - range: "00"
        label: "Master Control Rules"
        description: "ドメイン固有マスタールール"
      - range: "01-89"
        label: "Domain Specialized Rules"
        description: "各ドメインエリアのルール"
      - range: "97"
        label: "Flow to Stock Rules"
        description: "ドキュメント確定・移行"
      - range: "98"
        label: "Flow Assist"
        description: "ブレインストーミング支援"
      - range: "99"
        label: "Rule Maintenance"
        description: "ルール保守・ブラッシュアップ（生成後の対話編集と新規スケルトン作成を含む）"
    note: |-
      01番ルールはプロジェクト初期化（PMBOKの立上げプロセスに相当）を担い、Flow/Stock/Archived の基礎ディレクトリと初期ドキュメントを整備する。
      97/98/99番台はテンプレ共通ひな型のため、派生エージェントでは固有の Flow/Stock 構造・paths・運用フローに合わせて必ず更新する。


# =========================
# 全体像クイックリファレンス
# =========================

quick_reference:
  phases:
    - order: 1
      name: "Phase 1: 設計準備"
      focus: "ドメイン分析・要件定義・機能設計を整理し、成功基準とKPIを合意する。root設定(`templates.root_dir`/`root: \"{{templates.root_dir}}/{{agent_name}}\"`)、初回作成タスクリスト、要件定義ファイルをここで生成し連携させる。"
      deliverables:
        - "Flow/{{meta.year_month}}/{{meta.today}}/{{meta.agent_dir}}/{{meta.today}}_agent_creation_tasklist.md（Markdownタスクリスト）"
        - "要件定義メモ"
        - "Flow/{{meta.year_month}}/{{meta.today}}/{{meta.agent_dir}}/{{meta.today}}_agent_creation_tasklist.md（root設定と承認事項を記録）"
        - "{{patterns.draft_requirements}}（ヒアリング内容と合意事項）"
        - "業界標準フレームワーク調査ログ（Web検索結果・文献出典・取得日時）"
    - order: 2
      name: "Phase 2: ルール実装"
      focus: "01〜15番のドメインルールをテンプレ準拠で先に整備し、その成果を踏まえて 00_master_rules.mdc と {domain}_paths.mdc を仕上げる。要件定義ファイルを参照しながら機能を落とし込み、02番以降の各ルールは成果物ファイルの格納パターン（{{patterns.output_*}} 等）を `{domain}_paths.mdc` に追加して Flow/Stock/Archived の保存先を明示する。"
      deliverables:
        - ".cursor/rules/*.mdc"
        - "{domain}_paths.mdc に追記した出力パターン一覧"
    - order: 3
      name: "Phase 3: 品質保証"
  focus: "`scripts/validate_rules.py` で全ルールの構文・パスコメントを検証し、エラーが出た場合は修正して再実行する。検証結果は {{patterns.rule_check_log}} に保存し、要件定義ファイルと照合して不足・差分を特定する。"
      deliverables:
        - "バリデーションレポート（{{patterns.rule_check_log}}）"
    - order: 4
      name: "Phase 4: 継続改善"
      focus: "レビュー専用ルールで改善サイクルを運用し、Flow→Stock の証跡と改善バックログを残す。ユーザーと協議し、ブラッシュアップ継続か生成フォルダ単体のプライベートGit運用かを決定する。"
      deliverables:
        - "レビュー報告"
        - "改善タスクリスト"
  master_rule_trigger_template:
    usage_note: "00_master_rules.mdc のドメインルール帯に追加する完全フォーマット"
    snippet: |-
      ### {機能名}
      - trigger: "({ドメイン固有トリガー}|{同義語}|{英語表記})"
        priority: high
        steps:
          - name: "start_message"
            action: "message"
            content: "**{機能名}を開始します。**\n\n必要な情報を順次お聞きしますので、可能な限り具体的にお答えください。"
          - name: "collect_existing_info"
            action: "gather_existing_info"
          - name: "create_framework_log"
            action: "create_markdown_file"
            path: "Flow/{{meta.year_month}}/{{meta.today}}/{{meta.agent_dir}}/framework_research.md"
            template_reference: "00_master_rules.mdc => framework_research_template"
          - name: "framework_research_gate"
            action: "conditional_step"
            parameters:
              condition: "{{framework_research_done}} == true"
              true_action: "call 0X_{domain}_{function}.mdc => {function}_questions"
              false_action: "message: 'フレームワーク調査ログが未完了です。Flow/{{meta.year_month}}/{{meta.today}}/{{meta.agent_dir}}/framework_research.md を記入し、framework_research_done=true を指定して再実行してください。'"
          - name: "create_output"
            action: "create_markdown_file"
            path: "{{patterns.output_{document_type}}}"
            template_reference: "0X_{domain}_{function}.mdc => {function}_template"
          - name: "completion_message"
            action: "message"
            content: "**{機能名}を完了しました。**\n\n保存場所: `{{patterns.output_{document_type}}}`\n\n【Flowワークフローの場合】\n- ドラフトを確認・編集してください\n- 完成したら「Stock移行」で確定版へ\n\n【直接変換の場合】\n- ファイルは即座に使用可能です"


#### 使用可能なactionの完全リスト
available_actions:
  - name: "message"
    schema:
      action: "message"
      required_fields:
        - "content"
    usage_note: "ユーザーに通知や案内を出す。"
  - name: "call"
    schema:
      action: "call"
      parameters:
        file_reference: "ファイル名.mdc => セクション名"
    usage_note: "別ファイルの質問・テンプレートを呼び出す。"
  - name: "create_markdown_file"
    schema:
      action: "create_markdown_file"
      parameters:
        path: "{{patterns.パターン名}}"
        template_reference: "ファイル名.mdc => テンプレート名"
    usage_note: "テンプレートを適用してMarkdownを生成する。"
  - name: "gather_existing_info"
    schema:
      action: "gather_existing_info"
    usage_note: "既存情報を収集し、作業の文脈を整理する。"
  - name: "execute_shell"
    schema:
      action: "execute_shell"
      parameters:
        command: "mkdir -p {{patterns.flow_day_dir}}/{{meta.agent_dir}} {{patterns.stock_documents_dir}} {{patterns.stock_images_dir}} Archived/keep"
    usage_note: "外部コマンドを実行し、環境やファイルを整備する。"
  - name: "create_directory"
    schema:
      action: "create_directory"
      parameters:
        path: "{{patterns.パターン名}}"
    usage_note: "指定パターンに基づいてディレクトリを作成する。"
  - name: "validate_input"
    schema:
      action: "validate_input"
      parameters:
        validation_rules: "required_fields: [field1, field2]"
    usage_note: "入力値の必須項目を検証する。"
  - name: "conditional_step"
    schema:
      action: "conditional_step"
      parameters:
        condition: "{{field_name}} != empty"
        true_action: "call ファイル名.mdc => セクション名"
        false_action: "message: '情報が不足しています'"
    usage_note: "条件に基づいて処理を分岐させる。"
  - name: "conditional_step"
    schema:
      action: "conditional_step"
      parameters:
        condition: "{{field_name}} != empty"
        true_action: "call ファイル名.mdc => セクション名"
        false_action: "message: '情報が不足しています'"
    usage_note: "条件に基づいて処理を分岐させる。"

# =========================
# 実装必須ポイント
# =========================

implementation_requirements:
  fundamentals:
    structure_rules:
      - "trigger: 複数の表記を | で区切って包括的に設定する。"
      - "priority: high/medium/low で優先度を設定する。"
      - "steps: 最低5ステップで構成する。"
    default_step_flow:
      - order: 1
        action: "start_message"
        description: "開始メッセージを提示する。"
      - order: 2
        action: "collect_existing_info"
        description: "既存情報を収集し最新状況を把握する。"
      - order: 3
        action: "ask_questions"
        description: "対象セクションの質問を実行する。"
      - order: 4
        action: "create_output"
        description: "テンプレートに基づき成果物ファイルを作成する。"
      - order: 5
        action: "completion_message"
        description: "完了メッセージを通知する。"
    file_creation_patterns:
      - type: "Flowワークフロー"
        sequence:
          - "ドラフト作成"
          - "確認・編集"
          - "Stock移行"
      - type: "直接変換"
        sequence:
          - "入力内容を最終ファイルに直接反映する"
    parameter_rules:
      - "path は {{patterns.xxx}} 形式で参照する。"
      - "template_reference は ファイル名.mdc => セクション名 形式で統一する。"
      - "content 内の改行は \n\n で明確に区切る。"
      - "`templates.root_dir` と `root: \"{{templates.root_dir}}/{{agent_name}}\"` の設定内容を Flow/{{meta.year_month}}/{{meta.today}}/{{meta.agent_dir}} タスクリストに記録し、全ルールが同一の出力先階層を参照するようにする。"
      - "02番以降のルールで新たな成果物を生成する場合は、`{domain}_paths.mdc` の patterns に `output_` プレフィックスでファイル名・ディレクトリを定義してからトリガーへ参照させる。"
    error_prevention:
      - "ファイル名は作成する01〜15番のファイルと一致させる。"
      - "パスパターンは {domain}_paths.mdc で定義されたキーを使用する。"
      - "セクション名は対応する NN_{domain}_{function}.mdc 内のセクションと一致させる。"
  format_standards:
    master_rule:
      items:
        - "フロントマター (---) と path_reference: '{domain}_paths.mdc' を保持する。"
    - "ai_instructions に安全対策・構造厳守・失敗報告・書式方針を明記する。"
    - "特に以下の4項目はテンプレ生成時の既定文として必ず残し、追記する場合も削除・改変しない。"
      - "\"すべてのルールは正確に実行し、独自の解釈で変更しないこと\""
      - "\"execute_shellアクションのコマンドは一切変更せずそのまま実行すること\""
      - "\"指定されたファイルパスやフォルダ構造を尊重し、勝手に構造を変更しないこと\""
      - "\"失敗した場合でも代替手段を取らず、失敗を報告してユーザーの指示を仰ぐこと\""
        - "タイトル帯は # ========================================================== を用いる。"
        - "ドメインルール帯は任意だが master_triggers を一元管理する。"
    individual_rules:
      items:
        - "フロントマター (---) と path_reference: '{domain}_paths.mdc' を記載する。"
        - "タイトル帯は # ==========================================================\n# NN_{domain}_xxxx.mdc - タイトル\n# ========================================================== とする。"
        - "Phase帯は # ======== Phase N: 説明 ======== を必要数配置する。"
        - "下位区切りには # ----- Questions ----- / # ----- Templates ----- を使用する。"
      question_schema: |-
        some_questions:
          - category: "カテゴリ名"
            items:
              - key: "field_key"
                prompt: "質問文"
                type: "text|multiline"
                required: true|false
      template_rule: "*_template: | 形式で即使用可能なテンプレートを定義する。"
    naming_conventions:
      - "00: 00_master_rules.mdc"
      - "01〜: NN_{domain}_{function}.mdc（NNは2桁ゼロ埋め）"
      - "参照は call NN_{domain}_{function}.mdc => section_name を使用する。"
    generation_script_notes:
      - "enhanced_generate_agent.py は 00_master_rules.mdc を規格準拠で生成する。"
      - "01〜番ファイルは箱のみ提供されるため本規約に沿って手作業で整備する。"
  creation_checklist:
    - "フロントマターと path_reference を必ず記載する。"
    - "タイトル帯・Phase帯・下位区切りを規格通りに配置する。"
    - "質問は prompt/type/required 形式で定義する。"
    - "テンプレートは即使用可能な品質に仕上げる。"
    - "00 の ai_instructions に新規ルール書式方針を明記する。"
  master_rule_structure_guide:
    - "フロントマターと globs を保持し path_reference と ai_instructions を管理する。"
    - "ai_instructions の直後に master_triggers を配置しドメイントリガーを追記する。"
    - "ステップ構成はテンプレ例を基準に必要なトリガーのみ追加・修正する。"
    - "01〜89番向けのプロンプトや Phase 構造は追加しない。"
    - "コメントブロックはテンプレ形式を維持し文言のみ調整する。"
  standard_format_requirements:
    prompt_section_template: |-
      # ======== プロンプト（目的と使い方） ========
      prompt_purpose: |
        ＜このルールの目的を1-2文で明確化。誰の意思決定を、何のために、どの成果物で支援するか＞
      prompt_why_questions: |
        ＜なぜ質問が必要か／何を揃えるかを1-4行で＞
      prompt_why_templates: |
        ＜テンプレートを使う理由（1-3行）＞
      prompt_principles: |
      　 ＜運用原則＞
    system_capabilities_template: |-
      # ======== {システム名}統合エージェント ========
      system_capabilities:
        capability_1: "機能1の詳細説明"
        capability_2: "機能2の詳細説明"
        capability_3: "機能3の詳細説明"
        capability_4: "機能4の詳細説明"
        capability_5: "機能5の詳細説明"
        capability_6: "機能6の詳細説明"
    phase_section_template: |-
      # ======== Phase 1: {フェーズ名}フェーズ ========
      phase_1_description: |
        {フェーズの目的と処理内容の詳細説明}
        {具体的な処理ステップの概要}
        {期待される成果物と品質基準}
      # ======== Phase 2: {フェーズ名}フェーズ ========
      phase_2_description: |
        {フェーズの目的と処理内容の詳細説明}
        {具体的な処理ステップの概要}
        {期待される成果物と品質基準}
    process_section_template: |-
      # ======== {システム名}プロセス ========
      {system_name}_steps:
        1_{process_name}:
          name: "{プロセス名}"
          phases:
            - "{詳細なプロセスステップ1}"
            - "{詳細なプロセスステップ2}"
            - "{詳細なプロセスステップ3}"
          {quality_standards/integration_points/automation_features}:
            - "{品質基準・統合ポイント・自動化機能}"
            - "{品質基準・統合ポイント・自動化機能}"
            - "{品質基準・統合ポイント・自動化機能}"
        2_{process_name}:
          name: "{プロセス名}"
          phases:
            - "{詳細なプロセスステップ1}"
            - "{詳細なプロセスステップ2}"
            - "{詳細なプロセスステップ3}"
          {quality_standards/integration_points/automation_features}:
            - "{品質基準・統合ポイント・自動化機能}"
            - "{品質基準・統合ポイント・自動化機能}"
            - "{品質基準・統合ポイント・自動化機能}"
    separator_rules:
      phase: "# ======== Phase X: {フェーズ名}フェーズ ========"
      section: "# ======== {セクション名} ========"
      subsection: "### {サブセクション名}"
    mandatory_sections:
      - "system_capabilities (6つの機能定義)"
      - "Phase 1 セクション (phase_1_description)"
      - "Phase 2 セクション (phase_2_description)"
      - "プロセスステップセクション ({system_name}_steps)"
      - "質問・テンプレート・ワークフローセクション"
    format_quality_criteria:
      - "統一性: 全ファイルで同一構造を維持する。"
      - "詳細性: 各セクションを実務レベルで具体化する。"
      - "専門性: ドメイン固有の専門知識を反映する。"
      - "統合性: 他ファイルとの連携ポイントを明確化する。"
    full_example:
      description: "01_{domain}_{function}.mdc の完全実装例"
      snippet: |-
        ---
        description: {ドメイン}における{機能名}システム
        globs:
        alwaysApply: false
        ---
        # ==========================================================
        # 01_{domain}_{function}.mdc - {機能名}システム
        # ==========================================================

        path_reference: "{domain}_paths.mdc"

        # ======== プロンプト（目的と使い方） ========
        prompt_purpose: |
          ＜このルールの目的を1-2文で明確化。誰の意思決定を、何のために、どの成果物で支援するか＞

        prompt_why_questions: |
          ＜なぜ質問が必要か／何を揃えるかを1-4行で＞

        prompt_why_templates: |
          ＜テンプレートを使う理由（1-3行）＞

        prompt_principles: |
        　 ＜運用原則＞
        # ======== {機能名}システム統合エージェント ========

        system_capabilities:
          core_function: "{機能の中核となる処理の詳細説明}"
          data_processing: "{データ処理・分析機能の詳細説明}"
          workflow_management: "{ワークフロー管理・自動化の詳細説明}"
          quality_assurance: "{品質保証・検証機能の詳細説明}"
          integration_support: "{他システム連携・統合の詳細説明}"
          user_experience: "{ユーザー体験・インターフェースの詳細説明}"

        # ======== Phase 1: {フェーズ1名}フェーズ ========

        phase_1_description: |
          {フェーズ1の目的と処理内容の詳細説明（3-4行）}
          {具体的な処理ステップの概要と期待される成果物}
          {品質基準と完了条件の明確化}

        # ======== Phase 2: {フェーズ2名}フェーズ ========

        phase_2_description: |
          {フェーズ2の目的と処理内容の詳細説明（3-4行）}
          {具体的な処理ステップの概要と期待される成果物}
          {品質基準と完了条件の明確化}

        # ======== 統合オプション質問 ========

        {function_name}_questions:
          - key: "question_key_1"
            prompt: "質問内容をここに記載："
            type: "text/multiline"
            required: true/false
            placeholder: "プレースホルダーテキスト"

        # ======== {機能名}プロセス ========

        {function_name}_steps:
          1_{process_name}:
            name: "{プロセス1名}"
            phases:
              - "{詳細なプロセスステップ1の説明}"
              - "{詳細なプロセスステップ2の説明}"
              - "{詳細なプロセスステップ3の説明}"
            quality_standards:
              - "{品質基準1}"
              - "{品質基準2}"
              - "{品質基準3}"

          2_{process_name}:
            name: "{プロセス2名}"
            phases:
              - "{詳細なプロセスステップ1の説明}"
              - "{詳細なプロセスステップ2の説明}"
              - "{詳細なプロセスステップ3の説明}"
            integration_points:
              - "{統合ポイント1}"
              - "{統合ポイント2}"
              - "{統合ポイント3}"

        # ======== {機能名}ワークフロー ========

        {function_name}_workflow:
          phase_1:
            - name: "{ワークフロー項目1}"
              action: "{action_name}"
              description: "{項目の説明}"
              mandatory: true

        # ======== テンプレート ========

        {function_name}_template: |
          # {テンプレート名} - {{meta.timestamp}}

          ## セクション1
          {{variable_name}}

          ---
          **文書情報**
          - 作成日: {{meta.timestamp}}
          - ドメイン: {domain}
          - エージェント: {AgentName}
          - 分類: {機能分類}

        # ======== エラーハンドリング ========

        error_handling:
          error_type_1:
            message: "エラーメッセージ"
            recovery_actions:
              - "回復アクション1"
              - "回復アクション2"

        # ======== 設定 ========

        {function_name}_settings:
          setting_1: "value"
          setting_2: "value"

        # ======== 統合ポイント ========

        integration_points:
          other_system:
            trigger: "trigger_condition"
            action: "integration_action"

        # ======== 品質保証 ========

        quality_assurance:
          mandatory_checks:
            - "チェック項目1"
            - "チェック項目2"

        # ======== 成功メトリクス ========

        success_metrics:
          - "メトリクス1 < 値"
          - "メトリクス2 > 値"
          - "メトリクス3 = 値"
  final_checklist:
    - "prompt_purpose / prompt_why_questions / prompt_why_templates / prompt_principles をすべて記載する。"
    - "目的を1-2文で明確化し質問理由とテンプレ理由を具体化する。"
    - "system_capabilities を6項目具体化する。"
    - "Phase 1・Phase 2 の description を3-4行で詳細に記述する。"
    - "{function_name}_steps に2つ以上のプロセスを含める。"
    - "区切り線 # ======== セクション名 ======== を統一する。"
    - "質問セクションに実用的な項目を定義する。"
    - "テンプレートを実際に使用可能な構造にする。"
    - "エラーハンドリングから成功メトリクスまで全セクションを網羅する。"
    - "framework_research.md の要点・適用方針を反映し、出典・取得日時を明示する。"
  compliance_note: "完全実装例に準拠しないファイルは品質不適合。外部参照なしでも本例だけで完成できること。"


# =========================
# プロンプトセクション適用手順
# =========================

prompt_section_policy:
  purpose: "各ルールの目的・質問理由・テンプレート役割・運用原則を明確化し、品質を標準化する。"
  scope:
    target_files:
      - "01〜89_{domain}_{function}.mdc"
    exclusions:
      - "パスファイル"
  placement:
    - "path_reference: '{domain}_paths.mdc' の直下"
    - "# ======== {システム名}統合エージェント ======== セクションの直前"
  writing_rules:
    language: "日本語（簡潔・断定）"
    prohibitions:
      - "推測表現（〜と思われる 等）"
      - "根拠のない補完"
    missing_value_policy: "情報が無い場合は『未記載』と明記する。"
  required_fields:
    - id: "prompt_purpose"
      description: "誰が・何のために・どの成果物で支援するかを1-2文で明確化する。"
    - id: "prompt_why_questions"
      description: "質問が必要な理由と揃える情報を1-4行で記載する。"
    - id: "prompt_why_templates"
      description: "テンプレートを使う理由を1-3行で説明する。"
    - id: "prompt_principles"
      description: "運用原則を箇条書きで示す（事実記録・欠損明示・根拠明記・ドメイン特有原則など）。"
  style_guidelines:
    - "短文・能動態・断定形（です／ます調）で記述する。"
    - "専門語は必要に応じて一般語に言い換える。"
    - "目的／質問理由／テンプレ役割／原則を必ず4点セットで記載する。"
    - "事実と意図を分離し、推測や根拠のない例示は避ける。"
  checklist:
    - "prompt_purpose / prompt_why_questions / prompt_why_templates / prompt_principles の4項目を全て記載。"
    - "目的は誰・何・なぜを1-2文で言い切る。"
    - "質問理由は収集する情報を具体的に記述する。"
    - "テンプレートの役割をFlow→Stockや外部共有など具体の利用シーンと結びつける。"
    - "運用原則に『未記載』『出典・日時・パス明示』などのルールを含める。"
    - "推測表現を含めない。"


# =========================
# フレームワーク調査テンプレート
# =========================

framework_research_template: |
  # フレームワーク調査ログ - {{meta.timestamp}}

  ## 参照フレームワーク
  - 名称: 
  - 公式/準拠元: 
  - URL: 
  - 取得日時: 

  ## 要点（業務観点）
  - 

  ## 本エージェントへの適用方針
  - 適用箇所:
  - 反映方法:
  - 除外/留意事項:

  ## 出典リスト（最低1件以上）
  - タイトル / URL / 取得日時

  ---
  - 保存先: Flow/{{meta.year_month}}/{{meta.today}}/{{meta.agent_dir}}/framework_research.md


# =========================
# エージェント生成後の必須01〜ルール作成ワークフロー
# =========================

post_generation_workflow:
  workflow:
    overview_steps:
      - order: 1
        name: "enhanced_generate_agent.py で基本構造とテンプレ資材をコピー"
        tasks:
          - "template/agent_base/ を参照し MANIFEST.yaml の copy_targets に従って .claude/・scripts/・.cursor/templates/ をコピーする。"
          - "template/agent_base/.cursor/templates/rules/ が存在すれば .cursor/rules/ へ優先コピーし、無い場合は .cursor/rules/ をフォールバックとする。"
          - "コピー後、99_rule_maintenance.mdc などの汎用メンテナンスルール文言を新エージェントに合わせて調整する。"
      - order: 2
        name: "output/{{agent_info.domain}}_agent/.cursor/rules/ でルールを作り込む"
        tasks:
          - "テンプレが無い場合は空ファイルから整備する。"
      - order: 3
        name: "output/{{agent_info.domain}}_agent/.cursor/rules/ 上で直接編集・保存"
        tasks:
          - "必ず .mdc 形式のまま管理する。"
  implementation_sequence:
    steps:
      - order: 1
        title: "エージェント生成"
        actions:
          - "scripts/enhanced_generate_agent.py を実行して骨格を生成する。"
      - order: 2
        title: "パスファイル整備"
        actions:
          - ".cursor/rules/agent_paths.mdc を {domain}_paths.mdc にリネームする。"
          - "template_paths.mdc を削除して参照衝突を防ぐ。"
          - "詳細なパターン追記は 01〜ルール整備完了後に行う。"
      - order: 3
        title: "01〜15番ルール作成"
        actions:
          - "01_{domain}_initialization.mdc から番号順に整備し、質問・テンプレート・アクションを確定する。"
          - "各ルールで参照する {{patterns.*}} キーを洗い出し、必要な出力パターンをまとめる。"
      - order: 4
        title: "00_master_rules.mdc 整備"
        actions:
          - "テンプレコメントを除去し、description / タイトル帯 / path_reference / globs をエージェント名に合わせて整える。"
          - "ai_instructions をエージェント固有の安全基準で書き直し、禁止事項・承認確認・欠損時対応を明記する。"
          - "master_triggers をフェーズ別のメッセージ→情報収集→質問→出力→完了メッセージ構成で再定義し、不要なテンプレ操作は削除する。"
          - "01〜ルールで決まった出力パターンに合わせて {domain}_paths.mdc の root / dirs / patterns を仕上げる。"
      - order: 5
        title: "レビューとコミット"
        actions:
          - "編集内容を確認し、必要に応じてテスト後コミットする。"
      - order: 6
        title: "ルールバリデーション"
        actions:
          - "出力エージェントフォルダ（例: `output/{{agent_info.domain}}_agent/`）へ移動し、`scripts/validate_rules.py` を実行する。"
          - "エラーが出たファイルを修正し、スクリプトを再実行して `All rule files passed validation.` になるまで繰り返す。"
          - "最終結果を Flow/{{meta.year_month}}/{{meta.today}}/{{meta.agent_dir}}/rule_check_{{meta.today}}.md とタスクリストに記録する。"
      - order: 7
        title: "動作テスト"
        actions:
          - "主要トリガーでワークフローを実行し、意図どおりの成果物が生成されるかを確認する。"
    important_notes:
      - "output/{{agent_info.domain}}_agent/.cursor/rules/ が実際に参照されるルール格納場所である。"
      - "97/98/99番台ルールはテンプレ汎用文言のため、エージェント固有のパス・質問・承認フローへ必ず置き換える。"
      - "01〜ルール整備で必要要素が出揃ってから {domain}_paths.mdc と 00_master_rules.mdc を更新し、ディレクトリ構成・master_triggers・メッセージをエージェント仕様に合わせる。"
  template_copy_priority:
    description: "enhanced_generate_agent.py でのテンプレ資材コピー優先順位"
    rules:
      - "template/agent_base/.cursor/templates/rules/ が存在する場合は output/{{agent_info.domain}}_agent/.cursor/rules/ へ優先コピーする。"
      - "存在しない場合は template/agent_base/.cursor/rules/ をフォールバックとして同宛先へコピーする。"
      - "コピー後、名称や文脈がエージェントに適合するよう文言を見直す。"
      - "テンプレに rules が無い場合は 01〜ルールを手作業で作成する。"
  domain_rule_creation:
    core_principles:
      - "機能数は01〜20の範囲でドメインに合わせて調整する。"
      - "実務で即利用できる詳細な質問・テンプレートを作成する。"
      - "業界標準フレームワークに準拠する。"
      - "Flow/{{meta.year_month}}/{{meta.today}}/{{meta.agent_dir}}/framework_research.md の要点・適用方針を各ルール（質問/テンプレート/指標/paths）へ反映する。ログ未整備時はルール追加を行わない。"
      - "01〜89番ルールは alwaysApply: false を設定する。"
      - "02番以降の各ルールでは、成果物の保存先・ファイル名を `{domain}_paths.mdc` に定義し、Flow/{{meta.year_month}}/{{meta.today}}/{{meta.agent_dir}} タスクリストで設定完了をチェックする。"
    function_patterns:
      base_examples:
        - "01_initialization: プロジェクト初期化（Flow/Stock/Archived 基礎フォルダと要件定義ファイル {{patterns.draft_requirements}} の生成、タスクリスト初期化を担当）"
        - "02〜08: ドメイン固有の主要業務機能"
        - "09〜12: 分析・評価機能"
        - "13〜15: 文書作成・報告機能"
    recommended_counts:
      BABOK: "10〜15機能"
      marketing: "8〜12機能"
      legal: "6〜10機能"
      hr: "8〜12機能"
      finance: "10〜15機能"
    implementation_policy: "実用性重視で15機能以内に収め、各機能群の完成度を優先する。"
    general_examples:
      - "02_requirements_analysis.mdc - 要件分析"
      - "03_design_documentation.mdc - 設計書作成"
      - "04_progress_report.mdc - 進捗報告"
      - "05_final_deliverable.mdc - 最終成果物"
    domain_examples:
      BABOK:
        description: "ビジネスアナリシス領域向け5ルール例"
        files:
          - "01_project_initiation.mdc - 初期化・体制構築"
          - "02_requirements_management.mdc - 要求抽出・検証"
          - "03_business_analysis.mdc - ビジネスケース・ステークホルダー分析"
          - "04_solution_design.mdc - ソリューション評価・データモデリング"
          - "05_implementation_control.mdc - 変更戦略・最終評価"
      marketing:
        description: "マーケティング領域向け4ルール例"
        files:
          - "01_market_intelligence.mdc - 市場/競合分析"
          - "02_strategy_planning.mdc - 戦略立案"
          - "03_campaign_execution.mdc - キャンペーン企画"
          - "04_performance_optimization.mdc - 効果測定・最適化"
      legal:
        description: "法務領域向け3ルール例"
        files:
          - "01_contract_management.mdc - 契約書レビュー"
          - "02_compliance_risk.mdc - コンプライアンス/リスク評価"
          - "03_policy_training.mdc - 規程策定・研修資料"
    implementation_principles:
      - "標準フォーマットを厳守する。"
      - "ドメイン特有のベストプラクティスを反映する。"
      - "実務で即利用可能な品質を確保する。"
      - "他ファイルとの連携ポイントを明確化する。"
    customization_points:
      - "trigger にドメイン固有語を追加する。"
      - "questions に業界特有の質問を含める。"
      - "template を業界標準の文書構造へ合わせる。"
      - "file_path をドメイン固有ディレクトリへ合わせる。"
    domain_path_examples:
      BABOK:
        path_patterns:
          - "draft_business_case"
          - "draft_stakeholder_analysis"
          - "draft_requirements_specification"
      marketing:
        path_patterns:
          - "draft_campaign_plan"
          - "draft_market_research"
          - "draft_competitor_analysis"
      legal:
        path_patterns:
          - "draft_contract_review"
          - "draft_compliance_check"
          - "draft_risk_assessment"
  master_rule_integration:
    note: "00_master_rules.mdc の A-01-XX. Domain Specific Rules にトリガーを追加する。"
    example_snippet: |-
      ## A-01-01. Project Initialization Rules

      ### プロジェクト初期化  
      - trigger: "({domain}プロジェクト開始|{domain}初期化|新規{domain}プロジェクト|プロジェクト開始)"
        priority: high
        steps:
          - name: "welcome_message"
            action: "message"
            content: "**{AgentName}エージェントを開始します。**

新しいプロジェクトの初期化を行います。基本情報をお聞きしますので、お答えください。"
          - name: "start_info_collection"
            action: "call 01_{domain}_initialization.mdc => project_init_questions"
            - name: "create_project_structure"
              action: "execute_shell"
              command: "mkdir -p {{patterns.flow_day_dir}}/{{meta.agent_dir}} {{patterns.stock_documents_dir}} {{patterns.stock_images_dir}} Archived/keep"
          - name: "create_readme"
            action: "create_markdown_file"
            path: "README.md"
            template_reference: "01_{domain}_initialization.mdc => project_readme_template"
          - name: "completion_message"
            action: "message"
            content: "**プロジェクトの初期化が完了しました。**

プロジェクト概要: `README.md`
作業ディレクトリ構造を作成済み

次のステップでは、具体的な{domain}業務を開始できます。"

      ### 要件分析
      - trigger: "(要件分析|要件定義|requirements analysis)"
        priority: high
        steps:
          - name: "start_requirements"
            action: "message"
            content: "**要件分析を開始します。**

現在の状況と要件について詳しくお聞きします。"
          - name: "collect_existing_info"
            action: "gather_existing_info"
          - name: "ask_requirements_questions"
            action: "call 02_requirements_analysis.mdc => requirements_analysis_questions"
          - name: "create_requirements_draft"
            action: "create_markdown_file"
            path: "{{patterns.draft_requirements}}"
            template_reference: "02_requirements_analysis.mdc => requirements_analysis_template"
          - name: "requirements_completion"
            action: "message"
            content: "**要件分析ドラフトを作成しました。**

保存場所: `{{patterns.draft_requirements}}`

内容を確認し、必要に応じて修正してください。完成したら「Stock移行」で確定版にできます。"

      ### 設計書作成
      - trigger: "(設計書作成|設計|design documentation)"
        priority: high
        steps:
          - name: "start_design"
            action: "message"
            content: "**設計書作成を開始します。**

設計に関する情報を詳しくお聞きします。"
          - name: "collect_existing_info"
            action: "gather_existing_info"
          - name: "ask_design_questions"
            action: "call 03_design_documentation.mdc => design_documentation_questions"
          - name: "create_design_draft"
            action: "create_markdown_file"
            path: "{{patterns.draft_design}}"
            template_reference: "03_design_documentation.mdc => design_documentation_template"
          - name: "design_completion"
            action: "message"
            content: "**設計書ドラフトを作成しました。**

保存場所: `{{patterns.draft_design}}`

技術的な詳細や図表を追加して完成させてください。"

      ### 進捗報告
      - trigger: "(進捗報告|progress report|状況報告)"
        priority: medium
        steps:
          - name: "start_progress"
            action: "message"
            content: "**進捗報告を開始します。**

現在の進捗状況についてお聞きします。"
          - name: "collect_existing_info"
            action: "gather_existing_info"
          - name: "ask_progress_questions"
            action: "call 04_progress_report.mdc => progress_report_questions"
          - name: "create_progress_draft"
            action: "create_markdown_file"
            path: "{{patterns.draft_progress_report}}"
            template_reference: "04_progress_report.mdc => progress_report_template"
          - name: "progress_completion"
            action: "message"
            content: "**進捗報告書を作成しました。**

保存場所: `{{patterns.draft_progress_report}}`

関係者への共有準備が整いました。"

      ### 最終成果物
      - trigger: "(最終成果物|final deliverable|最終報告)"
        priority: high
        steps:
          - name: "start_final"
            action: "message"
            content: "**最終成果物の作成を開始します。**

プロジェクトの総括と最終報告について詳しくお聞きします。"
          - name: "collect_existing_info"
            action: "gather_existing_info"
          - name: "ask_final_questions"
            action: "call 05_final_deliverable.mdc => final_deliverable_questions"
          - name: "create_final_draft"
            action: "create_markdown_file"
            path: "{{patterns.draft_final_report}}"
            template_reference: "05_final_deliverable.mdc => final_deliverable_template"
          - name: "final_completion"
            action: "message"
            content: "**最終成果物を完成しました。**

保存場所: `{{patterns.draft_final_report}}`

プロジェクトの完了報告として使用できます。お疲れ様でした。"
  path_patterns:
  usage_notes:
    - "draft_* は Flow ワークフロー用ドラフトパターン。"
    - "output_* は直接変換で即時利用する成果物。"
    - "stock_* は確定版の成果物。"
    - "`program` / `project` / `document_genre` は初期導入時に置き換えるプレースホルダ。未定の場合は `core_program` など仮称でディレクトリを作成し、合意後に更新する。"
    - "画像・音声・動画・データ・アーカイブのカテゴリ（`image_category` など）はエージェントのドメインに合わせた既定値へ必ず更新し、01〜ルール完成後に {domain}_paths.mdc の meta ブロックへ反映する。"
    - "プレースホルダ未設定時は `core_docs` / `core_images` / `core_audio` / `core_videos` / `core_datasets` / `core_archives` が初期値として使用される。エージェント作成時に必ず適切な値へ置き換える。"
    - "`agent_dir` は Flow 側の日付フォルダ直下に作成されるサブディレクトリ名で、通常はエージェント名のスネークケースを設定する。"
    - "`root: \"{{templates.root_dir}}/{{agent_name}}\"` は必ず実際のフルパスへ置き換える（例: `/Users/you/workspace/music_agent`）。プレースホルダのまま残さない。"
    - "`root: \"{{templates.root_dir}}/{{agent_name}}\"` における `templates.root_dir` は、エージェントフォルダを配置する実際の作業ディレクトリ（例: `/Users/you/workspace`）に差し替える。"
  snippet: |-
      patterns:
        flow_public_date: "Flow/{{meta.year_month}}/{{meta.today}}/{{meta.agent_dir}}"

        stock_program_dir: "Stock/programs"
        stock_project_dir: "{{stock_program_dir}}/{{project}}"
        stock_documents_dir: "{{stock_project_dir}}/documents/{{document_genre}}"
        stock_images_dir: "{{stock_project_dir}}/images/{{image_category}}"
        stock_audio_dir: "{{stock_project_dir}}/audio/{{audio_category}}"
        stock_video_dir: "{{stock_project_dir}}/videos/{{video_category}}"
        stock_data_dir: "{{stock_project_dir}}/data/{{dataset_category}}"
        stock_archive_dir: "{{stock_project_dir}}/archives/{{archive_category}}"
        docs_root: "{{stock_documents_dir}}"
        images_root: "{{stock_images_dir}}"
        audio_root: "{{stock_audio_dir}}"
        video_root: "{{stock_video_dir}}"
        data_root: "{{stock_data_dir}}"
        archive_root: "{{stock_archive_dir}}"
        stock_document: "{{docs_root}}/{{document_name}}.md"

        draft_document: "{{flow_public_date}}/draft_{{document_name}}.md"
        draft_project_plan: "{{flow_public_date}}/draft_project_plan.md"
        draft_requirements: "{{flow_public_date}}/draft_requirements.md"
        draft_design: "{{flow_public_date}}/draft_design.md"
        draft_progress_report: "{{flow_public_date}}/draft_progress_report.md"
        draft_final_report: "{{flow_public_date}}/draft_final_report.md"

        output_document: "{{docs_root}}/{{document_name}}.md"
        output_analysis: "{{docs_root}}/analysis_{{env.NOW:date:YYYY-MM-DD}}.md"
        output_report: "{{docs_root}}/report_{{env.NOW:date:YYYY-MM-DD}}.md"
        output_summary: "{{docs_root}}/summary_{{env.NOW:date:YYYY-MM-DD}}.md"
        output_image: "{{images_root}}/{{document_name}}.png"
        output_audio: "{{audio_root}}/{{document_name}}.mp3"
        output_video: "{{video_root}}/{{document_name}}.mp4"
        output_dataset: "{{data_root}}/{{document_name}}.csv"
        output_archive: "{{archive_root}}/{{document_name}}.zip"

        stock_project_plan: "{{docs_root}}/project_plan.md"
        stock_requirements: "{{docs_root}}/requirements.md"
        stock_design: "{{docs_root}}/design.md"
        stock_progress_report: "{{docs_root}}/progress_report.md"
        stock_final_report: "{{docs_root}}/final_report.md"
        rule_check_log: "{{patterns.flow_day_dir}}/rule_check_{{meta.today}}.md"
  manual_workflow:
    description: "完全手動作成ワークフローの10ステップ"
    steps:
      - "Taskリスト作成"
      - "01番ルール作成（プロジェクト初期化・フォルダ生成・初期成果物作成）"
      - "02〜15番ルール作成（要件に応じて順次設計）"
      - "00_master_rules.mdc 修正"
      - "パスファイル修正"
      - "動作テスト"
      - "`scripts/validate_rules.py` の実行と {{patterns.rule_check_log}} への結果保存"
      - "タスクリスト最終確認（未完了項目が無いことを確認）"
      - "ルール保存とコミット"
    notes:
      - "01番ルールは常にプロジェクト初期化（フォルダ生成・初期ドキュメント作成）を担い、PMBOKの立上げプロセスに相当する。"
      - "フォルダ構成と要件の承認を得るまで後続工程へ進まないこと。"
      - "02番以降のルールは要件定義の結果に応じて順次作成し、タスクリストで進捗管理する。"
  task_list_guidance:
    precondition: "すべての開発はTaskリスト作成から開始する。"
    stages:
      domain_analysis: |-
        domain_analysis_tasks:
          - task: "ドメイン業界標準調査"
            content: "対象ドメインの確立されたフレームワークを調査"
            deliverable: "業界標準フレームワーク一覧と適用可能性評価"
          - task: "現行業務プロセス分析"
            content: "実務フローとステークホルダーの特定"
            deliverable: "業務プロセスマップと関係者マトリックス"
          - task: "競合・類似ツール調査"
            content: "既存ツールの機能分析"
            deliverable: "競合分析レポートと差別化ポイント"
      requirements_definition: |-
        requirements_tasks:
          - task: "ターゲットユーザー定義"
            content: "利用者ペルソナと使用シーンの明確化"
            deliverable: "ユーザーペルソナとユースケース定義書"
          - task: "機能要件整理"
            content: "必須・推奨・将来機能の分類"
            deliverable: "優先度付き機能要件一覧"
          - task: "非機能要件定義"
            content: "性能・品質・制約事項の明確化"
            deliverable: "非機能要件仕様書"
          - task: "成功基準設定"
            content: "評価指標とKPIの設定"
            deliverable: "成功基準・KPI定義書"
      function_design: |-
        function_design_tasks:
          - task: "プロジェクト初期化ルール設計"
            content: "01_initialization ルールでディレクトリ生成・初期ドキュメント作成・TODO登録を扱う構成を固める"
            deliverable: "初期化タスク設計メモ"
          - task: "機能アーキテクチャ設計"
            content: "02〜15機能の構成と連携"
            deliverable: "機能アーキテクチャ図"
          - task: "ワークフロー設計"
            content: "Flow/直接変換パターンの選択"
            deliverable: "ワークフロー仕様書"
          - task: "質問・テンプレート設計"
            content: "実務で使用可能な質問とアウトプット設計"
            deliverable: "質問設計書とテンプレ仕様書"
          - task: "トリガー・アクション設計"
            content: "00_master_rules.mdc のトリガー設計"
            deliverable: "トリガー・アクション仕様書"
    compliance_checklist:
      syntax:
        - "YAML構文の正確性"
        - "ルール番号体系準拠"
        - "ファイル構造準拠"
        - "{{patterns.xxx}} 形式の正確な使用"
      flow_stock:
        - "Flow → Stock の文書管理フローを考慮"
        - "Flow の日付階層ディレクトリの運用ルール遵守"
        - "Archived による履歴管理"
      numbering:
        - "00: Master Control Rules"
        - "01〜89: Domain Specialized Rules"
        - "97: Flow to Stock Rules"
        - "98: Flow Assist"
        - "99: Rule Maintenance"
  implementation_priorities:
    phase1:
      summary: "必須基盤機能 (1-3ルール)"
      steps:
        - "01_core_functions: 基幹機能群"
        - "02_primary_workflow: 主要業務機能群"
        - "03_management_support: 管理支援機能群"
    phase2:
      summary: "中核業務機能 (4-8ルール)"
      details:
        - "ドメイン主要ワークフローを網羅"
        - "業界標準の必須プロセスをカバー"
    phase3:
      summary: "完成・評価機能 (9-15ルール)"
      details:
        - "分析・評価機能群"
        - "最終レポート・文書作成機能群"
        - "品質管理・完了確認機能群"
    strategy:
      - "Taskリスト完了後に実装を開始する。"
      - "まず3ルールでMVPを構築する。"
      - "段階的に15ルール以内でドメイン全体をカバーする。"
      - "各ルールは関連機能をまとめて実用レベルまで詳細化する。"
      - "フェーズ3完了後に ` scripts/validate_rules.py` を実行し、ルール整合を確認する。"
    design_flexibility:
      first_rule_patterns:
        - "パターンA（プロジェクト型）: 初期化 + 基本設定 + 構造作成"
        - "パターンB（単機能型）: 最重要単機能"
        - "パターンC（複合型）: 関連2-3機能の複合"
      combination_principles:
        - "機能的関連性でまとめる。"
        - "利用頻度の高い機能をセットにする。"
        - "アウトプット連携のある機能をまとめる。"
        - "同一トリガー・質問・テンプレートを共有できる機能をまとめる。"


# =========================
# エージェント品質検証フロー
# =========================

agent_quality_framework:
  validation_process:
    title: "ルールバリデーション"
    steps:
      - "出力エージェントフォルダ（例: `output/{{agent_info.domain}}_agent/`）に移動し、`scripts/validate_rules.py` を実行する。"
      - "エラーが出たファイルを修正し、スクリプトを再実行して `All rule files passed validation.` になるまで繰り返す。"
      - "最終結果を Flow/{{meta.year_month}}/{{meta.today}}/{{meta.agent_dir}}/rule_check_{{meta.today}}.md に保存し、対応内容をタスクリストへ反映する。"

# =========================
# 注意事項
# =========================

important_notes:
  - "業界標準フレームワークに必ず基づく。"
  - "機械的生成ではなく手作り品質を維持する。"
  - "生成後の手動修正は必須（自動生成は骨格のみ）。"
  - "ルールバリデーション（`scripts/validate_rules.py`）で整合を確認し、必要な修正を行うこと。"
  - "実務経験者による検証を推奨する。"


# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal. （ただし ` scripts/enhanced_generate_agent.py` の生成物は常に必要と見なす）
ALWAYS prefer editing an existing file to creating a new one. （ただしジェネレーターによるスキャフォルドは新規作成を許可）
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User. （ただしジェネレーターによる README/root.md 生成は常に許可）
<!-- FILE: 00_master_rules.mdc END -->

