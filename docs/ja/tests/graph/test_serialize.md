# グラフシリアライズツールテスト (test_serialize.py)

> 📅 最終更新日: 2026/06/11

## 役割
グラフ構造のシリアライズおよび可視化フォーマット機能を検証し、グラフトポロジが正しく JSON 構造や読みやすいテキストリストに変換できることを確認します。

## コアテスト対象
- `build_structure_graph`: 隣接リスト形式のグラフをネスト辞書構造に変換。
- `format_structure_list_from_graph`: ネスト構造をインデント付きフォーマット文字列リストに変換。
- `make_stage`: `stage_mode` × `execution_mode` の組み合わせに基づいて `TaskStage` を構築するテストヘルパー関数。

## 主要テストシナリオ
1. **DAG シリアライズ**: 典型的な階層構造（例：s1→{s2,s3}→s4）が正しく解析され、各ノードの func_name、stage_mode、execution_mode、max_workers などの属性が正確であることを検証。
2. **循環グラフシリアライズ**: 循環グラフ（例：cs1→cs2→cs3→cs1）のシリアライズ時に無限ループに陥らないことを検証。
3. **テキストフォーマット**: 生成された文字列リストに期待されるモードマーカー（例：`(S:serial, E:serial, W:2)`）および参照マーカー（`[Ref]`）が含まれていることを検証。

## テストの重点
- **参照マーカー**: 非ツリー状 DAG や循環グラフにおいて、重複出現するノードが初回のみ詳細を表示し、それ以降は参照としてマークされることを確認。
- **再帰終了**: シリアライズアルゴリズムが循環参照を処理する際に、訪問済みノードを正しく識別して適時に再帰を終了することを確認。

## 実行方法

```bash
# 全テスト実行
pytest tests/graph/test_serialize.py -v

# 特定テスト名にマッチ
pytest tests/graph/test_serialize.py -k "dag" -v
pytest tests/graph/test_serialize.py -k "cyclic" -v
pytest tests/graph/test_serialize.py -k "format" -v
```

## パフォーマンス参考

| テスト | 所要時間 |
|--------|---------|
| `TestUtilSerialize`（DAG/循環/フォーマット） | ~0.1s 全体 |

## 重要な詳細
- `make_stage` ヘルパー関数を使用して異なる `stage_mode` × `execution_mode` 組み合わせのテストノードを構築。
- テストは JSON データ層と最終表示テキスト層の両方をカバー。

## 注意事項
- テストコードは `tests/graph/test_serialize.py` にあり、対応する実装は `src/celestialflow/graph/util_serialize.py` にあります。
