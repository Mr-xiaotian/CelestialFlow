# Push ルート（POST）— `push_routes`

> 📅 最終更新日: 2026/06/22

## 役割

`push_routes` モジュールは **Reporter（報告側）** がサーバー側に**データを送信**するための全 POST エンドポイントを提供します。各送信は対応するメモリストアを更新し、バージョン番号（`store_revs`）をインクリメントすることで、クライアントが Pull ルートを通じてデータ変更を感知できるようにします。すべての Reporter 側送信には `graph_id` が必要であり、サーバー側で現在の graph インスタンスかどうかを検証します。

## コア関数

### `register(router: APIRouter, server: TaskWebServer, config_path: str) -> None`

指定された `APIRouter` に全6つの POST エンドポイントを登録します。

| パラメータ | 型 | 説明 |
|------|------|------|
| `router` | `APIRouter` | FastAPI ルーターインスタンス |
| `server` | `TaskWebServer` | 共有状態を保持する Web サーバーインスタンス |
| `config_path` | `str` | 設定ファイルのディスクパス。設定の永続化保存に使用 |

---

## エンドポイント

### 1. `POST /api/push_config`

フロントエンド設定を保存し、ポーリング間隔を更新します。

**リクエストボディ：** `WebConfigModel`

```json
{
  "global": {
    "theme": "dark",
    "autoRefreshEnabled": true,
    "refreshInterval": 5000,
    "language": "zh-CN"
  },
  "dashboard": {
    "historyLimit": 20,
    "showStructureEdgeDelta": false,
    "useTotalPendingInStatus": false,
    "layout": { "left": ["mermaid"], "middle": ["status"], "right": ["progress"] }
  },
  "errors": {
    "pageSize": 10,
    "sortOrder": "newest",
    "jumpToInjectionAfterRetry": true
  },
  "injection": {
    "showInjectableOnly": true
  }
}
```

**ロジック：**
1. リクエストボディを辞書にデシリアライズし、`server.config` を更新
2. `refreshInterval` 値に基づいて `server.report_interval` を再計算
3. `save_config()` を呼び出して設定を `config_path` に永続化
4. 保存成功時は `{"ok": true}` を返し、失敗時は HTTP 500 を返す

> 注意：現在の実装では、まずメモリ内の `server.config` と `server.report_interval` を更新し、その後ディスク保存を試みます。`save_config()` が失敗した場合、リクエストは 500 を返しますが、プロセス内の設定は既に変更されています。

**戻り値：**
- 成功：`{"ok": true}`
- 失敗：`{"ok": false, "error": "Failed to save config"}`（ステータスコード 500）

---

### 2. `POST /api/push_structure`

グラフ構造データを更新します。

**リクエストボディ：** `StructureModel`（`graph_id` と `structure` フィールドを含む）

```json
{
  "graph_id": "graph-001",
  "structure": {
    "nodes": {"n1": {"label": "MyTask"}},
    "edges": {"n1": []},
    "source_nodes": ["n1"]
  }
}
```

**ロジック：**
1. `data.graph_id` が現在の graph コンテキストかどうかを検証。一致しない場合は `{"ok": false}` を返す
2. `data.structure` をアトミックに `server.structure_store` に書き込み
3. `server.store_revs["structure"]` を 1 インクリメント

**戻り値：** `{"ok": true}` または `{"ok": false}`

---

### 3. `POST /api/push_status`

各ノードの実行状態を更新します。

**リクエストボディ：** `StatusModel`（`graph_id`、`timestamp`、`status` フィールドを含む）

```json
{
  "graph_id": "graph-001",
  "timestamp": 1716883200.5,
  "status": {"node_a": "running", "node_b": "success"}
}
```

**ロジック：**
1. `data.graph_id` が現在の graph コンテキストかどうかを検証
2. `server.status_timestamp` と `server.status_store` を更新
3. `server.store_revs["status"]` を 1 インクリメント

**戻り値：** `{"ok": true}` または `{"ok": false}`

---

### 4. `POST /api/push_errors`

