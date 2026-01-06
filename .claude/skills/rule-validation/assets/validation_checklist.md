# Skills バリデーション チェックリスト

## 検証前の確認
- [ ] 検証対象フォルダ（.claude/skills/）が存在する
- [ ] CLAUDE.md が存在する
- [ ] validate_skills.py が存在する

## 検証実行
```bash
cd output/{domain}_agent
python3 scripts/validate_skills.py
```

## 検証項目
validate_skills.py は以下をチェックする:
- [ ] SKILL.mdの存在
- [ ] フロントマター（name, description）の存在
- [ ] 必須セクション（Instructions, Resources, Next Action）
- [ ] assets/フォルダの存在
- [ ] Skill名規則（{domain}-{action}-{object}）

## エラー対応
エラーが出た場合:
1. エラー内容を確認
2. 該当ファイルを修正
3. 再度validate_skills.pyを実行
4. `All skills passed validation.` が出るまで繰り返す

## 検証ログ記録
- [ ] skills_check_log.md に結果を記録
- [ ] 検証日時を明記
- [ ] 対象Skill一覧を記載
- [ ] エラー内容と修正内容を記載

## 完了条件
- [ ] `All skills passed validation.` が出力された
- [ ] タスクリストに validation_passed=true を記録
- [ ] 検証ログをFlow配下に保存
