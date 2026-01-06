# Core Rule Maintenance Questions

## 必須入力項目

### 1. 変更対象
- [ ] Section 1: コア原則
- [ ] Section 2: 成果物タイプと語調
- [ ] Section 3: 品質ゴール
- [ ] Section 4: Skill選択ポリシー
- [ ] Section 5: 成果物分類
- [ ] Section 6: ワークフロー索引
- [ ] Section 7: パス辞書
- [ ] AGENTS.md（Cursor専用）

### 2. 変更種別
- [ ] 追加（新規項目）
- [ ] 修正（既存項目の変更）
- [ ] 削除（既存項目の削除）

### 3. 変更内容
**具体的に記載してください**:
- 変更前:
- 変更後:
- 変更理由:

---

## セクション別の追加質問

### Section 6: ワークフロー索引の変更時

1. **対象Skill**: 追加/変更するSkill名は？
2. **フェーズ**: どのフェーズに配置？
   - [ ] Initiating
   - [ ] Discovery/Research
   - [ ] Planning
   - [ ] Executing
   - [ ] Decision
   - [ ] Monitoring
   - [ ] Closing
   - [ ] 横断プロセス
3. **連携先**: 連携するSkillは？（→ で接続する先）
4. **並列Skill**: 並列で使用可能なSkillは？（/ で接続）

### Section 7: パス辞書の変更時

1. **カテゴリ**: どのカテゴリに追加？
   - [ ] dirs（ディレクトリ）
   - [ ] patterns（ファイルパスパターン）
   - [ ] meta（動的変数）
2. **変数名**: 追加する変数名は？
3. **値/パス**: 設定する値は？
4. **参照先**: 参照する既存変数は？（例: `{{patterns.flow_date}}`）
5. **使用Skill**: このパスを使用するSkillは？

---

## 影響範囲の確認

### 関連Skills
この変更で影響を受けるSkillsをリストアップ:
-

### 関連パス
この変更で影響を受けるパス参照をリストアップ:
-

### 関連Subagents
この変更で影響を受けるSubagentsをリストアップ:
-

---

## 確認事項

- [ ] 現在のCLAUDE.mdを読み込み済み
- [ ] 変更理由が明確
- [ ] 影響範囲を特定済み
- [ ] 最小差分での変更を計画済み
