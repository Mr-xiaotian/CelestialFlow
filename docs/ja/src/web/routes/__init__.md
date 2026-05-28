# Runtime ルート組立エントリ

> 📅 最終更新日: 2026/05/28

## 目的

`__init__.py`（つまり `celestialflow.web.routes` パッケージエントリ）は、すべての Web API ルートの組立エントリポイントです。`APIRouter` を作成し、**Pull**（データ取得）と **Push**（データプッシュ）の2つのサブルートモジュールを登録し、ルートパスのページエントリも登録します。

## コア関数

### `create_router(server: TaskWebServer) -> APIRouter`

完全に組み立てられた `APIRouter` インスタンスを作成して返し、FastAPI アプリケーションにマウントします。

| パラメータ | 型 | 説明 |
|-----------|------|------|
| `server` | `TaskWebServer` | タスク Web サーバーインスタンス。ルートはこの参照を通じてデータストア、設定、その他の共有状態にアクセス |

**登録されるルート:**

| パス | メソッド | 説明 |
|------|--------|------|
| `/` | `GET` | ページエントリ。`templates/index.html` を返す |
| `/api/pull_*` | `GET` | `pull_routes.register()` で登録されるすべての取得エンドポイント |
| `/api/push_*` | `POST` | `push_routes.register()` で登録されるすべてのプッシュエンドポイント |

**登録順序:**

```
┌──────────────────────────────────────┐
│  APIRouter                           │
│                                      │
│  1. GET  /          (index.html)     │
│  2. GET  /api/pull_*                 │
│  3. POST /api/push_*                 │
└──────────────────────────────────────┘
```

すべてのルートは同じ `TaskWebServer` インスタンスを共有するため、Push ルートの更新はすぐに Pull ルートのレスポンスに反映されます。

## 使用例

```python
from celestialflow.web.routes import create_router
from celestialflow.web.core_server import TaskWebServer

server = TaskWebServer(...)
router = create_router(server)

# FastAPI アプリケーションにマウント
from fastapi import FastAPI
app = FastAPI()
app.include_router(router)
```
