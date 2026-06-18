# CelestialFlow —— 軽量で並列可能なグラフ構造ベースの Python タスクスケジューリングフレームワーク

<p align="center">
  <img src="https://raw.githubusercontent.com/Mr-xiaotian/CelestialFlow/main/img/logo.png" width="1080" alt="CelestialFlow Logo">
</p>

<p align="center">
  <a href="https://pypi.org/project/celestialflow/"><img src="https://badge.fury.io/py/celestialflow.svg"></a>
  <a href="https://pepy.tech/projects/celestialflow"><img src="https://static.pepy.tech/personalized-badge/celestialflow?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads"></a>
  <a href="https://pypi.org/project/celestialflow/"><img src="https://img.shields.io/pypi/l/celestialflow.svg"></a>
  <a href="https://pypi.org/project/celestialflow/"><img src="https://img.shields.io/pypi/pyversions/celestialflow.svg"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Task%20Graph-DAG-blueviolet">
  <img src="https://img.shields.io/badge/Workflow-Orchestrator-7c3aed">
  <img src="https://img.shields.io/badge/IPC-Redis%20Ready-red">
  <img src="https://img.shields.io/badge/Distributed-Worker%20Friendly-orange">
</p>

<p align="center">
  <a href="https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/README.md">中文</a> | <a href="https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/en/README.md">English</a> | <a href="https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/ja/README.md">日本語</a>
</p>

**CelestialFlow** は、軽量でありながら完全な機能を備えたタスクフローフレームワークで、**複雑な依存関係**、**柔軟な実行モデル**、**クロスデバイス実行**、**リアルタイム可視化監視**を必要とする中/大規模 Python タスクシステムに適しています。

- Airflow/Dagster より軽量で、より早く開始可能
- multiprocessing/threading より構造化されており、loop / complete graph などの複雑な依存パターンを直接表現可能

フレームワークの基本ユニットは **TaskExecutor** で、独立して実行でき、3 つの実行モードをサポートします：

* **リニア（serial）**
* **マルチスレッド（thread）**
* **コルーチン（async）**

TaskExecutor はタスクの結果キャッシュ、タスク重複排除、プログレスバー表示、多実行モード比較などの機能を実装しており、単独でも非常に使いやすくなっています。

ただし、TaskExecutor を直接使用する以外に、より重要なのはそのサブクラス **TaskStage** の使用です。TaskStage は相互に接続して、上流と下流の依存関係を持つタスクグラフ（**TaskGraph**）を形成できます。下流の stage は上流の実行完了結果を自動的に入力として受け取り、明確なデータフローを形成します。

TaskStage のタスク実行モードも TaskExecutor と同様に 3 つを含みます。

グラフレベルでは、各 Stage は 2 つのコンテキストモードをサポートします：

* **リニア実行（serial layout）**：現在のノードが実行完了してから次のノードを起動（下流ノードは事前にタスクを受信可能ですが、すぐには実行されません）。
* **スレッド実行（thread layout）**：現在のノードがメインプロセスの独立したスレッドで起動され、I/O 集中型タスクや pickle 不可能な関数（lambda など）に適しています。

TaskGraph は完全な **有向グラフ構造（Directed Graph）** を構築でき、従来の有向非巡回グラフ（DAG）だけでなく、**ツリー（Tree）**、**循環（loop）**、さらには **完全グラフ（Complete Graph）** 形式のタスク依存関係も柔軟に表現できます。

実行とスケジューリングに加えて、CelestialFlow はさらに **CelestialTree（略称: ctree）イベント追跡システム**を導入し、各タスクとその派生動作（成功、失敗、リトライ、分割、ルーティングなど）に明確な因果関係を記録します。ctree を利用することで、任意の初期タスクから出発し、TaskGraph 内での伝播経路と実行軌跡を完全に復元でき、タスクシステムの完全な**追跡、分析、解釈**が可能になります。

これに加えて、CelestialFlow は Web 可視化監視をサポートし、Redis を通じてクロスプロセス、クロスデバイス連携を実現できます。同時に Go ベースの外部 worker（Redis 経由で通信）を導入し、CPU 集中型タスクを処理することで、このシナリオでの Python のパフォーマンスボトルネックを補完します。

## プロジェクト構造（Project Structure）

