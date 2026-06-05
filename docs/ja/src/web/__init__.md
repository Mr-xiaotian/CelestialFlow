# Web モジュール

> 📅 最終更新日: 2026/05/23

Web モジュールは、インタラクティブな監視・管理インターフェースを提供します。FastAPI とネイティブ TypeScript で構築されており、タスク状態のリアルタイム可視化、エラー追跡、動的タスク注入、グローバル設定管理をサポートします。

## モジュール概要

Web モジュールは `TaskReporter` とエンドユーザー間のブリッジとして機能します。一方では RESTful API Server として動作し、ランタイムからの状態スナップショットを受信・キャッシュします。もう一方では高性能・低遅延のシングルページアプリケーション（SPA）を提供し、開発者がグラフタスクの実行フロー、パフォーマンスボトルネック、異常の詳細を直感的に観察できるようにします。

## ファイル説明

### コアバックエンドコンポーネント

1. **core_server.py** (`TaskWebServer`)
   - **役割**: Web コアサーバー。データキャッシュ、バージョン管理（known_rev）、API ルーティングを管理します。
   - **主要機能**: 状態集約、設定の永続化、エラーページネーションクエリ、タスク注入中継。

2. **util_error.py**
   - **役割**: エラーログのフィルタリング、正規化、ページネーションロジックを提供します。

3. **util_config.py**
   - **役割**: `config.json` の読み書きを担当し、設定のデグレード起動をサポートします。

### コアフロントエンドコンポーネント

1. **dashboard_history.ts**
   - **役割**: 複数指標の履歴シーケンスを維持し、Chart.js を使用して進捗折れ線グラフを描画します。指標のリアルタイム切り替えをサポートします。

2. **dashboard_statuses.ts**
   - **役割**: 動的ノードカードを描画し、各段階のリアルタイムパフォーマンス指標とプログレスバーを表示します。

3. **dashboard_structure.ts**
   - **役割**: Mermaid.js に基づいてタスクグラフトポロジ構造を描画し、動的ノード色付けをサポートします。

4. **injection.ts**
   - **役割**: タスク手動注入 UI を管理し、複数ノードのバッチ注入とファイルアップロードをサポートします。

5. **errors.ts**
   - **役割**: エラーログのページネーション表示と詳細フィルタリングを担当します。

## アーキテクチャ特徴

### クライアント履歴累積
フロントエンドとバックエンド間の通信頻度を大幅に削減するために、履歴トレンドデータはバックエンドからの全量プッシュではなく、フロントエンドが連続的な状態スナップショット（Status Snapshot）に基づいてブラウザメモリ内で自律的に累積・維持します。

### 増分取得メカニズム
すべての取得インターフェース（`pull_*`）は `known_rev` メカニズムをサポートします。バックエンドのデータバージョンが変更された場合のみ実際の Payload が送信され、それ以外の場合はバージョン番号のみが返されるため、ポーリング帯域幅を大幅に節約します。

### 設定デグレード起動
堅牢な初期化フローが設計されています：バックエンドの設定読み込みに失敗した場合、フロントエンドは自動的に組み込みの `DEFAULT_WEB_CONFIG` にフォールバックし、監視パネルがどのような状況でも正常にレンダリングされて基本データを表示できることを保証します。

## 使用パターン

### サーバーの起動
```bash
# コマンドラインツールを直接実行
celestialflow-web --port 5000
```

### タスク注入例
```python
import requests

# 指定ノードに新しいタスクを注入
requests.post("http://localhost:5000/api/push_injection_tasks", json={
    "node": "Stage_A",
    "task_datas": [{"id": 1, "data": "payload"}],
    "timestamp": "2026-05-23T10:00:00"
})
```

## 使用例

### TaskWebServer の作成と起動の基本例

```python
from celestialflow import TaskWebServer

# サーバーインスタンスを作成
server = TaskWebServer(
    host="127.0.0.1",   # リッスンアドレス
    port=5000,            # リッスンポート
    log_level="info",    # ログレベル
)

# サーバーを起動（ブロッキング呼び出し、継続的に実行されます）
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
    # 1. まず Web サーバーを起動（バックグラウンドスレッドで実行）
    server = TaskWebServer(host="127.0.0.1", port=5000, log_level="info")
    # 実際の本番環境では server.start_server() はブロッキングされます。
    # ここでは reporter と server の連携フローを示します

    # 2. タスクグラフを作成
    def process(x: int) -> int:
        return x * 2

    graph = TaskGraph(schedule_mode="eager")
    stage = TaskStage("Processor", process, execution_mode="thread")
    graph.set_stages([stage])

    # 3. TaskReporter を作成して起動
    log_inlet = LogInlet()
    reporter = TaskReporter(
        host="127.0.0.1",
        port=5000,
        task_graph=graph,
        log_inlet=log_inlet,
    )
    reporter.start()

    # 4. タスクを実行
    await graph.start_graph({stage.get_tag(): range(50)})

    # 5. レポーターを停止
    reporter.stop()


asyncio.run(main())
```
