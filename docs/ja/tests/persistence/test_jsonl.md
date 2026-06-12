# JSONL ユーティリティテスト (test_jsonl.py)

> 📅 最終更新日: 2026/05/23

## 役割
`celestialflow.persistence.util_jsonl` のユーティリティ関数を検証し、JSONL 形式の永続化ログを正確に解析・フィルタリング・グループ化できることを確認します。

## コアテスト対象
- `parse_jsonl_value`: 文字列値を Python ネイティブ型（数値、ブール、タプルなど）にインテリジェントに解析。
- `load_jsonl_logs`: ログ行を一括読み込みしフィルタリング。
- `load_jsonl_by_key`: 単一キー（stage など）でグループ化してフィールドを抽出。
- `load_jsonl_grouped_by_keys`: 複数キーの組み合わせでグループ化。
- `load_task_error_pairs`: タスクとエラーレコードのペア抽出専用。

## 主要テストフロー
1. **インテリジェント解析**: 文字列 "1" が整数に、"True" がブール値に、"[1, 2]" がタプルに変換されることを検証。
2. **エラー文字列分割**: `ValueError(msg)` 形式からエラータイプとメッセージ内容を抽出することを検証。
3. **構造化読み取り**: Meta 行、通常データ行、複雑なタスク行（タプル ID など）を含む JSONL ファイルをシミュレートし、読み取りの完全性を検証。
4. **マルチレベルグループ化**: `(error, stage)` の組み合わせキーによるグループ化ロジックを検証。

## テストの重点
- **ロバスト性**: Meta 行や形式が不整合な行が読み取り時に正しくスキップされることを確認。
- **型復元**: JSONL から復元されたタスクデータが元の型（`(1, 2)` タプルなど）を保持することを検証。
- **フィールドフィルタリング**: `keys` パラメータがメモリ使用量を効果的に削減し、必要なフィールドのみを抽出することを検証。

## 実行方法

```bash
# すべて実行
pytest tests/persistence/test_jsonl.py -v

# インテリジェント解析テストのみ実行
pytest tests/persistence/test_jsonl.py -k "parse" -v

# グループ化読み取りテストのみ実行
pytest tests/persistence/test_jsonl.py -k "group" -v

# エラーペアテストのみ実行
pytest tests/persistence/test_jsonl.py -k "error_pair" -v
```

## パフォーマンス参考

| テスト | 所要時間 |
|------|------|
| `TestJsonlUtils` | ~0.1s（純粋なロジック、I/O 待機なし） |

## 重要な詳細
- `pytest.fixture` を使用して一時的な `sample_jsonl` ファイルを作成しテストします。
- `test_load_task_error_pairs` は `PersistedErrorRecord` データモデルのカプセル化を検証します。

## 注意事項
- テストコードは `tests/persistence/test_jsonl.py` にあります。