エラーログリストを直接受信し SQLite に書き込みます。

**リクエストボディ：** `ErrorsModel`（`graph_id` と `errors` フィールドを含む）

```json
{
  "graph_id": "graph-001",
  "errors": [
    {"ts": "2026-06-18T10:00:00", "error_id": "e1", "error_type": "ValueError", "error_message": "..."}
  ]
}
```

**ロジック：**
1. `data.graph_id` が現在の graph コンテキストかどうかを検証
2. `append_records` を呼び出してエラーを SQLite データベースに書き込み
3. `server.store_revs["errors"]` を 1 インクリメント

**戻り値：** `{"ok": true}` または `{"ok": false}`

---

### 5. `POST /api/push_analysis`

グラフトポロジ分析情報を更新します。

**リクエストボディ：** `AnalysisModel`（`graph_id` と `analysis` フィールドを含む）

```json
{
  "graph_id": "graph-001",
  "analysis": {"root_count": 3, "max_depth": 5}
}
```

**ロジック：**
1. `data.graph_id` が現在の graph コンテキストかどうかを検証
2. `server.analysis_store` を更新
3. `server.store_revs["analysis"]` を 1 インクリメント

**戻り値：** `{"ok": true}` または `{"ok": false}`

---

### 6. `POST /api/push_injection_tasks`

フロントエンドから送信された注入タスクを実行待ちキューに書き込みます。

**リクエストボディ：** `TaskInjectionModel`（`RootModel[dict[str, list[Any]]]`）

```json
{
  "StageA": [1, 2, 3],
  "StageB": [{"id": 4, "val": "x"}]
}
```

**ロジック：**
1. `task_injection_lock` ロックを取得
2. `data.root` を走査し、`{node_name: task_list}` 方式で `server.injection_tasks` に書き込み
3. ロックを解放

> 注意：リクエストボディは直接 `{ノード名: [タスクリスト]}` 形式の辞書であり、`node`/`task_datas`/`timestamp` フィールドでラップされなくなりました。各ノード名に対応するタスクリストは、そのノードの既存の注入待ちタスクを**上書き**します（追加ではありません）。

**戻り値：**
- 成功：`{"ok": true}`
- 失敗：`{"ok": false, "msg": "タスク注入に失敗: ..."}`（ステータスコード 500）

---

## 使用例

### Reporter 側から状態とエラーを送信

```python
import requests

BASE = "http://localhost:8000"

# 推送节点状态
requests.post(f"{BASE}/api/push_status", json={
    "graph_id": "graph-001",
    "timestamp": 1716883200.5,
    "status": {
        "node_a": {"state": "running", "pending": 0},
        "node_b": {"state": "success", "pending": 0}
    }
})

# 推送错误日志
requests.post(f"{BASE}/api/push_errors", json={
    "graph_id": "graph-001",
    "errors": [
        {"ts": "2026-06-18T10:00:00", "error_id": "e1", "error_type": "ValueError", "error_message": "Invalid input"}
    ]
})

# 推送结构数据
requests.post(f"{BASE}/api/push_structure", json={
    "graph_id": "graph-001",
    "structure": {
        "nodes": {"n1": {"label": "MyTask"}},
        "edges": {"n1": []},
        "source_nodes": ["n1"],
    }
})
```

### Web フロントエンドで設定を保存

```javascript
const resp = await fetch("/api/push_config", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    global: {
      theme: "dark",
      autoRefreshEnabled: true,
      refreshInterval: 10000,
      language: "zh-CN",
    },
    dashboard: {
      historyLimit: 20,
      showStructureEdgeDelta: false,
      useTotalPendingInStatus: false,
      layout: { left: ["mermaid"], middle: ["status"], right: ["progress"] }
    },
    errors: {
      pageSize: 10,
      sortOrder: "newest",
      jumpToInjectionAfterRetry: true,
    },
    injection: {
      showInjectableOnly: true,
    },
  })
});
const result = await resp.json();
console.log(result.ok ? "保存成功" : "保存失败");
```
