# demo_utils.py ユーティリティ説明

> 📅 最終更新日: 2026/05/15

## 目的

`demo/` ディレクトリ下のデモスクリプト用に、共有テスト関数とヘルパークラスを提供します。`tests/test_utils.py` と内容がほぼ同一であり、デモコード専用のユーティリティライブラリです。

## 内容分類

### 汎用計算関数
- `fibonacci` / `fibonacci_async`: 再帰フィボナッチ（例外境界付き）
- `no_op` / `sum_int` / `add_one` / `sqrt`: 基本演算
- `square` / `add_offset` / `add_5` / `add_10` / `add_15` / `add_20` / `add_25` など: 1秒 sleep 付きの模擬時間消費タスク
- `neuron_activation`: シグモイド活性化関数（ML 推論のシミュレーション）

### Sleep バリアント
- `sleep_1` / `sleep_1_async`: 純粋な1秒遅延

### Sleep 付き演算（demo_structure 用）
- `operate_sleep` / `operate_sleep_A~E`: 1秒遅延付き二項演算
- `add_one_sleep`: 多条件例外境界付き（`n>30`、`n==0`、`n is None`）

### URL 処理関数（demo_stages 用）
- `generate_urls_sleep` / `log_urls_sleep` / `download_sleep` / `parse_sleep`
- `download_to_file`: ローカルファイルへの実 HTTP ダウンロード

### ETL シミュレーション関数（demo_graph 用）
- `extract_record`: ID に基づいてレコード辞書を生成（0.5秒 sleep 付き）
- `transform_normalize`: レコード値を正規化（0.3秒 sleep 付き）
- `transform_enrich`: レコードに奇偶分類を追加（0.3秒 sleep 付き）
- `load_record`: レコード保存をシミュレーションし結果文字列を返す（0.2秒 sleep 付き）

### 非同期ヘルパー関数（demo_graph 用）
- `async_double`: 入力を非同期で2倍にする（0.3秒 sleep 付き）
- `async_to_str`: 入力を非同期でフォーマット文字列に変換（0.2秒 sleep 付き）

### 特殊クラス
- `RouterWrapper`: `TaskRouter` デモ用のルーティングラッパー

## tests/test_utils.py との関係

2つのファイルの内容はほぼ完全に同一です。これはデモコードがテストコードから分離された際にコピーが保持された歴史的な経緯によるものと考えられます。メンテナンス時は両方を同期させるか、共通ユーティリティを `celestialflow/utils/` 下の独立モジュールに抽出することを検討してください。

## 起こりうる問題

1. **tests/test_utils.py との重複**: 一方を修正する際にもう一方を忘れると、デモとユニットテストの動作が分岐する可能性があります。
2. **ハードコードされた Windows パス**: パス置換ロジックは `demo_stages.py` 内の `DownloadStage` および `DownloadRedisTransport` カスタムサブクラスに存在し、本ファイルにはありません。
3. **`requests` ネットワーク依存**: `download_to_file` は外部ネットワークアクセスが必要であり、隔離されたネットワーク環境では利用できません。

## 実行方法

このファイルは共有モジュールであり、直接実行しません：
```python
from demo_utils import fibonacci, sleep_1, RouterWrapper
```

## 依存関係

- `requests`
