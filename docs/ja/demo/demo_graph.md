# demo_graph.py デモ説明

> 📅 最終更新日: 2026/05/15

## 目的

CelestialFlow における `TaskGraph` の高度なグラフトポロジー構築をデモンストレーションします：ファンアウト/ファンイン（fan-out/fan-in）ETL パイプライン、および非同期段階的パイプライン。

## デモシナリオ

### `demo_etl_fan_out_fan_in`
ETL パイプライン、ファンアウト/ファンイントポロジー：

```
Extract ──┬── Normalize ──┬── Load
          └── Enrich ─────┘
```

- `Extract` → ID に基づいてレコードを生成（thread モード、4 worker）
- `Normalize` → レコード値を正規化（thread モード、4 worker）
- `Enrich` → レコードにカテゴリラベルを追加（thread モード、4 worker）
- `Load` → レコードを保存（serial モード）

**グラフ構造**: DAG、一対多ファンアウト + 多対一ファンイン
**スケジューリングモード**: `eager`
**実行後**: `graph.get_graph_summary()` を呼び出して成功/失敗タスク数を出力

### `demo_async_staged_pipeline`
2段階非同期パイプライン：

```
AsyncDouble ──> AsyncToStr
```

- `AsyncDouble` → 入力を非同期で2倍にする（async モード、8 worker）
- `AsyncToStr` → 結果を非同期で文字列に変換（async モード、8 worker）

**グラフ構造**: DAG、線形2段階
**スケジューリングモード**: `staged`（レイヤーごとの実行）
**実行後**: `graph.get_status_dict()` を呼び出して各ステージの成功/失敗タスク数を出力

## 主要設定

- すべての stage は `stage_mode="thread"` を使用
- ETL パイプラインは `schedule_mode="eager"`、非同期パイプラインは `schedule_mode="staged"` を使用
- `execution_mode="async"` はコルーチンタスク関数に使用

## 起こりうる問題

1. **アサーションなし**: デモスクリプトであり、結果の正確性は検証しません。
2. **ETL 関数に sleep を含む**: `extract_record`（0.5秒）、`transform_normalize`/`transform_enrich`（0.3秒）、`load_record`（0.2秒）、完全な実行には一定の時間がかかります。

## 実行方法

```bash
python demo/demo_graph.py
```

## 依存関係

- `celestialflow`（`TaskGraph`、`TaskStage`）
- `demo_utils`（`extract_record`、`transform_normalize`、`transform_enrich`、`load_record`、`async_double`、`async_to_str`）
- `python-dotenv`
- 外部サービス: CelestialTree（オプション）、Reporter（オプション）
