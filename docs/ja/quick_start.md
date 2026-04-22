# クイックスタート（Quick Start）

> 📅 最終更新日: 2026/04/22

このセクションでは、**TaskGraph**の迅速なインストールと実行を案内し、サンプルを通じてタスクグラフのスケジューリングメカニズムを体験します。

## 独立した仮想環境の作成

他のプロジェクトとの依存関係の競合を避けるため、独立した環境での使用を推奨します。

```bash
# プロジェクト仮想環境を作成（デフォルトで.venvを生成）
uv venv --python 3.10

# 環境を有効化（Windows）
. .\.venv\Scripts\Activate.ps1

# 環境を有効化（Linux/macOS）
source .venv/bin/activate
```

独立した仮想環境での使用を推奨します。CelestialFlowでは`uv`による依存関係と環境の管理を推奨しています。

## CelestialFlowのインストール

CelestialFlowは[PyPI](https://pypi.org/project/celestialflow/)に公開されており、ソースコードのクローン不要で`pip` / `uv pip`から直接インストールできます。

```bash
# 最新バージョンを直接インストール
uv pip install celestialflow
```

ただし、後述のテストコードを実行したい場合や、Go言語ベースのgo_workerプログラムを使用したい場合は、プロジェクトのクローンが必要です。

```bash
# プロジェクトをクローン
git clone https://github.com/Mr-xiaotian/CelestialFlow.git
cd CelestialFlow
uv pip install .
```

## （オプション）.envの設定 && Web可視化の起動

Web監視インターフェースは必須ではありませんが、Webページを通じてタスク実行に関するより多くの情報を得られるため、使用を推奨します。

まず、プロジェクトのルートディレクトリに`.env`ファイルを作成し、以下の内容を記入してください：

```env
# .env
# TaskWebのリスニングアドレス
REPORT_HOST=127.0.0.1
# TaskWebのリスニングポート
REPORT_PORT=5005
```

次に、以下のコマンドでWebサービスを起動できます：

```bash
# プロジェクトをpipでインストールした場合、現在の仮想環境でcelestialflow-webコマンドを直接使用できます
celestialflow-web --port 5005

# プロジェクトを直接cloneしてプロジェクトディレクトリにcdした場合、task_web.pyファイルを実行する必要があります
python src/celestialflow/task_web.py --port 5005 
```

デフォルトのリスニングポートは`5000`ですが、競合を避けるため、テストコードではポート`5005`を使用しています。以下にアクセスしてください：

👉 [http://localhost:5005](http://localhost:5005)

タスク構造、実行状態、エラーログの確認、およびリアルタイムでのタスク注入などの機能を利用できます。

以下の画像は、テスト実行時のWebページの表示例です（デフォルトのレイアウトではありません）：

![WebUI](https://raw.githubusercontent.com/Mr-xiaotian/CelestialFlow/main/img/web_ui.gif)
<p align="center"><em>gif画像は細部が圧縮されすぎています(｡•́︿•̀｡)</em></p>

注意：Webインターフェースを起動していない状態で、以下の設定をした場合

```python
graph.set_reporter(True, host="127.0.0.1", port=5005)
```

[ログ](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/reference/persistence/core_log.md)にいくつかの`WARNING`メッセージが表示されます。これはTaskReporterがTaskWebに接続できないことを示すものですが、使用には影響しません。

```log
2025-12-10 08:57:13 WARNING [Reporter] Task injection fetch failed: ConnectTimeout
```

## テストサンプルの実行

プロジェクトには、フレームワークの機能を素早く理解するためのサンプルファイルが`tests/`ディレクトリに用意されています。

テストが正常に動作するよう、まず必要なテストライブラリとdotenvライブラリをインストールしてください：
```bash
uv pip install pytest pytest-asyncio python-dotenv
```

まず以下のテストを実行することを推奨します：

```bash
pytest tests/test_graph.py
pytest tests/test_stage.py
```

- `tests/test_graph.py` には、グラフ構造に関連するテストが含まれています：DAG構築、段階的スケジューリング、スレッドモード、ループ/グリッド/完全グラフ構造など。
- `tests/test_stage.py` には、Stageノードに関連するテストが含まれています：モード検証、タグ生成、シリアライズチェックなど。

コード実行中は、Web監視ページで実行状況を確認できます。
