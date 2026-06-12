# util_models

> 📅 最終更新日: 2026/06/11

## 役割

`celestialflow.web.util_models` モジュールは Web モジュールで使用される全ての Pydantic データモデルを定義し、データ検証、シリアライズ、API リクエスト/レスポンスの型制約に使用します。

## モデル一覧

### StructureModel

タスク構造データモデル。タスクグラフの構造情報を表します。

| フィールド | 型 | 説明 |
|------|------|------|
| `structure` | `dict[str, Any]` | 構造スナップショット辞書。通常 `nodes`、`edges`、`source_nodes` を含む |

### StatusModel

ノード状態データモデル。各ノードの実行状態を表します。

| フィールド | 型 | 説明 |
|------|------|------|
| `timestamp` | `float` | 状態データのタイムスタンプ（Unix） |
| `status` | `dict[str, dict[str, Any]]` | ノード名から状態辞書へのマッピング |

### ErrorsMetaModel

エラーメタデータモデル。エラーログファイルのメタ情報を表します。

| フィールド | 型 | 説明 |
|------|------|------|
| `jsonl_path` | `str` | エラーログ JSONL ファイルパス |
| `rev` | `int` | エラーログの現在のリビジョン/オフセット |

### ErrorsContentModel

エラー内容データモデル。完全なエラー記録リストを含みます。

| フィールド | 型 | 説明 |
|------|------|------|
| `errors` | `list[dict[str, Any]]` | エラー記録リスト。各項目はエラー辞書 |
| `jsonl_path` | `str` | エラーログ JSONL ファイルパス |
| `rev` | `int` | エラーログの現在のリビジョン/オフセット |

### AnalysisModel

タスク分析データモデル。

| フィールド | 型 | 説明 |
|------|------|------|
| `analysis` | `dict[str, Any]` | 分析結果辞書 |

### TaskInjectionModel

タスク注入リクエストモデル。実行中のタスクグラフに新しいタスクを動的に挿入するために使用します。

> このモデルは `RootModel[dict[str, list[Any]]]` を継承し、リクエストボディは直接 `{ノード名: [タスクリスト]}` 形式の辞書です。`node`/`task_datas`/`timestamp` などの独立フィールドは含まれません。

| ルート値の型 | 説明 |
|----------|------|
| `dict[str, list[Any]]` | キーはノード名、値はそのノードに注入するタスクデータリスト |

**リクエストボディ例：**

```json
{
  "StageA": [{"id": 1, "value": 42}, {"id": 2, "value": 99}],
  "StageB": [{"id": 3, "value": 55}]
}
```

### DashboardConfigModel

ダッシュボードレイアウト設定モデル。フロントエンドパネルカードのレイアウトを定義します。

| フィールド | 型 | 説明 |
|------|------|------|
| `left` | `list[str]` | 左パネルに表示するカードタイプリスト |
| `middle` | `list[str]` | 中央パネルに表示するカードタイプリスト |
| `right` | `list[str]` | 右パネルに表示するカードタイプリスト |

### GlobalConfigModel

グローバル共有設定モデル（`WebConfigModel.global_` の下にネスト）。

| フィールド | 型 | デフォルト値 | 説明 |
|------|------|--------|------|
| `theme` | `str` | — | UI テーマ（`"light"`、`"dark"` など） |
| `autoRefreshEnabled` | `bool` | `True` | 自動更新を有効にするかどうか |
| `refreshInterval` | `int` | — | ページデータの更新間隔（ms） |
| `language` | `str` | `"zh-CN"` | インターフェース言語 |

### DashboardPageConfigModel

ダッシュボードページ設定モデル（`WebConfigModel.dashboard` の下にネスト）。

| フィールド | 型 | デフォルト値 | 説明 |
|------|------|--------|------|
| `historyLimit` | `int` | — | 履歴記録数の上限 |
| `showStructureEdgeDelta` | `bool` | `False` | 構造図の辺増分を表示するかどうか |
| `useTotalPendingInStatus` | `bool` | `False` | ノード待機パラメータにグローバル推定を使用するかどうか |
| `layout` | `DashboardConfigModel` | — | ダッシュボードカードの3カラムレイアウト定義 |

### ErrorsPageConfigModel

エラーページ設定モデル（`WebConfigModel.errors` の下にネスト）。

