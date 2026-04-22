# demo_utils.py ユーティリティ説明

## 目的

`demo/` ディレクトリ配下のデモスクリプトに共有テスト関数とヘルパークラスを提供します。`tests/test_utils.py` と内容がほぼ同一であり、デモコード専用のユーティリティライブラリとして機能します。

## 内容分類

### 汎用計算関数
- `fibonacci` / `fibonacci_async`：再帰フィボナッチ（例外境界あり）
- `no_op` / `sum_int` / `add_one` / `sqrt`：基本的な算術演算
- `square` / `add_offset` / `add_5` / `add_10` など：1秒のスリープを含む模擬時間のかかるタスク
- `neuron_activation`：Sigmoid 活性化関数（ML 推論のシミュレーション）

### スリープバリアント
- `sleep_1` / `sleep_1_async`：純粋な1秒の遅延

### スリープ付き演算（demo_structure 用）
- `operate_sleep` / `operate_sleep_A~E`：1秒の遅延付き二項演算
- `add_one_sleep`：複数条件の例外境界を含む（`n>30`、`n==0`、`n is None`）

### URL 処理関数（demo_stages 用）
- `generate_urls_sleep` / `log_urls_sleep` / `download_sleep` / `parse_sleep`
- `download_to_file`：ローカルファイルへの実際の HTTP ダウンロード

### 特殊クラス
- `RouterWrapper`：`TaskRouter` デモ用のルーティングラッパー

## tests/test_utils.py との関係

2つのファイルの内容はほぼ同一です。これはデモコードがテストコードから分離された際にコピーが保持された歴史的経緯によるものと考えられます。メンテナンス時には両者を同期させるか、共通ユーティリティを `celestialflow/utils/` 配下の独立モジュールに抽出することを推奨します。

## 発生しうる問題

1. **tests/test_utils.py との重複**：一方のファイルを修正してもう一方を更新しないと、デモと単体テストの動作が乖離する可能性があります。
2. **ハードコードされた Windows パス**：`download_to_file` は `/tmp/` パスを `X:/Download/...` に置換しており、非 Windows 環境では失敗します。
3. **`requests` のネットワーク依存**：`download_to_file` は外部ネットワークアクセスが必要であり、隔離されたネットワーク環境では使用できません。

## 実行方法

これは共有モジュールであり、直接実行するものではありません：
```python
from demo_utils import fibonacci, sleep_1, RouterWrapper
```

## 依存関係

- `requests`
