# Push ルート（POST）— `push_routes`

> 📅 最終更新日: 2026/06/05

## 目的

`push_routes` モジュールは、**Reporter（レポーター）** がサーバーにデータを**プッシュ**するためのすべての POST エンドポイントを提供します。各プッシュは対応するメモリ内ストアを更新し、バージョン番号（`store_revs`）をインクリメントします。これにより、クライアントは Pull ルートを通じてデータ変更を検出できます。エラーデータは**キャッシュヒット**最適化をサポートします（path + rev が変更されていない場合は再読み込みをスキップ）。

## コア関数

### `register(router: APIRouter, server: TaskWebServer, config_path: str) -> None`

指定された `APIRouter` に全 7 つの POST エンドポイントを登録します。

| パラメータ | 型 | 説明 |
|------|------|------|
| `router` | `APIRouter` | FastAPI ルーターインスタンス |
| `server` | `TaskWebServer` | 共有状態を保持する Web サーバーインスタンス |
| `config_path` | `str` | 設定ファイルのディスクパス。設定の永続化に使用 |

---

## エンドポイント

### 1. `POST /api/push_config`

フロントエンド設定を保存し、ポーリング間隔を更新します。

**リクエストボディ:** `WebConfigModel`

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

**ロジック:**
1. リクエストボディを辞書にデシリアライズし、`server.config` を更新
2. `refreshInterval` 値に基づいて `server.report_interval` を再計算
3. `save_config()` を呼び出して設定を `config_path` に永続化
4. 保存成功時は `{"ok": true}` を返し、失敗時は HTTP 500 を返す

> 注意：現在の実装では、まずメモリ内の `server.config` と `server.report_interval` を更新してからディスク保存を試みます。`save_config()` が失敗した場合、リクエストは 500 を返しますが、プロセス内の設定は既に変更されています。

**戻り値:**
- 成功: `{"ok": true}`
- 失敗: `{"ok": false, "error": "Failed to save config"}`（ステータスコード 500）

---

### 2. `POST /api/push_structure`

グラフ構造データを更新します。

**リクエストボディ:** `StructureModel`（`structure` フィールドを含む）

**ロジック:**
1. `data.structure` を `server.structure_store` にアトミック書き込み
2. `server.store_revs["structure"]` を 1 インクリメント

**戻り値:** `{"ok": true}`

---

### 3. `POST /api/push_status`

各ノードの実行状態を更新します。

**リクエストボディ:** `StatusModel`（`timestamp` と `status` フィールドを含む）

**ロジック:**
1. `server.status_timestamp` を更新
2. `server.status_store` を更新
3. `server.store_revs["status"]` を 1 インクリメント

**戻り値:** `{"ok": true}`

---

### 4. `POST /api/push_errors_meta`

JSONL ファイルパスとバージョン番号でエラーログを読み込み。キャッシュヒット対応。

**リクエストボディ:** `ErrorsMetaModel`

```json
{
  "rev": 5,
  "jsonl_path": "/var/log/celestialflow/errors.jsonl"
}
```

**ロジック:**

```
┌─────────────────────────────────────────┐
│  リクエスト到着                           │
│     ↓                                    │
│  キャッシュヒット？（path と rev が      │
│  変更されていない）                        │
│     ├─ はい → {"cached": true} を返す   │
│     └─ いいえ →                         │
│          try:                            │
│            load_jsonl_logs() を呼び出し  │
│            （別スレッドで JSONL を読み取り）│
│            → error_store を更新          │
│            → キャッシュを更新（rev+path） │
│            → store_revs["errors"] += 1   │
│            {"cached": false} を返す      │
│          except:                         │
│            fallback=need_content を返す  │
└─────────────────────────────────────────┘
```

**戻り値:**
- キャッシュヒット: `{"ok": true, "cached": true}`
- 読み込み成功: `{"ok": true, "cached": false}`
- 読み込み失敗: `{"ok": false, "fallback": "need_content", "reason": "...", "msg": "..."}`

