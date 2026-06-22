# TaskWebServer（core_server）

> 📅 最終更新日: 2026/06/22

TaskWeb モジュールは FastAPI ベースの軽量 Web サーバーを提供し、タスクグラフの実行をリアルタイムで監視・管理します。`TaskReporter`（バックエンド）と Web UI（フロントエンド）の間の中継局として機能します。

## 起動方法

### コマンドライン起動

```bash
# 默认监听 0.0.0.0:5000
celestialflow-web

# 指定端口
celestialflow-web --port 5005

# 指定主机和端口
celestialflow-web --host 127.0.0.1 --port 5005

# 指定日志级别
celestialflow-web --log-level debug
```

### コマンドラインパラメータ

| パラメータ | デフォルト値 | 説明 |
|------|--------|------|
| `--host` | `0.0.0.0` | 监听地址 |
| `--port` | `5000` | 监听端口 |
| `--log-level` | `info` | 日志级别 (critical/error/warning/info/debug/trace) |

### コード内起動

```python
from celestialflow import TaskWebServer

server = TaskWebServer(host="127.0.0.1", port=5005, log_level="info")
server.start_server()
```

### CLI 入口

`core_server.py` はコマンドライン入口関数も提供します：

- `parse_args()` — `--host`、`--port`、`--log-level` 引数を解析します。`--log-level` は `critical` / `error` / `warning` / `info` / `debug` / `trace` に制限されます。
- `main_entry()` — 解析後の引数から `TaskWebServer` を構築し、`start_server()` を呼び出します。

コマンドラインツール `celestialflow-web` は `main_entry` から登録されています。

## 機能インターフェース

`http://localhost:5000`（または指定ポート）にアクセスすると Web UI が表示されます。

### メインパネル

| パネル | 機能 |
|------|------|
| **Dashboard** | タスクグラフのリアルタイム状態概要（構造可視化（Mermaid 図）、ノード数、成功/失敗/滞留タスク数、折れ線グラフ） |
| **Errors** | リアルタイムエラーログリスト |
| **Task Injection** | Web インターフェース経由でタスクを動的に注入 |

### テーマサポート

- 日中/夜間テーマ切り替えをサポート
- テーマ設定はバックエンドの `config.json` に永続化保存

## API インターフェース (RESTful)

TaskWeb は `TaskReporter` の呼び出しとフロントエンド用の一連の RESTful API を提供します。全てのインターフェースは `/api/` プレフィックスを持ち、プルインターフェースは `pull_`、プッシュインターフェースは `push_` の命名規則を使用します。

### プルインターフェース (GET /api/pull_*)

Web UI が最新データを取得するために使用します。大部分のプルインターフェース（`pull_status`、`pull_structure`、`pull_errors`、`pull_analysis`）は `known_rev` 機構をサポート：サーバー側のデータバージョンが変更されていない場合、`data: null` を返して帯域幅を節約します。`pull_config`、`pull_task_injection`、`pull_server_state` は `known_rev` 機構を使用せず、毎回完全なデータを返します。

| エンドポイント | 返却構造 (data フィールド) | 説明 |
|------|--------------------|------|
| `pull_config` | `dict` | テーマ、言語、更新頻度などのグローバル設定を取得 |
| `pull_structure`| `dict[str, Any]` | タスクグラフのトポロジ構造を取得（nodes/edges/source_nodes を含む） |
| `pull_status` | `dict[str, dict[str, Any]]` | 各ノードのリアルタイム実行指標と統一タイムスタンプを取得 |
| `pull_errors` | `list[dict]` | エラーログをページング取得。ノード/キーワードフィルタとソートをサポート |
| `pull_analysis` | `dict[str, Any]` | グラフのトポロジ分析結果を取得 |
| `pull_task_injection` | `dict[str, list[Any]]` | TaskGraph が注入待ちタスクキューを取得するために使用（ノード名でグループ化、読み取り後にクリア） |
| `pull_server_state` | `dict[str, Any]` | Reporter 同期に必要なサーバー状態を取得（interval/is_current_graph/has_structure/has_analysis/max_event_id_in_fail） |

### プッシュインターフェース (POST /api/push_*)

主に `TaskReporter` が呼び出し、バックエンドの実行状態を報告します。

| エンドポイント | データモデル | 説明 |
|------|---------|------|
| `push_config` | `WebConfigModel` | フロントエンドが呼び出し、ユーザー設定を保存 |
| `push_status` | `StatusModel` | ノード状態スナップショット + 現在のタイムスタンプを報告 |
| `push_structure`| `StructureModel` | グラフ構造を報告 |
| `push_analysis` | `AnalysisModel` | 分析データを報告 |
| `push_errors` | `ErrorsModel` | エラー内容を直接受信し SQLite に書き込み |
| `push_injection_tasks` | `TaskInjectionModel` | フロントエンドがタスク注入リクエストを送信 |

## データモデル (Pydantic)

> 完全なモデル定義は `util_models.md` を参照してください。ここではコアフィールドのみを記載します。

### StructureModel

