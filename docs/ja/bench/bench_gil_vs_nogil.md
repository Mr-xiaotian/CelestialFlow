# bench_gil_vs_nogil.py ベンチマーク説明

> 📅 最終更新日: 2026/06/18

## 目標

`CelestialFlow` を Python 3.14 標準版（GIL 有効）と free-threading 版（GIL 無効）で実行した場合の差異を比較します。以下の 2 つの能力に注目します：

- `TaskExecutor` がスレッドで CPU タスクを実行する際のスループット変化
- `TaskGraph` がスレッドパイプラインで全体を加速する効果

この benchmark は 1 つのプロセス内で自動的に 2 つの Python 環境を起動することはなく、**現在のインタープリター**のみをテストします。そのため、GIL 環境と No-GIL 環境でそれぞれ 1 回ずつ実行し、結果を手動で比較する必要があります。

## テスト内容

スクリプトファイル: `bench/bench_gil_vs_nogil.py`

| Workload | 説明 |
|------|------|
| `executor_cpu_serial` | `TaskExecutor` が CPU 集中タスクを直列実行 |
| `executor_cpu_thread` | `TaskExecutor` が CPU 集中タスクをスレッド実行 |
| `graph_cpu_pipeline_serial` | 3-stage `TaskGraph` による直列 CPU パイプライン |
| `graph_cpu_pipeline_thread` | 3-stage `TaskGraph` によるスレッド CPU パイプライン |
| `graph_io_pipeline_thread` | 3-stage `TaskGraph` によるスレッド I/O パイプライン |

### テスト負荷設計

- **CPU タスク**: 純粋な Python 整数ループとハッシュ風の混合演算を実行し、Python バイトコード実行のオーバーヘッドをできるだけ強く受けるように設計
- **I/O タスク**: `time.sleep()` でブロッキング待機をシミュレート
- **グラフ構造**: 3 つの stage からなる単純な直列パイプラインに固定し、グラフトポロジーの差異が結果に影響しないようにする
- **ログレベル**: 一律 `CRITICAL` を使用し、ログ出力が benchmark に与える影響を最小化
- **繰り返し回数**: デフォルトで各 workload を 3 回実行し、平均値 / 最小値 / 最大値を集計

## 主要設定

デフォルトパラメータは以下の通りです：

| パラメータ | デフォルト値 | 説明 |
|------|--------|------|
| `repeats` | `3` | 各 workload の繰り返し回数 |
| `workers` | `0` | 自動で `min(os.cpu_count(), 16)` を取得 |
| `cpu_tasks` | `128` | `TaskExecutor` の CPU テストタスク数 |
| `cpu_loops` | `120000` | 単一 CPU タスクのループ強度 |
| `pipeline_tasks` | `96` | `TaskGraph` パイプラインタスク数 |
| `pipeline_loops` | `60000` | パイプライン CPU タスクのループ強度 |
| `io_tasks` | `96` | I/O パイプラインタスク数 |
| `io_sleep_ms` | `10.0` | 各 I/O タスクの sleep 時間（ミリ秒） |

## 実行方法

スクリプトは現在のインタープリターのみをテストするため、2 つの Python 3.14 環境でそれぞれ実行してください。

### GIL 環境での実行

```bash
python bench/bench_gil_vs_nogil.py --json-out bench_gil_result.json
```

### No-GIL 環境での実行

```bash
python bench/bench_gil_vs_nogil.py --json-out bench_nogil_result.json
```

ローカルで例のように 2 つの `uv` 仮想環境を管理している場合、明示的に呼び出すこともできます：

```powershell
.\gil\.venv\Scripts\python.exe .\bench\bench_gil_vs_nogil.py --json-out .\bench_gil_result.json
.\no-gil\.venv\Scripts\python.exe .\bench\bench_gil_vs_nogil.py --json-out .\bench_nogil_result.json
```

## パラメータ調整

### worker 数の調整

```bash
python bench/bench_gil_vs_nogil.py --workers 8
```

### タスク規模を縮小してクイック検証

