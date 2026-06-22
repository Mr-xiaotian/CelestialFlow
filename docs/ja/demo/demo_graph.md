# demo_graph.py デモ説明

> 📅 最終更新日: 2026/06/22

## 目標

CelestialFlow における `TaskGraph` の高度なグラフトポロジー構築：ファンアウト/ファンイン（fan-out/fan-in）ETL パイプライン、および非同期ステージドパイプラインをデモする。

## デモシナリオ

### `demo_etl_fan_out_fan_in`
ETL パイプライン、ファンアウト/ファンイン トポロジー：

```mermaid
flowchart LR
    Extract["Extract<br/>thread | 4 workers"] --> Normalize["Normalize<br/>thread | 4 workers"]
    Extract --> Enrich["Enrich<br/>thread | 4 workers"]
    Normalize --> Load["Load<br/>serial"]
    Enrich --> Load
```

ASCII 補足図：

```
Extract ──┬── Normalize ──┬── Load
          └── Enrich ─────┘
```

- `Extract` → ID に基づいてレコードを生成（thread モード、4 worker）
- `Normalize` → レコード値を正規化（thread モード、4 worker）
- `Enrich` → レコードに分類ラベルを追加（thread モード、4 worker）
- `Load` → レコードを保存（serial モード）

**グラフ構造**：DAG、一対多ファンアウト + 多対一ファンイン  
**スケジュールモード**：`eager`

### `demo_async_staged_pipeline`
2 ステージ非同期パイプライン：

```mermaid
flowchart LR
    AsyncDouble["AsyncDouble<br/>async | 8 workers"] --> AsyncToStr["AsyncToStr<br/>async | 8 workers"]
```

ASCII 補足図：

```
AsyncDouble ──> AsyncToStr
```

- `AsyncDouble` → 入力を非同期で倍にする（async モード、8 worker）
- `AsyncToStr` → 結果を非同期で文字列に変換（async モード、8 worker）

**グラフ構造**：DAG、線形 2 ステージ  
**スケジュールモード**：`staged`（層ごとに実行）

## 主要設定

- すべての stage は `stage_mode="thread"` を使用
- ETL パイプラインは `schedule_mode="eager"`、非同期パイプラインは `schedule_mode="staged"` を使用
- `execution_mode="async"` はコルーチンタスク関数に使用

## 発生しうる問題

1. **アサーションなし**：デモスクリプトであり、結果の正確性は検証しない。
2. **ETL 関数に sleep を含む**：`extract_record`（0.5s）、`transform_normalize`/`transform_enrich`（0.3s）、`load_record`（0.2s）があり、完全な実行には一定の時間がかかる。

## 実行方法

```bash
python demo/demo_graph.py
```

## 想定される動作

### ETL パイプライン（`demo_etl_fan_out_fan_in`）

Extract → Normalize/Enrich → Load の順に実行され、出力には sleep ログと最終サマリーが含まれる：

```
[Extract] Input: 1 -> Output: {'id': 1, 'value': 10, 'label': 'item_1'}
[Extract] Input: 2 -> Output: {'id': 2, 'value': 20, 'label': 'item_2'}
[Normalize] Input: {'id': 1, 'value': 10} -> Output: {'id': 1, 'value': 10, 'normalized': 0.1}
[Enrich] Input: {'id': 1, 'value': 10} -> Output: {'id': 1, 'value': 10, 'category': 'odd'}
...
--- Graph Summary ---
Extract    : success=15 fail=0
Normalize  : success=15 fail=0
Enrich     : success=15 fail=0
Load       : success=30 fail=0
```

> 各 Extract は 1 件のレコードを生成し、Normalize と Enrich でそれぞれ処理された後、Load で集約される。入力が `range(1, 16)` の場合、Extract は 15 件のレコードを処理し、Normalize と Enrich はそれぞれ 15 件を受け取り、Load ノードは合計 30 件のタスク（15 × 2 下流）を受け取る。

### 非同期パイプライン（`demo_async_staged_pipeline`）

ステージごとに層ごとに実行され、AsyncDouble が完了してから AsyncToStr が開始される：

```
--- Staged 1: AsyncDouble ---
[AsyncDouble] Input: 1 -> Output: 2
[AsyncDouble] Input: 2 -> Output: 4
...
--- Staged 2: AsyncToStr ---
[AsyncToStr] Input: 2 -> Output: 'result=2'
[AsyncToStr] Input: 4 -> Output: 'result=4'
...
--- Status Snapshot ---
AsyncDouble : success=20 fail=0  pending=0
AsyncToStr  : success=20 fail=0  pending=0
```

> 総実行時間は約 3〜5 秒で、主に組み込みの `sleep` の影響を受ける。

## 依存

- `celestialflow`（`TaskGraph`、`TaskStage`）
- `demo_utils`（`extract_record`、`transform_normalize`、`transform_enrich`、`load_record`、`async_double`、`async_to_str`）
- `python-dotenv`
- 外部サービス：CelestialTree（オプション）、Reporter（オプション）
