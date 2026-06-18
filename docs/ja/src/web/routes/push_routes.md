# Push ルート（POST）— `push_routes`

> 📅 最終更新日: 2026/06/18

## 役割

`push_routes` モジュールは **Reporter（報告側）** がサーバー側に**データを送信**するための全 POST エンドポイントを提供します。各送信は対応するメモリストアを更新し、バージョン番号（`store_revs`）をインクリメントすることで、クライアントが Pull ルートを通じてデータ変更を感知できるようにします。エラーデータは**キャッシュヒット**最適化（path + rev が変わらなければ再読み込みをスキップ）をサポートします。

## コア関数

### `register(router: APIRouter, server: TaskWebServer, config_path: str) -> None`

指定された `APIRouter` に全7つの POST エンドポイントを登録します。

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

**リクエストボディ：** `StructureModel`（`structure` フィールドを含む）

**ロジック：**
1. `data.structure` をアトミックに `server.structure_store` に書き込み
2. `server.store_revs["structure"]` を 1 インクリメント

**戻り値：** `{"ok": true}`

---

### 3. `POST /api/push_status`

各ノードの実行状態を更新します。

**リクエストボディ：** `StatusModel`（`timestamp` と `status` フィールドを含む）

**ロジック：**
1. `server.status_timestamp` を更新
2. `server.status_store` を更新
3. `server.store_revs["status"]` を 1 インクリメント

**戻り値：** `{"ok": true}`

---

### 4. `POST /api/push_errors_meta`

JSONL ファイルパスとバージョン番号を通じてエラーログを読み込みます。キャッシュヒット対応。

**リクエストボディ：** `ErrorsMetaModel`

```json
{
  "rev": 5,
  "jsonl_path": "/var/log/celestialflow/errors.jsonl"
}
```

**ロジック：**

```
┌─────────────────────────────────────────┐
│  リクエスト到着                          │
│     ↓                                    │
│  キャッシュヒット？（path も rev も未変更）  │
│     ├─ はい → {"cached": true} を返す   │
│     └─ いいえ →                         │
│          try:                            │
│            load_jsonl_logs() を呼び出し  │
│            （独立スレッドで JSONL を読み取り）│
│            → error_store を更新          │
│            → キャッシュを更新 (rev+path) │
│            → store_revs["errors"] += 1   │
│            {"cached": false} を返す      │
│          except:                         │
│            fallback=need_content を返す  │
└─────────────────────────────────────────┘
```

**戻り値：**
- キャッシュヒット：`{"ok": true, "cached": true}`
- 読み込み成功：`{"ok": true, "cached": false}`
- 読み込み失敗：`{"ok": false, "fallback": "need_content", "reason": "...", "msg": "..."}`

> **注意：** 読み込み失敗時、呼び出し側は `push_errors_content` にフォールバックして直接エラー内容を送信する必要があります。

---

### 5. `POST /api/push_errors_content`

エラーログリストを直接受信して保存します。キャッシュヒット対応。

**リクエストボディ：** `ErrorsContentModel`

```json
{
  "rev": 5,
  "jsonl_path": "/var/log/celestialflow/errors.jsonl",
  "errors": [{"ts": "2026-05-28T10:00:00", "error_id": "...", ...}, ...]
}
```

**ロジック：**
- キャッシュヒット時はスキップし、直接 `{"cached": true}` を返す
- そうでない場合は `server.error_store` に書き込み、キャッシュとバージョン番号を更新

**戻り値：**
- キャッシュヒット：`{"ok": true, "cached": true}`
- 書き込み成功：`{"ok": true, "cached": false}`

---

### 6. `POST /api/push_analysis`

グラフトポロジ分析情報を更新します。

**リクエストボディ：** `AnalysisModel`（`analysis` フィールドを含む）

**ロジック：**
1. `server.analysis_store` を更新
2. `server.store_revs["analysis"]` を 1 インクリメント

**戻り値：** `{"ok": true}`

---

### 7. `POST /api/push_injection_tasks`

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

> 注意：リクエストボディは直接 `{ノード名: [タスクリスト]}` 形式の辞書であり、`node`/`task_datas`/`timestamp` フィールドでラップされなくなりました。各ノード名に対応するタスクリストは、そのノードの既存の注入待ちタスクを**上書き**します（追加以外）。

**戻り値：**
- 成功：`{"ok": true}`
- 失敗：`{"ok": false, "msg": "タスク注入に失敗: ..."}`（ステータスコード 500）

---

## 使用例

### Reporter 側の状態とエラーの送信

```python
import requests

BASE = "http://localhost:8000"

# ノード状態を送信
requests.post(f"{BASE}/api/push_status", json={
    "timestamp": 1716883200.5,
    "status": {"node_a": "running", "node_b": "success"}
})

# エラーログを送信（メタ情報モード：サーバー側に JSONL の自己読み取りを任せる）
resp = requests.post(f"{BASE}/api/push_errors_meta", json={
    "rev": 5,
    "jsonl_path": "/var/log/celestialflow/errors.jsonl"
})

# サーバー側の読み取りが失敗した場合、直接内容送信にフォールバック
data = resp.json()
if not data["ok"] and data.get("fallback") == "need_content":
    requests.post(f"{BASE}/api/push_errors_content", json={
        "rev": 5,
        "jsonl_path": "/var/log/celestialflow/errors.jsonl",
        "errors": [
            {"ts": "2026-05-28T10:00:00", "error_id": "e1", ...}
        ]
    })

# 構造データを送信
requests.post(f"{BASE}/api/push_structure", json={
    "structure": {
        "nodes": {"n1": {"label": "MyTask"}},
        "edges": {"n1": []},
        "source_nodes": ["n1"],
    }
})
```

### Web フロントエンドの設定保存

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
console.log(result.ok ? "保存成功" : "保存失敗");
```