```mermaid
flowchart LR

    %% ===== TaskGraph =====
    subgraph TG[TaskGraph]
        direction LR

        S1[TaskStage A]
        S2[TaskStage B]
        S3[TaskStage C]
        S4[TaskStage D]

        S1 --> S2 --> S3 --> S1
        S1 --> S4

    end

    %% TaskGraph の外枠を装飾
    style TG fill:#e8f2ff,stroke:#6b93d6,stroke-width:2px,color:#0b1e3f,rx:10px,ry:10px

    %% 統一装飾フォーマット
    classDef blueNode fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px;

    %% TaskStages を装飾
    class S1,S2,S3,S4 blueNode;

    %% ===== WebUI =====
    subgraph W[WebUI]
        JS
        HTML
    end

    style W fill:#ffeaf0,stroke:#d66b8c,stroke-width:2px,rx:10px,ry:10px
    style JS fill:#ffffff,stroke:#d66b8c,rx:5px,ry:5px
    style HTML fill:#ffffff,stroke:#d66b8c,rx:5px,ry:5px

    R[TaskWeb]
    style R fill:#f0e9ff,stroke:#8a6bc9,stroke-width:2px,rx:8px,ry:8px

    %% ===== Links =====
    TG --> R 
    R --> TG 
    R --> W
    W --> R

```

## クイックスタート（Quick Start）

CelestialFlow のインストール：

```bash
# 依存関係と環境の管理に `uv` の使用を推奨
uv pip install celestialflow

# ただし `pip` を直接使用することも可能
pip install celestialflow
```

シンプルな実行可能コード：

```python
from celestialflow import TaskStage, TaskGraph

def add(x, y): 
    return x + y

def square(x): 
    return x ** 2

if __name__ == "__main__":
    # 2 つのタスクノードを定義
    stage1 = TaskStage(name="Adder", func=add, stage_mode="thread", execution_mode="thread", unpack_task_args=True)
    stage2 = TaskStage(name="Squarer", func=square, stage_mode="thread", execution_mode="thread")

    # タスクグラフ構造を構築
    graph = TaskGraph()
    graph.set_stages(stages=[stage1, stage2])
    graph.connect([stage1], [stage2])

    # タスクを初期化して起動
    graph.start_graph({stage1.get_name(): [(1, 2), (3, 4), (5, 6)]})
```

.ipynb での実行は避けてください。

👉 完全な Quick Start は [Quick Start](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/quick_start.md) をご覧ください

## 詳細な読み物（Further Reading）

フレームワークの全体構造とコアコンポーネントを理解したい場合は、以下の参考ドキュメントが役立ちます：

- [stage/core_executor.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/stage/core_executor.md)
- [stage/core_stage.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/stage/core_stage.md)
- [graph/core_graph.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/graph/core_graph.md)
- [observability/core_progress.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/observability/core_progress.md)
- [runtime/core_metrics.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/runtime/core_metrics.md)
- [runtime/core_queue.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/runtime/core_queue.md)
- [stage/core_stages.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/stage/core_stages.md)
- [observability/core_report.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/observability/core_report.md)
- [graph/core_structure.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/graph/core_structure.md)
- [web/core_server.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/web/core_server.md)
- [other/go_worker.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/other/go_worker.md)

推奨読書順序：

```mermaid
flowchart TD
    classDef core fill:#e6efff,stroke:#3b82f6,color:#1e3a8a;
    classDef runtime fill:#e9f8ef,stroke:#22c55e,color:#14532d;
    classDef structure fill:#fff6e6,stroke:#f59e0b,color:#78350f;
    classDef execution fill:#f3e8ff,stroke:#a855f7,color:#581c87;
    classDef web fill:#ffeaea,stroke:#ef4444,color:#7f1d1d;

    TM[TaskExecutor.md] --> TS[TaskStage.md] --> TG[TaskGraph.md]
    TM --> TP[TaskProgress.md]
    TM --> TME[TaskMetrics.md]

    TG --> TQ[TaskQueue.md]
    TG --> TN[TaskStages.md]
    TG --> TR[TaskReport.md]
    TG --> TSR[TaskStructure.md]

    TR --> TW[TaskWeb.md]
    TN --> GW[Go Worker.md]

    class TM,TS,TG core;
    class TP,TME runtime;
    class TSR structure;
    class TQ,TN,GW execution;
    class TR,TW web;
```

以下の 3 編は補足読書として参照できます：

- [runtime/util_hash.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/runtime/util_hash.md)
- [runtime/util_types.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/runtime/util_types.md)
- [runtime/util_errors.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/runtime/util_errors.md)
- [persistence/core_fail.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/persistence/core_fail.md)
- [persistence/core_log.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/persistence/core_log.md)

完全なケースを通じてフレームワークの動作方法を理解したい場合は、TaskGraph を使用してゼロからプロジェクトを構築するこのチュートリアルを参照してください：

[📘 ケースチュートリアル](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/tutorial.md)

3.0.7 バージョンで追加された ctree_client とその機能に興味がある場合は、こちらをご覧ください：

[📚 CelestialTreeClient](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/other/ctree_client.md)

さらに多くのデモコードを実行できます。各デモファイルとその中のデモ関数の説明はこちらに記録されています：

