# TaskWeb

> 📅 最終更新日: 2026/06/18

TaskWeb モジュールは FastAPI ベースの軽量 Web サーバーを提供し、タスクグラフの実行をリアルタイムで監視・管理します。`TaskReporter`（バックエンド）と Web UI（フロントエンド）の間の中継局として機能します。

## 起動方法

### コマンドライン起動

```bash
# デフォルトで 0.0.0.0:5000 をリッスン
celestialflow-web

# ポートを指定
celestialflow-web --port 5005

# ホストとポートを指定
celestialflow-web --host 127.0.0.1 --port 5005

# ログレベルを指定
celestialflow-web --log-level debug
```

### コマンドラインパラメータ

| パラメータ | デフォルト値 | 説明 |
|------|--------|------|
| `--host` | `0.0.0.0` | リッスンアドレス |
| `--port` | `5000` | リッスンポート |
| `--log-level` | `info` | ログレベル (critical/error/warning/info/debug/trace) |

### コード内起動

```python
from celestialflow import TaskWebServer

server = TaskWebServer(host="127.0.0.1", port=5005, log_level="info")
server.start_server()
```

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

Web UI が最新データを取得するために使用します。`known_rev` 機構をサポート：サーバー側のデータバージョンが変更されていない場合、`data: null` を返して帯域幅を節約します。

| エンドポイント | 返却構造 (data フィールド) | 説明 |
|------|--------------------|------|
| `pull_config` | `WebConfigModel` | テーマ、言語、更新頻度などのグローバル設定を取得 |
| `pull_structure`| `list[dict]` | タスクグラフのトポロジ構造を取得 |
| `pull_status` | `dict[tag, NodeStatus]` | 各ノードのリアルタイム実行指標と統一タイムスタンプを取得 |
| `pull_errors` | `list[dict]` | エラーログをページング取得 |
| `pull_analysis` | `dict` | グラフのトポロジ分析結果を取得 (DAG、階層など) |
| `pull_task_injection` | `dict[str, list[Any]]` | TaskGraph が注入待ちタスクキューを取得するために使用（ノード名でグループ化） |
| `pull_interval` | `{"interval": float}` | Reporter のプッシュ間隔を取得 |

### プッシュインターフェース (POST /api/push_*)

主に `TaskReporter` が呼び出し、バックエンドの実行状態を報告します。

| エンドポイント | データモデル | 説明 |
|------|---------|------|
| `push_config` | `WebConfigModel` | フロントエンドが呼び出し、ユーザー設定を保存 |
| `push_status` | `StatusModel` | ノード状態スナップショット + 現在のタイムスタンプを報告 |
| `push_structure`| `StructureModel` | グラフ構造を報告 |
| `push_analysis` | `AnalysisModel` | 分析データを報告 |
| `push_errors_meta` | `ErrorsMetaModel` | エラーメタデータをプッシュ（キャッシュ対応） |
| `push_errors_content`| `ErrorsContentModel`| エラー内容をプッシュ（キャッシュ対応） |
| `push_injection_tasks` | `TaskInjectionModel` | フロントエンドがタスク注入リクエストを送信 |

## データモデル (Pydantic)

> 完全なモデル定義は `util_models.md` を参照してください。ここではコアフィールドのみを記載します。

### StructureModel

```python
class StructureModel(BaseModel):
    structure: dict[str, Any]  # 構造スナップショット。通常 nodes、edges、source_nodes を含む
```

### StatusModel

```python
class StatusModel(BaseModel):
    timestamp: float                      # 統一サンプリングタイムスタンプ
    status: dict[str, dict[str, Any]]     # キーはノード名、値はノード状態辞書
```

### ErrorsMetaModel

```python
class ErrorsMetaModel(BaseModel):
    jsonl_path: str  # JSONL ファイルパス
    rev: int         # バージョン番号（キャッシュ判定用）
```

### ErrorsContentModel

```python
class ErrorsContentModel(BaseModel):
    errors: list[dict[str, Any]]
    jsonl_path: str
    rev: int
```

### AnalysisModel

```python
class AnalysisModel(BaseModel):
    analysis: dict[str, Any]
```

### TaskInjectionModel

```python
class TaskInjectionModel(RootModel[dict[str, list[Any]]]):
    """タスク注入リクエストモデル。形式は {node_name: [tasklist]}。"""
```

> 旧バージョンの単一ノード形式とは異なり、現在のモデルは辞書のキーをノード名、値をタスクリストとします。リクエストボディ例：
> `{"StageA": [task1, task2], "StageB": [task3]}`

### WebConfigModel

設定はネストグループ構造を採用し、フラットではなくなりました。

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

- `load_config()` — 起動時に読み込み、`WebConfigModel` で検証
- `save_config(config, config_path)` — 設定を JSON ファイルに保存。スレッドセーフ（上位の `push_config` ルート内の `config_lock` が保証）
- `cal_interval(refresh_interval)` — ミリ秒の更新間隔を秒に変換し、範囲を `[1.0, 60.0]` に制限
- **デグレード起動**: `config.json` の読み込みに失敗した場合、Web サービスはハードコードされたデフォルト値で起動し、監視インターフェースが常に使用可能であることを保証します。
- **同期機構**: フロントエンドが `refreshInterval` を更新すると、バックエンドの `report_interval` が自動的に同期され、`TaskReporter` のプッシュ頻度に影響します。

## TaskGraph との統合

### TaskGraph で有効化

```python
from celestialflow import TaskGraph

graph = TaskGraph()
graph.set_stages(stages=[stage_a])
graph.set_reporter(True, host="127.0.0.1", port=5005)
graph.start_graph(init_tasks)
```

### データフロー

```
TaskGraph                    TaskWeb                    Browser
    |                           |                          |
    |--- push_structure ------->|--- Dashboard ----------->|
    |--- push_status ---------->|                          |
    |--- push_analysis -------->|                          |
    |                           |                          |
    |--- push_errors_meta ----->|---- Errors ------------->|
    |--- push_errors_content -->|                          |
    |                           |                          |
    |<-- pull_task_injection ---|<--- Inject Tasks --------|
    |<-- pull_interval ---------|<--- Web Config ----------|
    |                           |                          |
```

## エラー処理

### キャッシュ機構

`push_errors_meta` と `push_errors_content` は `(jsonl_path, rev)` ベースのキャッシュをサポートします：

- パスとバージョン番号の両方が変更されていない場合、`{"ok": true, "cached": true}` を返し、ファイルを再読み込みしません
- そうでない場合はデータを再読み込みし、`_errors_meta_path` / `_errors_meta_rev` を更新します

### グレースフルデグレード

JSONL ファイルを読み取れない場合、`push_errors_meta` はフォールバック指示を返します：

```json
{
    "ok": false,
    "fallback": "need_content",
    "reason": "FileNotFoundError",
    "msg": "File not found"
}
```

クライアントはこのレスポンスを受け取った後、`push_errors_content` を使用して直接エラー内容を渡します。

### タスク注入の並行安全性

`injection_tasks` リストは `_task_injection_lock` によって保護され、`push_injection_tasks` の書き込みと `pull_task_injection` の読み取り（クリア含む）は全てロック内で操作され、競合を防止します。

## 注意事項

1. **ポート競合**: 指定ポートが使用中でないことを確認してください。
2. **ファイアウォール**: リモートアクセスが必要な場合は、ファイアウォールルールを設定してください。
3. **HTTPS**: 本番環境ではリバースプロキシ（Nginx など）を使用して HTTPS を追加することを推奨します。
4. **認証**: 現在のバージョンには組み込み認証がありません。本番環境では認証層の追加を推奨します。
