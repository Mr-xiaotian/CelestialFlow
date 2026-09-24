# tests/runtime/test_types.py

> 📅 最終更新日: 2026/09/24

## 役割
`celestialflow.runtime.util_types` の値オブジェクト、コンテキストマネージャ、オプションのロック付き値ラッパー、ライフサイクル状態列挙、イベント定数を検証し、それらが実行時に各種ノード/キューで正しく使用されることを確認します。

## コアテスト対象
- `TerminationSignal`: 終了センチネル。`id` と `source` を保持。
- `TerminationIdPool`: 終了信号 ID プール。
- `NoOpContext`: 空のコンテキストマネージャ。ロックの無効化に使用可能。
- `ValueWrapper`: スレッドセーフなカウンタラッパー。独自にロックを生成する、外部ロックを再利用する、あるいは `NoOpContext` を渡してロックを無効化できる。
- `StageStatus`: ライフサイクル状態の `IntEnum`。
- `CTreeEvent`: イベント名定数の集合。

## テストカバレッジマトリクス

| テストクラス | ケース数 | カバレッジ目標 |
|--------|--------|---------|
| `TestUtilTypes` | 23 | `TerminationSignal` のデフォルト/カスタム/部分パラメータ；`TerminationIdPool` の非空/空/単一要素；`NoOpContext` の with 文/例外透過/直接呼び出し enter、exit；`ValueWrapper` の読み書き/ロック付き/コンテキストマネージャ/`get_lock` がロックまたは `NoOpContext` を返す/ロックの独立/負の数値；`StageStatus` の列挙値/IntEnum 動作/メンバー数；`CTreeEvent` のタスク定数/終了定数/プレフィックス形式 |

## カバレッジポイント
- `TerminationSignal` / `TerminationIdPool` の構築セマンティクス。
- `NoOpContext` のコンテキスト管理動作と例外の透過伝播。
- `ValueWrapper` のロックあり、ロック再利用、ロック無効化の 3 モードにおける読み書きセマンティクス。
- `StageStatus`、`CTreeEvent` の列挙値。

## 主要シナリオ
- `TerminationSignal` はデフォルトで `id == -1`、`source == "input"`；`_id`/`source` の部分キーワード構築をサポート。
- `ValueWrapper.get_lock()` は `Lock` を渡した場合はそのロックを返し、渡さない場合は自前で生成した実ロックを返し、明示的に `NoOpContext` を渡した場合はそのインスタンスを返す（読み書きはロックされない）。
- 各 `ValueWrapper` が自前で生成したロックは互いに独立し、インスタンス間で共有されない。
- `StageStatus` は `IntEnum` で、整数と比較でき、メンバー数は 3。
- `CTreeEvent.TASK_RETRY_PREFIX` はピリオドで終わる。

## 実行方法

```bash
pytest tests/runtime/test_types.py -v
pytest tests/runtime/test_types.py -k "value_wrapper or noop" -v
pytest tests/runtime/test_types.py -k "termination" -v
```

## 注意事項
- テストコードは `tests/runtime/test_types.py` にあり、対応する実装は `src/celestialflow/runtime/util_types.py` にあります。