[🎮 demo/](https://github.com/Mr-xiaotian/CelestialFlow/tree/main/docs/zh-CN/demo)

テストコードを実行したい場合は、まず以下のドキュメント内容を確認してください：

[🧪 tests/](https://github.com/Mr-xiaotian/CelestialFlow/tree/main/docs/zh-CN/tests)

bench の内容を確認したい場合、ここのデータはフレームワークの一部設計上の意思決定の根拠となっています：

[⚡ bench/](https://github.com/Mr-xiaotian/CelestialFlow/tree/main/docs/zh-CN/bench)

## 環境要件（Requirements）

**CelestialFlow** は Python 3.12+ ベースで、以下のコアコンポーネントに依存します。
お使いの環境がこれらの依存関係を正常にインストールできることを確認してください（`pip install celestialflow` で自動インストールされます）。

| 依存パッケージ           | 説明 |
| ----------------- | ---- |
| **Python ≥ 3.12**  | 実行環境、3.12 以上を推奨 |
| **fastapi**       | Web サービスインターフェースフレームワーク（タスク可視化とリモート制御用） |
| **uvicorn**       | FastAPI の高性能 ASGI サーバー |
| **requests**      | HTTP クライアントライブラリ、タスク状態レポートとリモート呼び出し用 |
| **networkx**      | タスクグラフ（TaskGraph）構造と依存関係分析 |
| **jinja2**        | FastAPI テンプレートエンジン、Web 可視化インターフェースレンダリング用 |
| **tqdm**          | オプションコンポーネント、プログレスバー表示、タスク実行可視化用 |
| **redis**         | オプションコンポーネント、分散タスク通信（`TaskRedis*` シリーズモジュール）用 |
| **celestialtree** | オプションコンポーネント、タスク状態レポートとリモート呼び出し（`ctree_client`）用 |

## ファイル構造（File Structure）

<p align="center">
  <img src="https://raw.githubusercontent.com/Mr-xiaotian/CelestialFlow/main/img/file_structure.svg" alt="FileStructure" />
  <br/>
  <em>celestial-flow 3.2.2</em>
</p>

(このビューは私の別プロジェクト [CelestialVault](https://github.com/Mr-xiaotian/CelestialVault) の `inst_file.FileTree.print_tree()` によって生成されました。画像への変換は [Carbon](https://carbon.now.sh) を利用しています。)

## バージョンログ（Version Log）
- 3.2.2
  - feat:
    - `core_server` にデータロックを追加し、並行アクセスによるエラー状態を回避
    - フロントエンド設定パネルの表示を最適化し、現在はグローバル設定と現在のページ関連設定のみを表示
    - 設定パネルにグローバル設定の「自動更新」オプションとエラーログページの「ソート方法」の 2 項目を追加
  - refactor:
    - フロントエンド・バックエンド間通信の `summary` を削除し、ノードの全体予想終了時間は各ノードの `status` で個別に伝達され、フロントエンドで全体の予想終了時間を計算
    - `structure_graph`（旧 `structure_json`）フィールドの内容を変更し、より簡潔になり情報の冗長性を回避、同時に後続の拡張が容易に
  - fix:
    - 指標折れ線グラフで指標選択が無効になる問題を修正
    - `report.stop` 内の `_refresh_all` の実行順序を変更し、thread 内のリフレッシュとの競合を回避
    - `graph._finalize_nodes` に thread が未終了の場合の防御的チェックを追加
    - `stage` の `start_time` が定義される前に `report` によって呼び出される問題を修正
    - `TaskRedisTransport._transport` で `id()` を使用して task_id を計算することによる問題を修正
    - 一部のタスクが hash 化できず panic を引き起こす問題を修正
  - chore:
    - すべての `type: ignore` を削除
      - かなり見栄えが良くなりました
    - `start_*` 関数の doc-string にその関数が一回限りの呼び出し関数であることを明記

より多くの過去ログは以下をご覧ください：

[change_log.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/change_log.md)

## Star 履歴トレンド（Star History）

プロジェクトに興味があれば、star を歓迎します。質問や提案があれば、[Issues](https://github.com/Mr-xiaotian/CelestialFlow/issues) を提出するか、[Discussion](https://github.com/Mr-xiaotian/CelestialFlow/discussions) でお知らせください。

![Star History Chart](https://api.star-history.com/svg?repos=Mr-xiaotian/CelestialFlow&type=Date)

## ライセンス（License）
This project is licensed under the MIT License - see the [LICENSE](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/LICENSE) file for details.

## 作者（Author）
Author: Mr-xiaotian
Email: mingxiaomingtian@gmail.com
Project Link: [https://github.com/Mr-xiaotian/CelestialFlow](https://github.com/Mr-xiaotian/CelestialFlow)

