# Pull ルート（GET）— `pull_routes`

> 📅 最終更新日: 2026/06/05

## 目的

`pull_routes` モジュールは、クライアントがデータを**取得**するためのすべての GET エンドポイントを提供します。これらのエンドポイントは **rev（バージョン番号）ガード** メカニズムを使用します：クライアントが渡した `known_rev` が現在のバージョンと一致する場合、帯域幅節約のために `data: null` を返します。変更があった場合のみ完全なデータが返されます。

## コア関数

### `register(router: APIRouter, server: TaskWebServer) -> None`

指定された `APIRouter` に全 7 つの GET エンドポイントを登録します。

| パラメータ | 型 | 説明 |
|------|------|------|
| `router` | `APIRouter` | FastAPI ルーターインスタンス |
| `server` | `TaskWebServer` | 共有状態を保持する Web サーバーインスタンス |

---

## エンドポイント

### 1. `GET /api/pull_config`

フロントエンド設定を取得します。

| パラメータ | 型 | デフォルト | 説明 |
|------|------|--------|------|
| — | — | — | パラメータなし |

**戻り値:** `dict[str, Any]` — 完全な `server.config` 辞書。

```json
{
  "theme": "dark",
  "autoRefreshEnabled": true,
  "refreshInterval": 5,
  "historyLimit": 20,
  "language": "zh-CN",
  "errorPageSize": 10,
  "errorSortOrder": "newest",
  "showStructureEdgeDelta": true,
  "dashboard": { "left": ["mermaid"], "middle": ["status"], "right": ["progress"] }
}
```

---

### 2. `GET /api/pull_structure`

グラフ構造データ（ノードとエッジ）を取得。rev ガード対応。

| パラメータ | 型 | デフォルト | 説明 |
|------|------|--------|------|
| `known_rev` | `int` | `-1` | クライアントが既に持っているバージョン番号 |

**戻り値:**

| フィールド | 説明 |
|------|------|
| `rev` | 現在のバージョン番号 |
| `data` | グラフ構造辞書。`known_rev==rev` の場合は `null` |

```json
// 更新あり
{"rev": 5, "data": {"nodes": {"n1": {"label": "Task"}}, "edges": {"n1": []}, "source_nodes": ["n1"]}}
// 更新なし
{"rev": 5, "data": null}
```

---

### 3. `GET /api/pull_status`

各ノードの実行状態を取得。rev ガード対応。

| パラメータ | 型 | デフォルト | 説明 |
|------|------|--------|------|
| `known_rev` | `int` | `-1` | クライアントが既に持っているバージョン番号 |

**戻り値:**

| フィールド | 説明 |
|------|------|
| `rev` | 現在のバージョン番号 |
| `timestamp` | 状態タイムスタンプ（float） |
| `data` | ノード状態辞書。変更なしの場合は `null` |

```json
{"rev": 3, "timestamp": 1716883200.5, "data": {"n1": "success", ...}}
```

---

### 4. `GET /api/pull_errors`

ページネーションされたエラーログを取得。ノード/キーワードフィルタリングと rev ガード対応。

| パラメータ | 型 | デフォルト | 説明 |
|------|------|--------|------|
| `known_rev` | `int` | `-1` | クライアントが既に持っているバージョン番号 |
| `page` | `int` | `1` | ページ番号（1 から開始） |
| `page_size` | `int` | `10` | 1ページあたりの件数 |
| `node` | `str` | `""` | ノード名でフィルタ。空文字列は無効 |
| `keyword` | `str` | `""` | キーワードでフィルタ。空文字列は無効 |
| `sort_order` | `str` | `"newest"` | ソート方式。`newest` / `oldest` のみ対応 |

**戻り値:**

| フィールド | 説明 |
|------|------|
| `rev` | 現在のバージョン番号 |
| `page` | 正規化されたページ番号 |
| `page_size` | 正規化されたページサイズ |
| `total` | フィルタ後の総件数 |
| `total_pages` | 総ページ数 |
| `sort_order` | 実際に適用されたソート方式 |
| `data` | 現在のページのエラーリスト。変更なしの場合は `null` |

```json
{
  "rev": 12, "page": 1, "page_size": 10,
  "total": 47, "total_pages": 5,
  "data": [{"ts": "...", "error_id": "...", "error_repr": "..."}, ...]
}
```

---

### 5. `GET /api/pull_analysis`

グラフトポロジ分析情報を取得。rev ガード対応。

| パラメータ | 型 | デフォルト | 説明 |
|------|------|--------|------|
| `known_rev` | `int` | `-1` | クライアントが既に持っているバージョン番号 |

**戻り値:** `{"rev": int, "data": dict | None}`

```json
{"rev": 2, "data": {"root_count": 3, "max_depth": 5, ...}}
```

---

### 6. `GET /api/pull_interval`

現在のポーリング間隔を取得します。

| パラメータ | 型 | デフォルト | 説明 |
|------|------|--------|------|
| — | — | — | パラメータなし |

**戻り値:** `{"interval": float}` — 秒単位。

```json
{"interval": 5.0}
```

---

### 7. `GET /api/pull_task_injection`

現在保留中の注入タスクキューを取得してクリアします。これは**ワンショット消費**エンドポイントです：レスポンス後にキューは空になり、同じバッチのタスクが再度取得されることはありません。

| パラメータ | 型 | デフォルト | 説明 |
|------|------|--------|------|
| — | — | — | パラメータなし |

**戻り値:** `list[dict[str, Any]]`

```json
[{"node": "StageA", "task_datas": [1, 2, 3], "timestamp": "2026-06-05T12:00:00"}, ...]
```

> 注意：現在の実装では GET を使用していますが、このエンドポイントには副作用があり、読み取り後にキューがクリアされます。純粋なクエリインターフェースというより「消費インターフェース」に近いです。

## 使用例

```python
# 構造データをポーリングし、バージョン変更時のみ処理
import requests

# 初回リクエスト
resp = requests.get("http://localhost:8000/api/pull_structure")
data = resp.json()
known_rev = data["rev"]
if data["data"] is not None:
    render_structure(data["data"])

# 後続のポーリング
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
