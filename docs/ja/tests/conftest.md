# tests/conftest.py

> 📅 最終更新日: 2026/10/09

## 役割
`tests/` ディレクトリ全体のルートレベル設定ファイルとして、環境変数の読み込みと共通テストヘルパー関数の提供を担当し、バックグラウンドスレッドの同期と実行中ノードの指標オブザーバーへのアクセス方法を統一的に提供します。

## コア機能

### 環境変数の読み込み
- `dotenv.load_dotenv()` を自動的に呼び出し、プロジェクトルートの `.env` ファイル内の設定がテスト起動時に利用可能になります。

### 共通テストヘルパー関数

| 関数 | 用途 | 主要パラメータ |
|------|------|----------------|
| `metrics_of(node)` | 実行中ノードの `observers` hub スナップショットから `MetricsObserver` 指標オブザーバーを取り戻し、アサーションでのノード指標読み取りに使用 | `node.observers._snapshot()` を走査し、見つからない場合は `AssertionError` を送出 |
| `wait_until(condition, *, timeout, interval, message)` | 条件が成立するまでポーリング待機し、バックグラウンドスレッドの同期記述を統一 | `timeout=5.0`, `interval=0.05` |
| `assert_stays_true(condition, *, duration, interval, message)` | 一定時間内、条件が真であり続けることを継続検証 | `duration=0.3`, `interval=0.05` |

> **説明**：ノードは自身で `metrics` フィールドを保持しなくなりました。リファクタリング後、指標オブザーバーは実行エントリで `node.observers` に登録され、`metrics_of()` が hub スナップショットからそのオブザーバーを取り戻し、テストアサーションに使用します（例: `metrics_of(executor).get_node_metrics(executor.get_name()).succeeded`）。

> `wait_until` は spout のバックグラウンドスレッドが消費を完了するのを待つためによく使用されます。`assert_stays_true` は停止後の spout が新しいレコードを処理し続けないことを検証するために使用されます。

## 注意事項
- このファイルは Pytest によって自動的に認識されます。
- このファイルは `pytest.fixture` を一切定義せず、`metrics_of` / `wait_until` / `assert_stays_true` の 3 つのテストヘルパー関数と `.env` の読み込みロジスのみを提供します。グローバルレベルの Fixture を追加する必要がある場合は、このファイルで定義すべきです。
