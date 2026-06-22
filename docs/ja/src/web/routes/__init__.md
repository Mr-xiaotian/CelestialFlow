# Web ルート組み立てエントリ

> 📅 最終更新日: 2026/06/22

## 役割

`__init__.py`（すなわち `celestialflow.web.routes` パッケージエントリ）は Web API ルート全体の組み立て起点です。`APIRouter` を作成し、**Pull**（データ取得）と **Push**（データ送信）の2つのサブルートモジュールを登録し、ルートパスのページエントリも登録します。

## コア関数

### `create_router(server: TaskWebServer) -> APIRouter`

組み立て済みの `APIRouter` インスタンスを作成して返し、FastAPI アプリケーションにマウントします。

| パラメータ | 型 | 説明 |
|------|------|------|
| `server` | `TaskWebServer` | タスク Web サーバーインスタンス。ルートはこの参照を通じてデータストア、設定などの共有状態にアクセスします |

**登録されるルート：**

| パス | メソッド | 説明 |
|------|------|------|
| `/` | `GET` | ページエントリ。`templates/index.html` を返す |
| `/api/pull_*` | `GET` | `pull_routes.register()` で登録された全プルエンドポイント |
| `/api/push_*` | `POST` | `push_routes.register(router, server, config_path)` で登録された全プッシュエンドポイント |

**登録順序：**

```
┌──────────────────────────────────────┐
│  APIRouter                           │
│                                      │
│  1. GET  /          (index.html)     │
│  2. GET  /api/pull_*                 │
│  3. POST /api/push_*                 │
└──────────────────────────────────────┘
```

全てのルートは同じ `TaskWebServer` インスタンスを共有するため、Push ルートがデータを更新すると Pull ルートは即座に最新状態を返せます。

## 使用例

```python
from celestialflow.web.routes import create_router
from celestialflow.web.core_server import TaskWebServer

server = TaskWebServer(...)
router = create_router(server)

# 挂载到 FastAPI 应用
from fastapi import FastAPI
app = FastAPI()
app.include_router(router)
```
