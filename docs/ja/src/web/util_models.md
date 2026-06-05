# util_models

> 📅 最終更新日: 2026/06/05

## 目的

`celestialflow.web.util_models` モジュールは、データ検証、シリアル化、API リクエスト/レスポンスの型制約に使用される Web モジュールの全 Pydantic データモデルを定義します。

## モデル一覧

### StructureModel

タスク構造データモデル。タスクグラフの構造情報を表現します。

| フィールド | 型 | 説明 |
|------|------|------|
| `structure` | `dict[str, Any]` | 構造スナップショット辞書。通常 `nodes`、`edges`、`source_nodes` を含みます |

### StatusModel

ノード状態データモデル。各ノードの実行状態を表現します。

| フィールド | 型 | 説明 |
|------|------|------|
| `timestamp` | `float` | 状態データのタイムスタンプ（Unix） |
| `status` | `dict[str, dict[str, Any]]` | ノード名から状態辞書へのマッピング |

### ErrorsMetaModel

エラーメタデータモデル。エラーログファイルのメタ情報を表現します。

| フィールド | 型 | 説明 |
|------|------|------|
| `jsonl_path` | `str` | エラーログ JSONL ファイルパス |
| `rev` | `int` | エラーログの現在のリビジョン/オフセット |

### ErrorsContentModel

エラーコンテンツデータモデル。完全なエラーレコードリストを含みます。

| フィールド | 型 | 説明 |
|------|------|------|
| `errors` | `list[dict[str, Any]]` | エラーレコードのリスト。各項目はエラー辞書 |
| `jsonl_path` | `str` | エラーログ JSONL ファイルパス |
| `rev` | `int` | エラーログの現在のリビジョン/オフセット |

### AnalysisModel

タスク分析データモデル。

| フィールド | 型 | 説明 |
|------|------|------|
| `analysis` | `dict[str, Any]` | 分析結果辞書 |

### TaskInjectionModel

タスク注入リクエストモデル。実行中のタスクグラフに新しいタスクを動的に挿入するために使用します。

| フィールド | 型 | 説明 |
|------|------|------|
| `node` | `str` | 注入ターゲットノード名 |
| `task_datas` | `list[Any]` | 注入するタスクデータのリスト。バックエンドは配列であることを要求します |
| `timestamp` | `datetime` | 注入リクエスト時刻 |

### DashboardConfigModel

ダッシュボードレイアウト設定モデル。フロントエンドパネルのカードレイアウトを定義します。

| フィールド | 型 | 説明 |
|------|------|------|
| `left` | `list[str]` | 左パネルに表示するカードタイプのリスト |
| `middle` | `list[str]` | 中央パネルに表示するカードタイプのリスト |
| `right` | `list[str]` | 右パネルに表示するカードタイプのリスト |

### WebConfigModel

Web UI グローバル設定モデル。

| フィールド | 型 | デフォルト | 説明 |
|------|------|--------|------|
| `theme` | `str` | — | UI テーマ |
| `autoRefreshEnabled` | `bool` | `True` | 自動リフレッシュを有効にするか |
| `refreshInterval` | `int` | — | ページデータリフレッシュ間隔（ms） |
| `historyLimit` | `int` | — | 履歴レコード数上限 |
| `language` | `str` | `"zh-CN"` | インターフェース言語 |
| `errorPageSize` | `int` | `10` | エラーページの1ページあたりの件数 |
| `errorSortOrder` | `str` | `"newest"` | エラーページのソート方式 |
| `showStructureEdgeDelta` | `bool` | `True` | 構造図エッジのデルタを表示するか |
| `dashboard` | `DashboardConfigModel` | — | ダッシュボードレイアウト設定（ネストモデル） |

## 使用例

### データ検証とシリアル化

```python
from celestialflow.web.util_models import WebConfigModel, DashboardConfigModel, TaskInjectionModel

# --- WebConfigModel の使用 ---
config = WebConfigModel(
    theme="dark",
    autoRefreshEnabled=True,
    refreshInterval=5,
    historyLimit=20,
    language="zh-CN",
    errorPageSize=10,
    errorSortOrder="newest",
    showStructureEdgeDelta=True,
    dashboard=DashboardConfigModel(
        left=["mermaid"],
        middle=["status"],
        right=["progress"],
    ),
)
print(f"テーマ: {config.theme}")
print(f"ダッシュボードレイアウト: {config.dashboard.model_dump()}")

# 辞書にシリアル化
config_dict = config.model_dump()

# 辞書から作成
restored = WebConfigModel(**config_dict)

# --- TaskInjectionModel の使用 ---
from datetime import datetime

injection = TaskInjectionModel(
    node="StageA",
    task_datas=[{"id": 1, "value": 42}, {"id": 2, "value": 99}],
    timestamp=datetime.now(),
)
print(f"注入ターゲット: {injection.node}, タスク数: {len(injection.task_datas)}")
```

> 注意：`TaskInjectionModel.task_datas` は現在厳格に `list[Any]` です。フロントエンドが単一のオブジェクト、文字列、数値をアップロードする場合は、事前に配列でラップしてください。さもなければインターフェースは 422 を返します。

### エラーデータ処理

```python
from celestialflow.web.util_models import ErrorsContentModel, ErrorsMetaModel

# エラーメタデータ
meta = ErrorsMetaModel(jsonl_path="./fallback/2026-05-28/errors.jsonl", rev=150)
print(f"エラーログパス: {meta.jsonl_path}, 現在のオフセット: {meta.rev}")

# エラーコンテンツ
errors = ErrorsContentModel(
    errors=[
        {"error_type": "ValueError", "error_message": "Invalid input"},
        {"error_type": "TimeoutError", "error_message": "Connection lost"},
    ],
    jsonl_path="./fallback/2026-05-28/errors.jsonl",
    rev=152,
)
print(f"エラー件数: {len(errors.errors)}")
```