> **注意:** 読み込み失敗時、呼び出し元は `push_errors_content` にフォールバックしてエラー内容を直接送信する必要があります。

---

### 5. `POST /api/push_errors_content`

エラーログリストを直接受信して保存。キャッシュヒット対応。

**リクエストボディ:** `ErrorsContentModel`

```json
{
  "rev": 5,
  "jsonl_path": "/var/log/celestialflow/errors.jsonl",
  "errors": [{"ts": "2026-05-28T10:00:00", "error_id": "...", ...}, ...]
}
```

**ロジック:**
- キャッシュヒット時はスキップして `{"cached": true}` を返す
- それ以外の場合は `server.error_store` に書き込み、キャッシュとバージョン番号を更新

**戻り値:**
- キャッシュヒット: `{"ok": true, "cached": true}`
- 書き込み成功: `{"ok": true, "cached": false}`

---

### 6. `POST /api/push_analysis`

グラフトポロジ分析情報を更新します。

**リクエストボディ:** `AnalysisModel`（`analysis` フィールドを含む）

**ロジック:**
1. `server.analysis_store` を更新
2. `server.store_revs["analysis"]` を 1 インクリメント

**戻り値:** `{"ok": true}`

---

### 7. `POST /api/push_injection_tasks`

フロントエンドから送信された注入タスクを保留中の実行キューに追加します。

**リクエストボディ:** `TaskInjectionModel`

```json
{
  "node": "StageA",
  "task_datas": [1, 2, 3],
  "timestamp": "2026-06-05T12:00:00"
}
```

**ロジック:**
1. `task_injection_lock` を取得
2. `data.model_dump(mode="json")` を `server.injection_tasks` に追加
3. ロックを解放

> 注意：バックエンドモデルは `task_datas` が配列であることを要求します。フロントエンドがオブジェクト、文字列、数値を渡した場合、FastAPI/Pydantic の検証段階で直接 422 が返されます。

**戻り値:**
- 成功: `{"ok": true}`
- 失敗: `{"ok": false, "msg": "タスク注入に失敗しました: ..."}`（ステータスコード 500）

---

## 使用例

### Reporter による状態とエラーのプッシュ

```python
import requests

BASE = "http://localhost:8000"

# ノード状態をプッシュ
requests.post(f"{BASE}/api/push_status", json={
    "timestamp": 1716883200.5,
    "status": {"node_a": "running", "node_b": "success"}
})

# エラーログをプッシュ（メタ情報モード：サーバーに JSONL を自分で読み取らせる）
resp = requests.post(f"{BASE}/api/push_errors_meta", json={
    "rev": 5,
    "jsonl_path": "/var/log/celestialflow/errors.jsonl"
})

# サーバー読み取り失敗時は、コンテンツを直接送信するフォールバック
data = resp.json()
if not data["ok"] and data.get("fallback") == "need_content":
    requests.post(f"{BASE}/api/push_errors_content", json={
        "rev": 5,
        "jsonl_path": "/var/log/celestialflow/errors.jsonl",
        "errors": [
            {"ts": "2026-05-28T10:00:00", "error_id": "e1", ...}
        ]
    })

# 構造データをプッシュ
requests.post(f"{BASE}/api/push_structure", json={
    "structure": {
        "nodes": {"n1": {"label": "MyTask"}},
        "edges": {"n1": []},
        "source_nodes": ["n1"],
    }
})
```

### Web フロントエンドでの設定保存

```javascript
const resp = await fetch("/api/push_config", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    theme: "dark",
    autoRefreshEnabled: true,
    refreshInterval: 10,
    historyLimit: 20,
    language: "zh-CN",
    errorPageSize: 10,
    errorSortOrder: "newest",
    showStructureEdgeDelta: true,
    dashboard: { left: ["mermaid"], middle: ["status"], right: ["progress"] }
  })
});
const result = await resp.json();
console.log(result.ok ? "保存成功" : "保存失敗");
```
