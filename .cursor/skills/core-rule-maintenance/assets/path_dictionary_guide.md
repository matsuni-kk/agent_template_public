# パス辞書メンテナンスガイド

## 概要

CLAUDE.md Section 7 のパス辞書は、全Skillsが参照するファイルパスの定義集。変更時は整合性に注意。

---

## 構造

```yaml
root: "絶対パス（リポジトリルート）"

dirs:
  # ディレクトリの定義
  flow:           "{{root}}/Flow"
  stock:          "{{root}}/Stock"

patterns:
  # ファイルパスパターンの定義
  flow_date:      "{{patterns.flow_yearmonth}}/{{today}}"
  draft_charter:  "{{patterns.flow_date}}/draft_project_charter.md"

meta:
  # 動的変数の定義
  today:          "{{env.NOW:date:YYYY-MM-DD}}"
```

---

## 追加手順

### 1. dirsへの追加

```yaml
# 新しいディレクトリを追加
dirs:
  new_dir:        "{{root}}/NewDirectory"
  new_subdir:     "{{dirs.new_dir}}/SubDirectory"
```

**ルール**:
- 親ディレクトリを先に定義
- 既存のdirsを参照可能

### 2. patternsへの追加

```yaml
# 新しいパターンを追加
patterns:
  new_template:   "{{patterns.flow_date}}/new_template.md"
  new_report:     "{{patterns.doc_monitoring}}/new_report_{{today}}.md"
```

**ルール**:
- `{{patterns.xxx}}`で他のパターンを参照可能
- `{{dirs.xxx}}`でディレクトリを参照可能
- `{{today}}`等のmeta変数を参照可能

### 3. metaへの追加

```yaml
# 新しいメタ変数を追加
meta:
  new_variable:   "{{env.NEW_VAR}}"
```

---

## 命名規則

| カテゴリ | プレフィックス | 例 |
|----------|---------------|-----|
| ドラフト | draft_ | draft_charter, draft_wbs |
| Stock文書 | stock_ | stock_charter, stock_wbs |
| テンプレート | _template | daily_tasks_template |
| ディレクトリ | _dir | meetings_dir, annals_dir |
| レポート | _report | status_report, worklog_report |

---

## 変数参照の解決順序

```
1. meta（動的変数）
2. root（ルートパス）
3. dirs（ディレクトリ）
4. patterns（パターン）
```

**例**:
```
{{patterns.draft_charter}}
  → {{patterns.flow_date}}/draft_project_charter.md
  → {{patterns.flow_yearmonth}}/{{today}}/draft_project_charter.md
  → {{dirs.flow}}/{{today | slice: 0, 4}}{{today | slice: 5, 2}}/{{today}}/draft_project_charter.md
  → {{root}}/Flow/202601/2026-01-05/draft_project_charter.md
  → /Users/xxx/Desktop/pmbok-agent/Flow/202601/2026-01-05/draft_project_charter.md
```

---

## チェックリスト

追加・変更時は以下を確認:

- [ ] 変数名がユニーク
- [ ] 参照先が存在する
- [ ] 循環参照がない
- [ ] 命名規則に従っている
- [ ] 実パスとして有効
- [ ] 関連Skillsで使用されている場合、そのSkillも更新

---

## よくあるパターン

### プロジェクト関連

```yaml
program_dir:        "{{dirs.programs}}/{{program_id}}"
project_dir:        "{{patterns.program_dir}}/projects/{{project_id}}"
docs_root:          "{{patterns.project_dir}}/documents"
```

### フェーズ別ドキュメント

```yaml
doc_initiating:     "{{patterns.docs_root}}/1_initiating"
doc_planning:       "{{patterns.docs_root}}/3_planning"
doc_executing:      "{{patterns.docs_root}}/4_executing"
doc_monitoring:     "{{patterns.docs_root}}/5_monitoring"
doc_closing:        "{{patterns.docs_root}}/6_closing"
```

### 日付ベースのFlow

```yaml
flow_yearmonth:     "{{dirs.flow}}/{{today | slice: 0, 4}}{{today | slice: 5, 2}}"
flow_date:          "{{patterns.flow_yearmonth}}/{{today}}"
```
