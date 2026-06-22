# Web モジュール

> 📅 最終更新日: 2026/06/22

Web モジュールは、FastAPI とネイティブ TypeScript で構築されたインタラクティブな監視・管理インターフェースを提供します。タスク状態のリアルタイム可視化、エラー追跡、動的タスク注入、グローバル設定管理をサポートします。

## モジュール概要

Web モジュールは `TaskReporter` とエンドユーザーの間のブリッジとして機能します。一方では RESTful API サーバーとしてランタイムからの状態スナップショットを受信・キャッシュし、他方では高パフォーマンス・低レイテンシのシングルページアプリケーション (SPA) を提供し、開発者がグラフタスクの実行フロー、パフォーマンスボトルネック、例外詳細を直感的に観察できるようにします。

## ファイル説明

### コアバックエンドコンポーネント

1. **core_server.py** (`TaskWebServer`)
   - **役割**: Web コアサーバー。データキャッシュ、バージョン管理（known_rev）、API ルーティングを管理。
   - **主要機能**: 状態集約、設定永続化、エラーページングクエリ、タスク注入中継。

2. **util_error.py**
   - **役割**: エラーログのフィルタリング、正規化、ページングロジックを提供。

3. **util_config.py**
   - **役割**: `config.json` の読み書きを担当し、設定のデグレード起動をサポート。

### コアフロントエンドコンポーネント

フロントエンド TypeScript ソースファイルは `web/static/ts/` にあり、JS にコンパイル後 `templates/index.html` で読み込まれます：

1. **main.ts** — グローバルエントリとポーリング調整
2. **utils.ts** — 汎用ユーティリティ関数
3. **i18n.ts** — 国際化サポート
4. **web_config.ts** — 設定管理ロジック
5. **dashboard_statuses.ts** — 動的ノードカードをレンダリングし、各ステージのリアルタイムパフォーマンス指標とプログレスバーを表示
6. **dashboard_structure.ts** — Mermaid.js ベースでタスクグラフトポロジ構造をレンダリング。動的ノード着色をサポート
7. **dashboard_history.ts** — 複数指標の履歴シーケンスを管理し、Chart.js で進捗折れ線グラフをレンダリング
8. **dashboard_summary.ts** — グローバル統計ダッシュボードのレンダリングと更新
9. **dashboard_analysis.ts** — トポロジ分析情報の表示
10. **errors.ts** — エラーログのページング表示と詳細フィルタリング
11. **injection.ts** — タスク手動注入 UI を管理。複数ノードの一括注入をサポート
12. **layout_editor.ts** — カードレイアウトエディタ（web_config の CARD_TEMPLATES/PANEL_SELECTOR_MAP に依存）

## アーキテクチャの特徴

### クライアント側履歴蓄積
フロントエンドとバックエンド間の通信頻度を大幅に削減するため、履歴トレンドデータはバックエンドが全量プッシュするのではなく、フロントエンドが連続的な状態スナップショット（Status Snapshot）に基づいてブラウザメモリ内で自律的に蓄積・管理します。

### 増分プル機構
全てのプルインターフェース（`pull_*`）は `known_rev` 機構をサポートします。バックエンドのデータバージョンが変更された場合のみ実際の Payload を転送し、そうでなければバージョン番号のみを返すことで、ポーリング帯域幅を大幅に節約します。

### 設定デグレード起動
システムは堅牢な初期化フローを設計しています：バックエンド設定の読み込みに失敗した場合、フロントエンドは自動的に組み込みの `DEFAULT_WEB_CONFIG` にフォールバックし、監視パネルが常に正常にレンダリングされ基本データを表示できることを保証します。

## 使用パターン

### サーバー起動
```bash
# 直接运行命令行工具
celestialflow-web --port 5000
```

### タスク注入例
```python
import requests

# 注入新任务到指定节点（格式：{节点名: [任务列表]}）
requests.post("http://localhost:5000/api/push_injection_tasks", json={
    "Stage_A": [{"id": 1, "data": "payload"}]
})
```

## 使用例

### TaskWebServer の作成と起動の基本例

```python
from celestialflow import TaskWebServer

# 创建服务器实例
server = TaskWebServer(
    host="127.0.0.1",   # 监听地址
    port=5000,            # 监听端口
    log_level="info",    # 日志级别
)

# 启动服务器（阻塞调用，会一直运行）
server.start_server()
```

起動後、ブラウザで `http://127.0.0.1:5000` にアクセスすると Web UI 監視パネルが表示されます。

### 完全なデータ報告チェーンの例

```python
from celestialflow import TaskGraph, TaskStage, TaskWebServer
from celestialflow.persistence import LogInlet
from celestialflow.observability import TaskReporter
import asyncio


async def main():
    # 1. 先启动 Web 服务器（在后台线程中运行）
    server = TaskWebServer(host="127.0.0.1", port=5000, log_level="info")
    # 实际生产环境中 server.start_server() 会阻塞，
    # 此处示意 reporter 与 server 配合的流程

    # 2. 创建任务图
    def process(x: int) -> int:
        return x * 2

    graph = TaskGraph(name="DemoGraph", schedule_mode="eager")
    stage = TaskStage("Processor", process, execution_mode="thread")
    graph.set_stages([stage])

    # 3. 创建并启动 TaskReporter
    log_inlet = LogInlet()
    reporter = TaskReporter(
        host="127.0.0.1",
        port=5000,
        task_graph=graph,
        log_inlet=log_inlet,
    )
    reporter.start()

    # 4. 执行任务
    graph.start_graph({stage.get_name(): range(50)})

    # 5. 停止上报器
    reporter.stop()


asyncio.run(main())
```