```bash
python bench/bench_gil_vs_nogil.py \
  --repeats 1 \
  --workers 4 \
  --cpu-tasks 16 \
  --cpu-loops 20000 \
  --pipeline-tasks 12 \
  --pipeline-loops 10000 \
  --io-tasks 12 \
  --io-sleep-ms 2
```

### CPU 負荷を増大

```bash
python bench/bench_gil_vs_nogil.py --cpu-loops 200000 --pipeline-loops 100000
```

## 発生しうる問題

1. **必ず 2 回に分けて実行すること**: スクリプトは Python 環境を自動で切り替えません。結果を比較する際は 2 つの出力を自分で収集する必要があります。
2. **初回実行時に fallback sqlite に書き込まれる**: `TaskExecutor` / `TaskGraph` は実行時に `fallback/` ディレクトリを作成するため、スクリプトはまず作業ディレクトリをリポジトリのルートに切り替え、一時パスや権限制限を回避します。
3. **異なるパラメータの結果を混在させないこと**: GIL と No-GIL の 2 回の実行でパラメータが異なる場合、結果に比較可能性がありません。
4. **CPU 周波数の変動が結果に影響する可能性**: Windows ではバックグラウンド負荷、温度制御、電源ポリシーによって単発の結果がばらつくため、デフォルトで 3 回繰り返し平均を取ります。

## ベンチマーク結果（実測）

### 2026/06/18 - Windows 11 / Python 3.14.3 / 8 workers

> 今回使用したパラメータ:
> `repeats=3, workers=8, cpu_tasks=96, cpu_loops=100000, pipeline_tasks=72, pipeline_loops=50000, io_tasks=72, io_sleep_ms=10`

| Workload | GIL 平均 | No-GIL 平均 | No-GIL 相対性能 |
|------|-----------|--------------|------------------|
| `executor_cpu_serial` | 1.1148s | 1.0836s | **1.03x** |
| `executor_cpu_thread` | 1.1191s | 0.2131s | **5.25x** |
| `graph_cpu_pipeline_serial` | 1.3526s | 1.2443s | **1.09x** |
| `graph_cpu_pipeline_thread` | 1.4777s | 0.1957s | **7.55x** |
| `graph_io_pipeline_thread` | 0.1514s | 0.1322s | **1.15x** |

ここで：

```text
No-GIL 相対性能 = GIL 平均所要時間 / No-GIL 平均所要時間
```

値が `1.00x` より大きい場合、No-GIL の方が高速であることを示します。

### 結果の解釈

- **直列 CPU モードでは差が小さい**: `executor_cpu_serial` と `graph_cpu_pipeline_serial` では約 `3% ~ 9%` の改善にとどまり、No-GIL がシングルスレッドの純粋な Python 実行を魔法のように加速するわけではないことを示しています。
- **スレッド CPU モードでは大幅に改善**: `executor_cpu_thread` は約 **5.25x**、`graph_cpu_pipeline_thread` は約 **7.55x** に達しました。
- **グラフレベルのスレッドパイプラインの方が改善が大きい**: 単一 executor のスレッドモードと比較して、`TaskGraph` のスレッドパイプラインは free-threading がもたらす並列能力をより十分に活用しています。
- **I/O モードにも改善はあるが主役ではない**: `graph_io_pipeline_thread` は約 **15%** の差にとどまり、I/O 待機は本来 GIL 下でも十分に並行実行できるという直感に合致します。

## 適用シーン

この benchmark は以下の質問に答えるのに適しています：

- `CelestialFlow` を Python 3.14 No-GIL 環境にデプロイした場合、スレッドモードはどの程度向上するか？
- `TaskExecutor` と `TaskGraph` のどちらの層が No-GIL からより大きな恩恵を受けるか？
- 現在のワークロードは CPU スレッド型と I/O 型のどちらに近いか？

もし目標が以下であれば：

- **async / thread / serial の 3 つの実行モードを比較したい**: まず `bench_execution_mode.py` を参照
- **異なる graph mode / DAG トポロジーの組み合わせを比較したい**: まず `bench_graph_mode.py` を参照
- **Python インタープリターの GIL と No-GIL の差異を専門に比較したい**: このファイルを使用

## 依存

- `celestialflow`
- Python 3.14 標準版（GIL）
- Python 3.14 free-threading 版（No-GIL）