| フィールド | 型 | デフォルト値 | 説明 |
|------|------|--------|------|
| `pageSize` | `int` | `10` | エラーページの1ページあたりの件数 |
| `sortOrder` | `str` | `"newest"` | デフォルトのソート方式（`"newest"` / `"oldest"`） |
| `jumpToInjectionAfterRetry` | `bool` | `True` | タスクリトライ後に注入ページにジャンプするかどうか |

### InjectionPageConfigModel

注入ページ設定モデル（`WebConfigModel.injection` の下にネスト）。

| フィールド | 型 | デフォルト値 | 説明 |
|------|------|--------|------|
| `showInjectableOnly` | `bool` | `True` | 注入可能ノードのみを表示するかどうか |

### WebConfigModel

Web UI グローバル設定モデル（ネストグループ構造に変更済み）。

| フィールド | 型 | デフォルト値 | 説明 |
|------|------|--------|------|
| `global_` | `GlobalConfigModel` | — | グローバル共有設定（JSON エイリアス `"global"`） |
| `dashboard` | `DashboardPageConfigModel` | — | ダッシュボードページ設定 |
| `errors` | `ErrorsPageConfigModel` | — | エラーページ設定 |
| `injection` | `InjectionPageConfigModel` | `InjectionPageConfigModel()` | 注入ページ設定 |

> **変更済み**: `WebConfigModel` は旧バージョンのフラットフィールド（`theme`, `refreshInterval`, `historyLimit`...）からネストグループ構造に変更されました。元の `theme`、`refreshInterval` などのフィールドは `GlobalConfigModel`（エイリアス `"global"`）に移動し、`historyLimit`、`showStructureEdgeDelta` などは `DashboardPageConfigModel` に、`errorPageSize`、`errorSortOrder` などは `ErrorsPageConfigModel` に移動しました。

## 使用例

### データ検証とシリアライズ

```python
from celestialflow.web.util_models import (
    WebConfigModel, GlobalConfigModel, DashboardPageConfigModel,
    DashboardConfigModel, ErrorsPageConfigModel, InjectionPageConfigModel,
    TaskInjectionModel,
)

# --- WebConfigModel の使用（ネスト構造）---
config = WebConfigModel(
    global=GlobalConfigModel(
        theme="dark",
        autoRefreshEnabled=True,
        refreshInterval=5000,
        language="zh-CN",
    ),
    dashboard=DashboardPageConfigModel(
        historyLimit=20,
        showStructureEdgeDelta=False,
        useTotalPendingInStatus=False,
        layout=DashboardConfigModel(
            left=["mermaid"],
            middle=["status"],
            right=["progress"],
        ),
    ),
    errors=ErrorsPageConfigModel(
        pageSize=10,
        sortOrder="newest",
        jumpToInjectionAfterRetry=True,
    ),
    injection=InjectionPageConfigModel(
        showInjectableOnly=True,
    ),
)
print(f"テーマ: {config.global_.theme}")
print(f"ダッシュボードレイアウト: {config.dashboard.layout.model_dump()}")

# 辞書にシリアライズ（by_alias=True で global_ を "global" に変換）
config_dict = config.model_dump(by_alias=True)

# 辞書から作成
restored = WebConfigModel.model_validate(config_dict)

# --- TaskInjectionModel の使用 ---
injection = TaskInjectionModel(
    StageA=[{"id": 1, "value": 42}, {"id": 2, "value": 99}],
    StageB=[{"id": 3, "value": 55}],
)
print(f"注入ノード数: {len(injection.root)}")
for node_name, tasks in injection.root.items():
    print(f"  {node_name}: {len(tasks)} タスク")
```

> 注意：`TaskInjectionModel` は `RootModel[dict[str, list[Any]]]` であり、リクエストボディは直接ノード名からタスクリストへのマッピング辞書です。`node`/`task_datas` などのフィールドでラップされません。

### エラーデータ処理

```python
from celestialflow.web.util_models import ErrorsContentModel, ErrorsMetaModel

# エラーメタデータ
meta = ErrorsMetaModel(jsonl_path="./fallback/2026-05-28/errors.jsonl", rev=150)
print(f"エラーログパス: {meta.jsonl_path}, 現在のオフセット: {meta.rev}")

# エラー内容
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
