# Pull ルート（GET）— `pull_routes`

> 📅 最終更新日: 2026/06/22

## 役割

`pull_routes` モジュールはクライアントが**データを取得**するための全 GET エンドポイントを提供します。大部分のインターフェースは **rev（バージョン番号）ガード** 機構を採用しています：クライアントが保持する `known_rev` が現在のバージョンと一致する場合、帯域幅節約のために `data: null` を返し、データが変更された場合のみ完全なデータボディを返します。

## コア関数

### `register(router: APIRouter, server: TaskWebServer) -> None`

指定された `APIRouter` に全7つの GET エンドポイントを登録します。

| パラメータ | 型 | 説明 |
|------|------|------|
| `router` | `APIRouter` | FastAPI ルーターインスタンス |
| `server` | `TaskWebServer` | 共有状態を保持する Web サーバーインスタンス |

---

## エンドポイント

### 1. `GET /api/pull_server_state`

Reporter 同期決定に必要なサーバー状態を返します。

| パラメータ | 型 | デフォルト値 | 説明 |
|------|------|--------|------|
| `graph_id` | `str` | `""` | Reporter 現在のタスクグラフインスタンスの一意識別子 |

**戻り値：** `dict[str, Any]` — `interval`、`is_current_graph`、`has_structure`、`has_analysis`、`max_event_id_in_fail` を含みます。

```json
{
  "interval": 5.0,
  "is_current_graph": true,
  "has_structure": true,
  "has_analysis": false,
  "max_event_id_in_fail": null
}
```

---

### 2. `GET /api/pull_task_injection`

現在の実行待ち注入タスクキューを取り出してクリアします。これは**ワンタイム消費**エンドポイントです：返却後キューはクリアされ、同じバッチのタスクが重複取得されることはありません。

| パラメータ | 型 | デフォルト値 | 説明 |
|------|------|--------|------|
| — | — | — | パラメータなし |

**戻り値：** `dict[str, list[Any]]` — ノード名からタスクリストへのマッピング。読み取り後キューはクリアされます。

```json
{"StageA": [1, 2, 3], "StageB": [{"id": 4, "val": "x"}]}
```

> 注意：現在の実装では GET を使用していますが、このエンドポイントには副作用があり、読み取り後にキューがクリアされます。これは「消費インターフェース」により近く、純粋なクエリインターフェースではありません。

---

### 3. `GET /api/pull_config`

フロントエンド設定を取得します。

| パラメータ | 型 | デフォルト値 | 説明 |
|------|------|--------|------|
| — | — | — | パラメータなし |

**戻り値：** `dict[str, Any]` — 完全な `server.config` 辞書。`global`、`dashboard`、`errors`、`injection` グループを含みます。

---

### 4. `GET /api/pull_structure`

グラフ構造データ（ノードとエッジ）を取得します。rev ガード対応。

| パラメータ | 型 | デフォルト値 | 説明 |
|------|------|--------|------|
| `known_rev` | `int` | `-1` | クライアントが既知のバージョン番号 |

**戻り値：** `{"rev": int, "data": dict | None}` — `data` は構造辞書（`nodes`/`edges`/`source_nodes` を含む）。`known_rev==rev` の場合は `null` になります。

---

### 5. `GET /api/pull_status`

各ノードの実行状態を取得します。rev ガード対応。

| パラメータ | 型 | デフォルト値 | 説明 |
|------|------|--------|------|
| `known_rev` | `int` | `-1` | クライアントが既知のバージョン番号 |

**戻り値：** `{"rev": int, "timestamp": float, "data": dict | None}`

---

### 6. `GET /api/pull_errors`

ページングされたエラーログを取得します。ノード/キーワードフィルタリング対応、rev ガード対応。

| パラメータ | 型 | デフォルト値 | 説明 |
|------|------|--------|------|
| `known_rev` | `int` | `-1` | クライアントが既知のバージョン番号 |
| `page` | `int` | `1` | ページ番号（1から開始） |
| `page_size` | `int` | `10` | 1ページあたりの件数 |
| `node` | `str` | `""` | ノード名でフィルタ。空文字列は無効 |
| `keyword` | `str` | `""` | キーワードでフィルタ。空文字列は無効 |
| `sort_order` | `str` | `"newest"` | ソート方式。`newest` / `oldest` のみ対応 |

**戻り値：** `{"rev": int, "page": int, "page_size": int, "total": int, "total_pages": int, "sort_order": str, "data": list | None}`

---

### 7. `GET /api/pull_analysis`

グラフトポロジ分析情報を取得します。

| パラメータ | 型 | デフォルト値 | 説明 |
|------|------|--------|------|
| `known_rev` | `int` | `-1` | クライアントが既知のバージョン番号（現在のバージョンでは常に完全データを返す） |

**戻り値：** `{"rev": int, "data": dict | None}` — 分析データがまだ生成されていない場合は `data` が `None` になります。

> **注意**：`pull_analysis` は `known_rev` をチェックせず、毎回完全データを返します（分析データが存在する場合）。この動作は `pull_status`/`pull_structure`/`pull_errors` とは異なります。

## 使用例

```python
# 轮询拉取结构数据，仅在版本变化时处理
import requests

# 初始请求
resp = requests.get("http://localhost:8000/api/pull_structure")
data = resp.json()
known_rev = data["rev"]
if data["data"] is not None:
    render_structure(data["data"])

# 后续轮询
while True:
    resp = requests.get(
        "http://localhost:8000/api/pull_structure",
        params={"known_rev": known_rev}
    )
    data = resp.json()
    if data["data"] is not None:
        known_rev = data["rev"]
        render_structure(data["data"])
    time.sleep(5)
```
