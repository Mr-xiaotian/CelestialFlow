# クイックスタート（Quick Start）

> 📅 最終更新日: 2026/06/18

本セクションでは、**TaskGraph** を素早くインストールして実行し、サンプルを通じてそのタスクグラフスケジューリングメカニズムを体験します。

## 独立した仮想環境の作成

他のプロジェクトとの依存関係の競合を避けるため、独立した環境での使用を推奨します。

```bash
# プロジェクト仮想環境を作成（デフォルトで .venv を生成）
uv venv --python 3.10

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

## （オプション）.env の設定 && Web 可視化の起動

Web 監視インターフェースは必須ではありませんが、Web ページを通じてタスク実行のより多くの情報を取得できるため、使用を推奨します。

まず、プロジェクトのルートディレクトリに `.env` ファイルを作成し、以下の内容を入力します：

```env
# .env
# TaskWeb のリスンアドレス
REPORT_HOST=127.0.0.1
# TaskWeb のリスンポート
REPORT_PORT=5005
```

その後、以下のコマンドで Web サービスを起動できます：

```bash
# pip でインストールした場合、現在の仮想環境で celestialflow-web コマンドを直接使用可能
celestialflow-web --port 5005

# クローンしてプロジェクトディレクトリに cd した場合、core_server.py を実行
python -m celestialflow.web.core_server --port 5005 
```

デフォルトのリスンポートは `5000` ですが、競合を避けるため、テストコードではポート `5005` を使用しています。以下にアクセスしてください：

👉 [http://localhost:5005](http://localhost:5005)

タスク構造、実行状態、エラーログ、リアルタイムタスク注入などの機能を確認できます。

以下はテスト実行時の Web ページ表示例であり、デフォルトの表示スタイルではありません：

![WebUI](https://raw.githubusercontent.com/Mr-xiaotian/CelestialFlow/main/img/web_ui.gif)
<p align="center"><em>gif 画像は多くの詳細を圧縮しています (｡•́︿•̀｡)</em></p>

注意: Web ウィンドウを起動せずに以下の設定をした場合：

```python
graph.set_reporter(True, host="127.0.0.1", port=5005)
```

[ログ](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/persistence/core_log.md)にいくつかの `WARNING` が表示されます。これは TaskReporter が TaskWeb に接続できないことを示していますが、使用には影響しません。

```log
2025-12-10 08:57:13 WARNING [Reporter] Task injection fetch failed: ConnectTimeout
```

## テストサンプルの実行

プロジェクトには `tests/` ディレクトリに複数のサンプルファイルが用意されており、フレームワークの特性を素早く理解するのに役立ちます。

テストを正常に実行するために、まずリポジトリルートで以下を実行することを推奨します：

```bash
uv sync --group dev
```

その後、以下のテストを最初に実行することを推奨します：

```bash
pytest tests/graph/test_graph.py
pytest tests/stage/test_stage.py
```

- `tests/graph/test_graph.py` にはグラフ構造関連のテストが含まれます：DAG 構築、階層スケジューリング、スレッドモード、循環/グリッド/完全グラフ構造など。
- `tests/stage/test_stage.py` には Stage ノード関連のテストが含まれます：モード検証、ラベル生成、シリアライズチェックなど。

コード実行中は Web 監視ページで実行状況を確認できます。

