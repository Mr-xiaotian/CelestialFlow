# TaskWeb

TaskWeb モジュールは、タスクグラフの実行をリアルタイムで監視・管理するための、FastAPI ベースの軽量 Web サーバーを提供します。

## 起動方法

### コマンドライン起動

```bash
# デフォルト: 0.0.0.0:5000 でリッスン
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
|------|-------------|------|
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
|--------|------|
| **Dashboard** | タスクグラフのリアルタイムステータス概要（構造の可視化（Mermaid 図）、ノード数、成功/失敗/バックログタスク数、折れ線グラフ） |
| **Errors** | リアルタイムエラーログリスト |
| **Task Injection** | Web インターフェースからの動的タスクインジェクション |

### テーマサポート

- ライト/ダークテーマの切り替えをサポート
- テーマ設定はバックエンドの `config.json` に永続化されます

## API エンドポイント

TaskWeb は `TaskReporter` およびフロントエンドが使用する一連の RESTful API を提供します。すべてのエンドポイントは `/api/` プレフィックス付きで、プルエンドポイントは `pull_` 命名規則、プッシュエンドポイントは `push_` 命名規則を使用します。

### データ取得 (GET)

| エンドポイント | 説明 |
|---------------|------|
| `GET /api/pull_config` | フロントエンド設定を取得（テーマ、リフレッシュ間隔、ダッシュボードレイアウトなど） |
| `GET /api/pull_structure` | グラフ構造を取得 |
| `GET /api/pull_status` | ステージの実行状態を取得 |
| `GET /api/pull_errors` | エラーログを取得 |
| `GET /api/pull_analysis` | 分析データを取得 |
| `GET /api/pull_summary` | サマリー統計を取得 |
| `GET /api/pull_history` | 各ステージのタスク処理履歴を取得（折れ線グラフ用） |
| `GET /api/pull_interval` | Reporter のプッシュ間隔を取得 |
| `GET /api/pull_history_limit` | 履歴レコードの最大保持件数を取得 |
| `GET /api/pull_task_injection` | 保留中のインジェクションタスクを取得（TaskGraph がプルする用） |

### データ送信 (POST)

| エンドポイント | 説明 |
|---------------|------|
| `POST /api/push_config` | フロントエンド設定を保存 |
| `POST /api/push_structure` | グラフ構造をプッシュ |
| `POST /api/push_status` | ステージ状態をプッシュ |
| `POST /api/push_errors_meta` | エラーメタデータをプッシュ（キャッシュ対応） |
| `POST /api/push_errors_content` | エラーコンテンツをプッシュ（キャッシュ対応） |
| `POST /api/push_analysis` | 分析データをプッシュ |
| `POST /api/push_summary` | サマリー統計をプッシュ |
| `POST /api/push_history` | 各ステージの履歴データをプッシュ |
| `POST /api/push_injection_tasks` | タスクをインジェクション（フロントエンドがプッシュ、TaskGraph がプル） |

## データモデル

### StructureModel

```python
class StructureModel(BaseModel):
    items: list[dict[str, Any]]
```

### StatusModel

```python
class StatusModel(BaseModel):
    status: dict[str, dict]
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
    errors: list[dict]
    offset: int
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

### HistoryModel

```python
class HistoryModel(BaseModel):
    history: dict[str, list[dict]]
    # key: ステージタグ; value: [{timestamp, tasks_processed}, ...]
```

### TaskInjectionModel

```python
class TaskInjectionModel(BaseModel):
    node: str             # ターゲットステージタグ
    task_datas: list[Any] # タスクデータリスト
    timestamp: datetime   # タイムスタンプ
```

### WebConfigModel

```python
class WebConfigModel(BaseModel):
    theme: str                        # "light" または "dark"
    refreshInterval: int              # リフレッシュ間隔（ミリ秒）
    historyLimit: int                 # 履歴レコードの最大保持件数
    dashboard: DashboardConfigModel   # ダッシュボードレイアウト設定
    cards: dict[str, CardConfigModel] # 各カードのタイトル設定

class DashboardConfigModel(BaseModel):
    left: list[str]    # 左カラムのカードキーリスト
    middle: list[str]  # 中央カラムのカードキーリスト
    right: list[str]   # 右カラムのカードキーリスト

class CardConfigModel(BaseModel):
    title: str         # カードタイトル
```

## 設定管理

Web サービスの設定は `web/config.json` に永続化されます。

- `load_config()` -- 起動時に読み込み、`WebConfigModel` で検証
- `save_config(config)` -- 設定を JSON ファイルに保存、スレッドセーフ（`_config_lock` を使用）
- `cal_interval(refresh_interval)` -- ミリ秒のリフレッシュ間隔を秒に変換、`[1.0, 60.0]` の範囲に制限

フロントエンドが `push_config` で設定を更新すると、`report_interval` も同期的に更新されます。

## TaskGraph との統合

### TaskGraph での有効化

```python
from celestialflow import TaskGraph

graph = TaskGraph()
graph.set_stages(root_stages=[stage_a])
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
    |--- push_history --------->|                          |
    |                           |                          |
    |--- push_errors_meta ----->|---- Errors ------------->|
    |--- push_errors_content -->|                          |
    |                           |                          |
    |<-- pull_task_injection ---|<--- Inject Tasks --------|
    |<-- pull_interval ---------|<--- Web Config ----------|
    |                           |                          |
```

## エラー処理

### キャッシュメカニズム

`push_errors_meta` と `push_errors_content` は `(jsonl_path, rev)` に基づくキャッシュをサポートします:

- パスとバージョン番号の両方が変更されていない場合、ファイルを再読み込みせずに `{"ok": true, "cached": true}` を返します
- それ以外の場合はデータを再読み込みし、`_errors_meta_path` / `_errors_meta_rev` を更新します

### グレースフルデグラデーション

JSONL ファイルを読み取れない場合、`push_errors_meta` はフォールバック指示を返します:

```json
{
    "ok": false,
    "fallback": "need_content",
    "reason": "FileNotFoundError",
    "msg": "File not found"
}
```

このレスポンスを受信すると、クライアントは `push_errors_content` に切り替えてエラーコンテンツを直接送信します。

### タスクインジェクションの並行安全性

`injection_tasks` リストは `_task_injection_lock` で保護されています。`push_injection_tasks` の書き込みと `pull_task_injection` の読み取り（クリアを含む）の両方がロック内で操作され、競合状態を防ぎます。

## 注意事項

1. **ポート競合**: 指定されたポートが使用中でないことを確認してください。
2. **ファイアウォール**: リモートアクセスが必要な場合、ファイアウォールルールを設定してください。
3. **HTTPS**: 本番環境では、リバースプロキシ（例: Nginx）を使用して HTTPS を追加することを推奨します。
4. **認証**: 現在のバージョンには組み込み認証がありません。本番環境では認証レイヤーの追加を推奨します。
