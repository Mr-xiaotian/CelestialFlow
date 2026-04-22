# PersistenceJSONL

`persistence/util_jsonl.py` は JSONL の永続化と読み取りユーティリティを提供します。

## 読み取りインターフェース

- `load_jsonl_logs`: オプションのフィールドフィルタリングによる行単位の読み取りで、指定した行番号からの開始をサポートします。
- `load_jsonl_grouped_by_keys`: 複数フィールドによるグループ化読み取りで、フィールド抽出と `ast.literal_eval` デシリアライゼーションをサポートします。
- `load_task_by_stage`: エラーレコードを stage 別に分類して読み込みます。
- `load_task_by_error`: エラーレコードを error と stage 別に分類して読み込みます。
