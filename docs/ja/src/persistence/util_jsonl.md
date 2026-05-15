# PersistenceJSONL

> 📅 最終更新日: 2026/05/15

`persistence/util_jsonl.py` は JSONL の永続化と読み取りユーティリティを提供します。

## 読み取りインターフェース

- `load_jsonl_logs`: オプションのフィールドフィルタリング付きで行ごとに読み取り。指定行番号からの開始をサポート。
- `load_jsonl_grouped_by_keys`: 複数フィールドによるグループ読み取り。フィールド抽出と `ast.literal_eval` デシリアライズをサポート。
- `load_task_by_stage`: エラーレコードをステージ別に分類して読み込み。
- `load_task_by_error`: エラーレコードをエラーとステージ別に分類して読み込み。
- `load_jsonl_by_key`: 指定フィールドでグループ化して JSONL ファイルから値を読み込み。カスタムグループキーと値抽出フィールドをサポート。
- `load_task_error_pairs`: エラーレコードを読み込み、`(task, error)` ペアのリストを返す。
