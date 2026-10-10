# tests/node/test_node.py

> 📅 最終更新日: 2026/10/09

## 役割

`celestialflow.node.core_node.BaseTaskNode`（公開サブクラス `TaskExecutor` を介して間接的にカバー）が提供する汎用設定、紐付け、起動時例外集約の振る舞いを検証します。ノード一意識別、実行モード検証、リトライ可能例外の設定、`get_meta()` による構築期フィールドの区分、および `connect_to` が確立するキュー紐付けが実行モード切替後も安定していることを含みます。

## コアテスト対象

| クラス / 関数 | 役割 | 説明 |
|-----------|------|------|
| `add_one(x)` | テストコールバック | 同期加算関数 |
| `async_add_one(x)` | テストコールバック | 非同期加算コルーチン関数 |
| `TestBaseTaskNodeConfig` | ケースクラス | 名称、実行モード、リトライ可能例外、メタ情報、モード切替時の下流紐付け保持をカバー |
| `TestBaseTaskNodeStartErrors` | ケースクラス | `start` / `start_async` の例外集約挙動をカバー |

## 主要テストシナリオ

### `TestBaseTaskNodeConfig` — 設定と紐付け

| ケース | カバレッジ目標 |
|------|---------|
| `test_node_name_identity` | ノード名がコンストラクタ引数 `name` から直接取得される |
| `test_node_name_changes_with_name` | `set_name(...)` で名称変更後、`get_name()` も同期更新される |
| `test_valid_execution_mode_serial` | `execution_mode="serial"` に対応 |
| `test_valid_execution_mode_thread` | `execution_mode="thread"` に対応 |
| `test_valid_execution_mode_async` | `execution_mode="async"` に対応（`async_add_one` を使用） |
| `test_invalid_execution_mode` | 不正なモードで `InvalidOptionError` が送出される |
| `test_default_retry_exceptions_empty` | デフォルトのリトライ可能例外は空（`retry_exceptions == ()`、`get_retry_error_type_names() == set()`） |
| `test_set_retry_exceptions_is_additive` | `set_retry_exceptions(...)` が例外型を蓄積し、型名の集合としてマッピングする |
| `test_get_meta_reports_build_time_fields` | `get_meta()` は `class_name` / `execution_mode` / `max_workers` のみを返す |
| `test_connect_to_binding_survives_execution_mode_switch` | `connect_to` が確立した下流 / 上流のキュー紐付けが `set_execution_mode("thread")` 後も安定を保つ |

### `TestBaseTaskNodeStartErrors` — 起動例外の集約

| ケース | カバレッジ目標 |
|------|---------|
| `test_start_raises_exception_group_after_finish` | `monkeypatch` で `_prepare_start` が `ValueError("prepare failed")` を投げ、`_finish_start` が `[RuntimeError("finish failed")]` を返すように細工する。同期 `start()` が最終的に `ExceptionGroup` を投げ、内部の 2 つの例外が "prepare → finish" の順で格納される |
| `test_start_async_raises_exception_group_after_finish` | 非同期バージョンも同様に prepare 例外と finish 例外を集約して `ExceptionGroup` を投げる |

## 主要データフロー

```mermaid
flowchart TB
    Start[start / start_async]
    Prep[_prepare_start]
    Mode{execution_mode}
    Serial[dispatch_serial]
    Thread[dispatch_thread]
    Async[dispatch_async]
    Finish[_finish_start]
    Agg[ExceptionGroup 集約して送出]

    Start --> Prep
    Prep --> Mode
    Mode -- serial --> Serial
    Mode -- thread --> Thread
    Mode -- async --> Async
    Serial --> Finish
    Thread --> Finish
    Async --> Finish
    Finish --> Agg
```

## テストカバレッジマトリクス

| テストクラス | ケース数 | カバレッジ目標 |
|--------|--------|---------|
| `TestBaseTaskNodeConfig` | 10 | 名称の識別と変更、3 種の合法的な実行モード、不正モードでのエラー、リトライ可能例外のデフォルトと蓄積、メタ情報のフィールド区分、モード切替で下流紐付けが破壊されないこと |
| `TestBaseTaskNodeStartErrors` | 2 | 同期 / 非同期 `start*` の例外集約 |
| **合計** | **12** | |

## 実行方法

```bash
# すべて実行
pytest tests/node/test_node.py -v

# 設定関連ケースのみ
pytest tests/node/test_node.py -k "Config" -v

# 起動例外集約ケースのみ
pytest tests/node/test_node.py -k "StartErrors" -v

# 実行モード関連ケースのみ
pytest tests/node/test_node.py -k "execution_mode" -v
```

## パフォーマンス参考

| テストクラス | 所要時間 |
|--------|------|
| `TestBaseTaskNodeConfig` | < 0.5s |
| `TestBaseTaskNodeStartErrors` | < 0.5s |

## 注意事項

- `test_connect_to_binding_survives_execution_mode_switch` は回帰テストです。`connect_to` が確立した下流のキュープール `yield_queue` と上流の入力元 `source_names` が実行モード切替後も安定し、ディスパッチャ再構築によって紐付けが失われません。
- `get_meta()` は構築期メタ情報（`class_name` / `execution_mode` / `max_workers`）のみを返し、グラフ構造の一回限りの報告に用います。
- `TestBaseTaskNodeStartErrors` は `monkeypatch.setattr` で `_prepare_start` と `_finish_start` という **内部フック** を置き換え、同期 / 非同期の起動時例外がどちらも `ExceptionGroup` に集約されて送出されることを検証します。
- `ExceptionGroup` は Python 3.11+ でのみ利用可能です。本リポジトリは Python 3.14 をベースにしているため要件を満たします。
- 関連実装は `src/celestialflow/node/core_node.py` にあります。