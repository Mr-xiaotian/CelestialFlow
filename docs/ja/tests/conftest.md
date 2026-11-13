# tests/conftest.py

> 📅 最終更新日: 2026/11/13

## 役割

`tests/` ディレクトリ全体のルートレベル設定ファイルとして、環境変数の読み込みと共通テストヘルパー関数の提供を担当し、テストにおけるバックグラウンドスレッドの同期、実行中ノードの指標オブザーバー、ライフサイクルデータベースへのアクセス方法を統一的に提供します。

## コア機能

### 環境変数の読み込み

- `dotenv.load_dotenv()` を自動的に呼び出し、プロジェクトルートの `.env` ファイル内の設定がテスト起動時に利用可能になることを保証します。

### 共通テストヘルパー関数

| 関数 | 用途 | 主要パラメータ / 挙動 |
|------|------|----------------|
| `metrics_of(node)` | ノードの hub 上の `MetricsObserver` を取り戻し、アサーションで指標を読み取る | `node.observers.find(MetricsObserver)` を呼び出す。未登録の場合は `AssertionError` を送出 |
| `lifecycle_db_of(target)` | 対象オブジェクトの hub 上のライフサイクルデータベースパスを取り戻す | タスクグラフには `target.get_observers()` を、ノードには `target.observers` を読み取り、`find(LifecycleObserver)` でその `db_path` を返す。未登録または未起動（`db_path is None`）の場合は `AssertionError` を送出 |
| `wait_until(condition, *, timeout, interval, message)` | 条件が成立するまでポーリング待機し、バックグラウンドスレッドの同期記述を統一 | `timeout=5.0`、`interval=0.05`。タイムアウト後にもう一度確認し、それでも成立しなければ `pytest.fail(message)` |
| `assert_stays_true(condition, *, duration, interval, message)` | 一定時間内、条件が真のままであることを継続検証 | `duration=0.3`、`interval=0.05`。いずれかのサンプル点で不成立なら `pytest.fail(message)` |

> **説明**：ノード自身は `metrics` / `lifecycle` フィールドを保持しなくなりました。関連するオブザーバーは実行エントリによって `node.observers` に登録されます。`ObserverHub.find()` はまず自層を調べ、次にネストした hub へ再帰的に入るため、グラフ実行時に注入されたグラフレベルのオブザーバーも `metrics_of(graph)` / `lifecycle_db_of(graph)` で見つけられます。

> `wait_until` は spout のバックグラウンドスレッドが消費を完了するまで、または lifecycle / log がディスクに書き込まれるまで待つためによく使用されます。`assert_stays_true` は停止後の spout が新しいレコードを処理し続けないことを検証するために使用されます。

## 注意事項

- このファイルは Pytest によってルートレベルの `conftest.py` として自動的に認識されます。
- このファイルは `pytest.fixture` を一切定義せず、`metrics_of` / `lifecycle_db_of` / `wait_until` / `assert_stays_true` の 4 つのテストヘルパー関数と `.env` の読み込みロジックのみを提供します。グローバルレベルの Fixture を追加する必要がある場合は、このファイルで定義すべきです。
- `lifecycle_db_of` は `LifecycleObserver` が `start()` で初期化を完了していることを要求します。そうでない場合 `db_path` が `None` となり、アサーション失敗を引き起こします。
