# bench_persistence_spout.py ベンチマーク説明

> 📅 最終更新日: 2026/06/17

## 目標

永続化関連の `spout` が「キューに大量のレコードを事前投入し、バックグラウンド消費と書き込みのみを測定する」シナリオにおけるスループット上限を評価します。

本スクリプトは現在 2 種類のターゲットをカバーしています：

- `LogSpout`
- `FallbackSpout`

ここで：

- `LogSpout` はシングルスレッドでのログファイル書き込みによるキュー消化速度を測定します
- `FallbackSpout` は「各有効変更後に直接 `commit()`」モードでの SQLite fallback のトランザクションスループットを測定します

## テスト内容

| テスト項目 | 説明 | 計測範囲 |
|--------|------|----------|
| `LogSpout` | ログレコードを事前生成してキューに投入し、その後 `spout` を起動してキューを消化 | `start()` から `stop()` まで |
| `FallbackSpout` | `insert` レコードを事前生成してキューに投入し、その後 `spout` を起動してキューを消化 | `start()` から `stop()` まで |

スクリプトが採用するモデルは：

```text
preload queue -> start spout -> drain all queued records
```

したがって、テスト結果は「バックグラウンド書き込み側の限界処理速度」により近く、呼び出し側がリアルタイムでデータを生成するコストは含まれません。

## 主要設定

- `--log-count`: デフォルト `200_000`
- `--fallback-count`: デフォルト `20_000`
- `LogSpout` は一時ディレクトリ下の `bench_task_logger.log` に出力
- `FallbackSpout` は一時ディレクトリ下の `bench_fallback.sqlite3` に出力
- `FallbackSpout` は現在のプロジェクト実装、すなわち「各有効変更後に直接 `commit()`」を使用

## 発生しうる問題

1. **`LogSpout` の結果は実際のハードディスク強制フラッシュ頻度とは等しくない**: 現在のテストでは各レコードに対して明示的な `flush()` や `fsync()` を実行しておらず、測定結果はファイルバッファとページキャッシュの書き込み速度により近くなります。
2. **`FallbackSpout` のボトルネックは主にトランザクションコミットにある**: 今回の結果は、現在のディスクとトランザクションモードにおける SQLite の `commit()` スループットを大きく反映しており、Python のループオーバーヘッドだけではありません。
3. **起動・停止コストが少量サンプルの結果に影響を与える**: レコード数が少なすぎる場合、スレッド起動、停止シグナル、最終 `commit()` の固定コストが増幅されます。
4. **大規模サンプルでは不安定現象が発生する可能性がある**: ローカルでより大規模なサンプル `--log-count 500000 --fallback-count 50000` を試したところ、`LogSpout` は正常に完了しましたが、`FallbackSpout` フェーズでインタープリタークラッシュが 1 回発生しました。そのため、この規模はストレス探索値と見なし、安定したベースラインとはしないことを推奨します。

## ベンチマーク結果（実測）

### 2026/06/17 - Windows ローカル初回実測

> 環境: Windows, ローカル `.venv`, モデルは「キュー事前投入後に spout 起動で消化」, `log-count=200000`, `fallback-count=20000`

| テスト項目 | レコード数 | 総所要時間 | スループット | 1 件あたり平均所要時間 |
|--------|--------|--------|------|--------------|
| `LogSpout` | 200,000 | 0.2036s | 982,287.88 records/s | 1.02 us |
| `FallbackSpout` | 20,000 | 3.2515s | 6,151.08 records/s | 162.57 us |

**今回の結論**:

- `LogSpout` は毎秒約 100 万件に迫り、現在の実装ではログ書き込みのボトルネックは主に Python 側にはないことを示しています
- `FallbackSpout` は毎秒約 6.1k 件で、SQLite の単一トランザクションコミット制限が明らかに影響しています
- 両者のスループット差は約 **160x**

### 2026/06/17 - Windows ローカル再テスト（中程度拡大サンプル）

> 環境: Windows, ローカル `.venv`, モデル同上, `log-count=300000`, `fallback-count=30000`

| テスト項目 | レコード数 | 総所要時間 | スループット | 1 件あたり平均所要時間 |
|--------|--------|--------|------|--------------|
| `LogSpout` | 300,000 | 0.2960s | 1,013,446.75 records/s | 0.99 us |
| `FallbackSpout` | 30,000 | 4.6633s | 6,433.23 records/s | 155.44 us |

**今回の補足結論**:

- `LogSpout` はサンプル拡大後も約 **100 万件/秒** で安定
- `FallbackSpout` はサンプル拡大後も約 **6.4k 件/秒** で安定
- 現在のマシンと実装において、`log` はボトルネックではなく、`fallback/sqlite` が主要な制限項目です

## 実行方法

```bash
python bench/bench_persistence_spout.py
```

プロジェクトがインポート可能なパッケージとしてインストールされていない場合、ローカル仮想環境のインタープリターを直接使用することもできます：

```bash
.\.venv\Scripts\python.exe bench/bench_persistence_spout.py
```

## パラメータ調整

### ログサンプル数の調整

```bash
python bench/bench_persistence_spout.py --log-count 500000
```

### fallback サンプル数の調整

```bash
python bench/bench_persistence_spout.py --fallback-count 50000
```

### 両方のサンプルを同時に調整

```bash
python bench/bench_persistence_spout.py --log-count 300000 --fallback-count 30000
```

## 依存

- Python 標準ライブラリ
- プロジェクトソースコード内の `celestialflow.persistence`
