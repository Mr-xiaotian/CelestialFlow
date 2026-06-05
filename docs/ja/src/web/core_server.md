# TaskWeb

> 📅 最終更新日: 2026/05/23

TaskWeb モジュールは、FastAPI ベースの軽量 Web サーバーを提供し、タスクグラフの実行をリアルタイムで監視・管理します。`TaskReporter`（バックエンド）と Web UI（フロントエンド）の間の中継局として機能します。

## 起動方法

### コマンドラインでの起動

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

### コマンドライン引数

| 引数 | デフォルト値 | 説明 |
|------|--------|------|
| `--host` | `0.0.0.0` | リッスンアドレス |
| `--port` | `5000` | リッスンポート |
| `--log-level` | `info` | ログレベル (critical/error/warning/info/debug/trace) |

### コードからの起動

```python
from celestialflow import TaskWebServer

server = TaskWebServer(host="127.0.0.1", port=5005, log_level="info")
server.start_server()
```

## 機能画面

`http://localhost:5000`（または指定ポート）にアクセスすると Web UI が表示されます。

### 主要パネル

| パネル | 機能 |
|------|------|
| **Dashboard** | タスクグラフのリアルタイムステータス概要（構造可視化（Mermaid 図）、ノード数、成功/失敗/滞留タスク数、折れ線グラフ） |
| **Errors** | リアルタイムエラーログリスト |
| **Task Injection** | Web 画面から動的にタスクを注入 |

### テーマサポート

- ライト/ダークテーマの切り替えをサポート
- テーマ設定はバックエンドの `config.json` に永続化保存

## API インターフェース (RESTful)

TaskWeb は一連の RESTful API を提供し、`TaskReporter` からの呼び出しとフロントエンドでの使用に対応します。すべてのインターフェースは `/api/` をプレフィックスとし、取得インターフェースは `pull_` 命名、送信インターフェースは `push_` 命名を使用します。

### 取得インターフェース (GET /api/pull_*)

Web UI が最新データを取得するために使用します。`known_rev` メカニズムをサポートします：サーバー側のデータバージョンが変更されていない場合、帯域幅節約のために `data: null` を返します。

| エンドポイント | 戻り値構造 (data フィールド) | 説明 |
|------|--------------------|------|
| `pull_config` | `WebConfigModel` | テーマ、言語、リフレッシュ頻度などのグローバル設定を取得 |
| `pull_structure`| `list[dict]` | タスクグラフのトポロジ構造を取得 |
| `pull_status` | `dict[tag, NodeStatus]` | 各ノードのリアルタイム実行指標と統一タイムスタンプを取得 |
| `pull_errors` | `list[dict]` | エラーログをページネーション取得 |
| `pull_analysis` | `dict` | グラフのトポロジ分析結果を取得 (DAG, 階層など) |
| `pull_summary` | `{"total_remain": float}` | グラフレベルの合計残り時間推定を取得 |
| `pull_task_injection` | `list[dict]` | TaskGraph が注入待ちタスクキューを取得するために使用 |
| `pull_interval` | `{"interval": float}` | Reporter のプッシュ間隔を取得 |

### 送信インターフェース (POST /api/push_*)

主に `TaskReporter` から呼び出され、バックエンドの実行状態を報告します。

| エンドポイント | データモデル | 説明 |
|------|---------|------|
| `push_config` | `WebConfigModel` | フロントエンドから呼び出され、ユーザー設定を保存 |
| `push_status` | `StatusModel` | ノード状態スナップショット + 現在のタイムスタンプを報告 |
| `push_structure`| `StructureModel` | グラフ構造を報告 |
| `push_analysis` | `AnalysisModel` | 分析データを報告 |
| `push_summary` | `SummaryModel` | グラフレベルのサマリー情報を報告 |
| `push_errors_meta` | `ErrorsMetaModel` | エラーメタデータをプッシュ（キャッシュ対応） |
| `push_errors_content`| `ErrorsContentModel`| エラー内容をプッシュ（キャッシュ対応） |
| `push_injection_tasks` | `TaskInjectionModel` | フロントエンドがタスク注入リクエストを送信 |

