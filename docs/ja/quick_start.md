# クイックスタート（Quick Start）

> 📅 最終更新日: 2026/10/30

本セクションでは、**TaskGraph** を素早くインストールして実行し、サンプルを通じてそのタスクグラフスケジューリングメカニズムを体験します。

## 独立した仮想環境の作成

他のプロジェクトとの依存関係の競合を避けるため、独立した環境での使用を推奨します。

```bash
# プロジェクト仮想環境を作成（デフォルトで .venv を生成）
uv venv --python 3.12

# 環境をアクティベート（Windows）
. .\.venv\Scripts\Activate.ps1

# 環境をアクティベート（Linux/macOS）
source .venv/bin/activate
```

独立した仮想環境での使用を推奨します。CelestialFlow は依存関係と環境の管理に `uv` の使用を推奨します。

## CelestialFlow のインストール

CelestialFlow は [PyPI](https://pypi.org/project/celestialflow/) に公開されており、`pip` / `uv pip` で直接インストールできます。ソースコードのクローンは不要です。

```bash
# 最新版を直接インストール
uv pip install celestialflow
```

上記のインストールには CelestialFlow のデフォルトランタイム依存のみが含まれ、`celestialtree` のようなオプションのトレースコンポーネントは含まれません。

CelestialTree イベントトレースを有効にしたい場合は、追加で以下を実行してください：

```bash
uv pip install celestialtree
```

ただし、後続のテストコードを実行したい場合や、Go 言語ベースの `go_worker` プログラムを使用したい場合は、プロジェクトをクローンする必要があります：

```bash
# プロジェクトをクローン
git clone https://github.com/Mr-xiaotian/CelestialFlow.git
cd CelestialFlow
uv sync --group dev
```

ここで `dev` 依存グループには `pytest`、`python-dotenv`、`redis`、`celestialtree` などの開発・拡張に必要な依存が含まれています。

## （オプション）状態レポートの設定

現在のメインリポジトリには Web サービスは内蔵されていません。サンプルコードでレポートを有効にしている場合は、それを自前の HTTP サービスまたは独立した `celestialflow-web` プロジェクトに指定できます。CelestialFlow のコアスケジューリング能力のみを体験したい場合は、この節はスキップできます。

状態レポートの設定は、実行エントリの `report` パラメータに `ReportConfig` インスタンスを明示的に渡すことで行います：

```python
from celestialflow import ReportConfig, TaskExecutor, TaskGraph

node = TaskExecutor("処理", func=lambda x: x * 2)
graph = TaskGraph(name="demo", graph_mode="thread")
graph.set_nodes([node])

# report を渡さない（または report=None を渡す）場合はレポートを無効化
graph.run(
    {"処理": [1, 2, 3]},
    report=ReportConfig("http://127.0.0.1:5005"),
)
```

`ReportConfig` は `http` / `https` アドレスのみを受け付け、構築時に検証が完了し、末尾の `/` は取り除かれます。レポートを有効にした後、対象サービスが起動していない場合、[ログ](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/ja/src/persist/core_log.md) にいくつかの `WARNING` が表示されます。これはレポート経路がリモートサービスに接続できないことを示していますが、タスクグラフ自体の動作には影響しません。

```log
2025-12-10 08:57:13 WARNING [Reporter] Task injection fetch failed: ConnectTimeout
```

## テストサンプルの実行

プロジェクトには `tests/` ディレクトリに複数のサンプルファイルが用意されており、フレームワークの特性を素早く理解するのに役立ちます。

テストを正常に実行するために、リポジトリルートで以下を直接実行することを推奨します：

```bash
uv sync --group dev
```

その後、以下のテストを最初に実行することを推奨します：

```bash
pytest tests/graph/test_graph.py
pytest tests/node/test_node.py
```

- `tests/graph/test_graph.py` にはグラフ構造関連のテストが含まれます：DAG 構築、階層スケジューリング、スレッドモード、循環/グリッド/完全グラフ構造など。
- `tests/node/test_node.py` にはノード関連のテストが含まれます：型、メタ情報、スケジューリングとライフサイクルなど。

コード実行中は、ログ、`PrintObserver`（コンソールオブザーバー）、`MetricsObserver`（メトリクスオブザーバー）、または `ReportConfig` によるリモートレポートで実行状況を確認できます。`MetricsObserver` は実行前に `graph.add_observer(...)` で登録してインスタンスを保持しておく必要があり、実行後に `get_node_metrics()` / `get_graph_metrics()` を呼び出して統計を読み取ります。
