# Agent Base Template

このフォルダは新規エージェント作成時にそのままコピーされる「セットテンプレート」です。

含まれるもの
- `.claude/`: フック・コマンド・プリセット（リポジトリ直下の`.claude`から同期）
- `scripts/`: 共通運用スクリプト一式
- `.cursor/templates/`: ドキュメントテンプレ配置先（中身は任意で追加）

含めないもの
- `.cursor/rules/`: 実際の稼働ルールはEnhanced生成時に作成します
- 生成スクリプト (`enhanced_generate_agent.py` 等)

運用メモ
- 更新後は `MANIFEST.yaml` の `copy_targets` が正しいかを確認してください。
- テンプレを増やす場合は `template/<テンプレ名>/` を作り、同様の構成と `MANIFEST.yaml` を用意します。