## データモデル (Pydantic)

### StructureModel
```python
class StructureModel(BaseModel):
    items: list[dict[str, Any]]
```

### StatusModel
```python
class StatusModel(BaseModel):
    timestamp: float                 # 統一サンプリングタイムスタンプ
    status: dict[str, dict[str, Any]] # キーはノード Tag、値は NodeStatus
```

### ErrorsMetaModel
```python
class ErrorsMetaModel(BaseModel):
    jsonl_path: str  # JSONL ファイルパス
    rev: int         # バージョン番号（キャッシュ判定に使用）
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

### SummaryModel
```python
class SummaryModel(BaseModel):
    summary: dict[str, Any]
```

### TaskInjectionModel
```python
class TaskInjectionModel(BaseModel):
    node: str             # ターゲットノードラベル
    task_datas: list[Any] # タスクデータリスト
    timestamp: datetime   # タイムスタンプ
```

### WebConfigModel
```python
class WebConfigModel(BaseModel):
    theme: str                        # "light" | "dark"
    refreshInterval: int              # ポーリング間隔 (ms)
    historyLimit: int                 # フロントエンド履歴保持長
    language: str = "zh-CN"           # 画面言語
    errorPageSize: int = 10           # エラーログページネーションサイズ
    showStructureEdgeDelta: bool = True # 構造図増分表示スイッチ
    dashboard: DashboardConfigModel   # ダッシュボード3カラムレイアウト定義

class DashboardConfigModel(BaseModel):
    left: list[str]    # 左カラムカード key リスト
    middle: list[str]  # 中央カラムカード key リスト
    right: list[str]   # 右カラムカード key リスト
```

## 設定管理

Web サービスの設定は `web/config.json` に永続化保存されます。

- `load_config()` — 起動時に読み込み、`WebConfigModel` で検証
- `save_config(config)` — 設定を JSON ファイルに保存、スレッドセーフ（`_config_lock` を使用）
- `cal_interval(refresh_interval)` — ミリ秒のリフレッシュ間隔を秒に変換、範囲を `[1.0, 60.0]` に制限
- **デグレード起動**: `config.json` の読み込みに失敗した場合、Web サービスはハードコードされたデフォルト値で起動し、監視画面が常に利用可能であることを保証します。
- **同期メカニズム**: フロントエンドが `refreshInterval` を更新すると、バックエンドの `report_interval` が自動的に同期され、`TaskReporter` のプッシュ頻度に影響します。

## TaskGraph との統合

### TaskGraph での有効化

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
    |--- push_summary --------->|                          |
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

`push_errors_meta` と `push_errors_content` は `(jsonl_path, rev)` に基づくキャッシュをサポートします：

- パスとバージョン番号がいずれも変化していない場合、`{"ok": true, "cached": true}` を返し、ファイルを再読み込みしない
- そうでなければデータを再読み込みし、`_errors_meta_path` / `_errors_meta_rev` を更新

### グレースフルデグラデーション

JSONL ファイルを読み取れない場合、`push_errors_meta` はフォールバック指示を返します：

```json
{
    "ok": false,
    "fallback": "need_content",
    "reason": "FileNotFoundError",
    "msg": "File not found"
}
```

クライアントはこのレスポンスを受信後、`push_errors_content` を使用してエラー内容を直接送信します。

### タスク注入の並行安全性

`injection_tasks` リストは `_task_injection_lock` で保護されており、`push_injection_tasks` の書き込みと `pull_task_injection` の読み取り（クリアを含む）はいずれもロック内で操作され、競合状態を回避します。

## 注意事項

1. **ポート競合**: 指定ポートが使用されていないことを確認してください。
2. **ファイアウォール**: リモートアクセスが必要な場合は、ファイアウォールルールを設定してください。
3. **HTTPS**: 本番環境ではリバースプロキシ（Nginx など）を使用して HTTPS を追加することを推奨します。
4. **認証**: 現在のバージョンには組み込みの認証がないため、本番環境では認証レイヤーの追加を推奨します。