```python
class StructureModel(BaseModel):
    graph_id: str = ""  # 图实例标识，用于 Reporter 端 graph 上下文校验
    structure: dict[str, Any]  # 结构快照，包含 nodes、edges、source_nodes
```

### StatusModel

```python
class StatusModel(BaseModel):
    graph_id: str = ""                    # 图实例标识
    timestamp: float                      # 统一采样时间戳
    status: dict[str, dict[str, Any]]     # 键为节点名，值为节点状态字典
```

### ErrorsModel

```python
class ErrorsModel(BaseModel):
    graph_id: str = ""              # 图实例标识
    errors: list[dict[str, Any]]    # 错误记录列表，直接写入 SQLite 数据库
```

### AnalysisModel

```python
class AnalysisModel(BaseModel):
    graph_id: str = ""        # 图实例标识
    analysis: dict[str, Any]  # 分析结果字典
```

### TaskInjectionModel

```python
class TaskInjectionModel(RootModel[dict[str, list[Any]]]):
    """任务注入请求模型，格式为 {node_name: [tasklist]}。"""
```

> 请求体直接为节点名到任务列表的映射。例：
> `{"StageA": [task1, task2], "StageB": [task3]}`

### WebConfigModel

設定はネストグループ構造を採用します。

```python
class GlobalConfigModel(BaseModel):
    theme: str
    autoRefreshEnabled: bool = True
    refreshInterval: int
    language: str = "zh-CN"

class DashboardConfigModel(BaseModel):
    left: list[str]
    middle: list[str]
    right: list[str]

class DashboardPageConfigModel(BaseModel):
    historyLimit: int
    showStructureEdgeDelta: bool = False
    useTotalPendingInStatus: bool = False
    layout: DashboardConfigModel

class ErrorsPageConfigModel(BaseModel):
    pageSize: int = 10
    sortOrder: str = "newest"
    jumpToInjectionAfterRetry: bool = True

class InjectionPageConfigModel(BaseModel):
    showInjectableOnly: bool = True

class WebConfigModel(BaseModel):
    global_: GlobalConfigModel = Field(alias="global")
    dashboard: DashboardPageConfigModel
    errors: ErrorsPageConfigModel
    injection: InjectionPageConfigModel = Field(default_factory=InjectionPageConfigModel)
```

## 設定管理

Web サービスの設定は `web/config.json` に永続化保存されます。

- `load_config()` — 起動時に読み込み、`WebConfigModel` で検証します。`config.json` が存在しない場合、ハードコードされたデフォルト値を使用せずに `ConfigurationError` を送出します。
- `save_config(config, config_path)` — 設定を JSON ファイルに保存。スレッドセーフ（上位の `push_config` ルート内の `config_lock` が保証）
- `cal_interval(refresh_interval)` — ミリ秒の更新間隔を秒に変換し、範囲を `[1.0, 60.0]` に制限
- **同期機構**: フロントエンドが `refreshInterval` を更新すると、バックエンドの `report_interval` が自動的に同期され、`TaskReporter` のプッシュ頻度に影響します。

## TaskGraph との統合

### TaskGraph で有効化

```python
from celestialflow import TaskGraph, TaskStage


def process(x: int) -> int:
    return x * 2


stage_a = TaskStage("StageA", process, execution_mode="thread")
graph = TaskGraph(name="DemoGraph")
graph.set_stages(stages=[stage_a])
graph.set_reporter(True, host="127.0.0.1", port=5005)
init_tasks = {stage_a.get_name(): [1, 2, 3]}
graph.start_graph(init_tasks)
```

### データフロー

```
TaskGraph                         TaskWeb                    Browser
    |                                |                          |
    |--- push_structure ------------>|--- Dashboard ----------->|
    |--- push_status --------------->|                          |
    |--- push_analysis ------------->|                          |
    |                                |                          |
    |--- push_errors --------------->|---- Errors ------------->|
    |                                |                          |
    |<-- pull_task_injection --------|<--- Inject Tasks --------|
    |<-- pull_server_state ----------|<--- Reporter Sync -------|
    |                                |                          |
```

## エラー処理

### SQLite 永続化

エラー記録は `append_records` を通じて SQLite データベースに直接書き込まれ、効率的なクエリとページングをサポートします。

### タスク注入の並行安全性

`injection_tasks` 辞書は `task_injection_lock` によって保護され、`push_injection_tasks` の書き込みと `pull_task_injection` の読み取り（クリア含む）は全てロック内で操作され、競合を防止します。注入は**上書き**セマンティクスを採用：同じノード名の新しいタスクは古いタスクリストを上書きします。

## 注意事項

1. **ポート競合**: 指定ポートが使用中でないことを確認してください。
2. **ファイアウォール**: リモートアクセスが必要な場合は、ファイアウォールルールを設定してください。
3. **HTTPS**: 本番環境ではリバースプロキシ（Nginx など）を使用して HTTPS を追加することを推奨します。
4. **認証**: 現在のバージョンには組み込み認証がありません。本番環境では認証層の追加を推奨します。
