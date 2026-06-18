# bench_ipc_queue.py ベンチマーク説明

> 📅 最終更新日: 2026/06/16

## 目的

実際のクロスプロセスシナリオにおいて、複数の Python IPC（プロセス間通信）メカニズム（MPQueue、SimpleQueue、Pipe、Manager().Queue）の性能を比較する。CelestialFlow のマルチプロセスモードにおけるキュー選定にデータを提供する。

## テスト内容

| メカニズム | 説明 | トポロジ対応 |
|------------|------|-------------|
| `MPQueue` | 標準マルチプロセスキュー | SPSC |
| `SimpleQueue` | ロックフリー簡略化キュー | SPSC |
| `Pipe` | 双方向/単方向パイプ | SPSC |
| `Manager().Queue` | Manager サーバーベースのキュー | SPSC |

- **規模**：`COUNT = 100_000`、`REPEAT = 3`
- **負荷モード**：`int`（8 バイト）、`small`（~16 バイト）、`medium`（~144 バイト）、`large`（~4104 バイト）
- **検証**：チェックサムによるデータ整合性確認（欠落・破損なし）

## 主要実装

- `producer_queue` / `consumer_queue`：センチネルオブジェクト `_SENTINEL = None` でストリーム終了を識別
- `producer_pipe` / `consumer_pipe`：明示的な `conn.close()` でハンドルリークを防止
- `expected_checksum`：負荷モードに基づき期待されるチェックサムを解析計算

## 発生し得る問題

1. **Pipe ハンドルリーク**：consumer/producer が接続を正しく閉じない場合、Windows では子プロセスの終了不能やハンドル枯渇を引き起こす可能性がある。
2. **`Manager().Queue` のサーバーボトルネック**：全データが Manager サーバープロセスを経由して転送される必要があり、生産者/消費者が高並行の場合、サーバープロセスが単一障害点になる。
3. **大規模負荷のメモリコピー**：`large` モードでは各ペイロードが約 4KB、100k 回の転送で約 400MB のデータコピーが発生し、キュー自体よりもメモリ帯域幅が主要な測定対象となる。
4. **Windows `spawn` シリアライズオーバーヘッド**：全ペイロードが pickle を通じて親子プロセス間で転送される必要があり、大規模オブジェクトのシリアライズ/デシリアライズ時間が支配的になる。

## ベンチマーク結果（実測）

### 履歴結果 - Windows spawn int 負荷（日時未記録）

> 環境：Windows、Python 3.10、spawn モード、COUNT=100,000、REPEAT=3、負荷=int（8 バイト）

| メカニズム | 平均所要時間 | スループット | MPQueue 比 |
|------|----------|--------|-------------|
| **MPQueue** | 1.328s | 75,277 items/s | 1.00x |
| **SimpleQueue** | 1.099s | 90,962 items/s | 1.21x |
| **Pipe** | 1.006s | 99,358 items/s | 1.32x |
| **Manager().Queue** | 7.884s | 12,684 items/s | 0.17x |

**主要な結論**：
- **Pipe が最速**：MPQueue より 32% 高速、かつキュー抽象レイヤー不要
- **SimpleQueue が次点**：ロックフリー実装、MPQueue より 21% 高速、ただし単一生産者単一消費者のみ対応
- **Manager().Queue が最遅**：MPQueue の 17% のスループットのみ、Manager サーバープロセスが絶対的ボトルネック
- CelestialFlow のマルチプロセスキュー選定において、Pipe と SimpleQueue は高スループットシナリオの最適解（トポロジが許容する場合）

### 2026/06/16 - Windows spawn int 負荷再テスト

> 環境：Windows、COUNT=100,000、REPEAT=3、`PAYLOAD_MODE=int`

| メカニズム | 平均所要時間 | スループット | MPQueue 比 |
|------|----------|--------|-------------|
| **MPQueue** | 0.8434s | 118,563 items/s | 1.00x |
| **SimpleQueue** | 0.8417s | 118,806 items/s | 1.00x |
| **Pipe** | 0.7699s | 129,881 items/s | 1.09x |
| **Manager().Queue** | 4.5027s | 22,209 items/s | 0.19x |

**今回の補足結論**：
- `Pipe` は引き続き現在のマシンで最速の方式だが、`MPQueue` / `SimpleQueue` との差は約 **9%** に縮小
- `SimpleQueue` と `MPQueue` は今回ほぼ同等で、`int` 負荷では両者のオーバーヘッドがすでに非常に低いことを示している
- `Manager().Queue` は引き続き顕著に遅く、スループットは最速方式の約 6 分の 1

## 実行方法

```bash
python bench/bench_ipc_queue.py
```

## パラメータ調整

### テスト規模と負荷モードの変更

`bench/bench_ipc_queue.py` の先頭でグローバル設定を調整：

```python
COUNT = 10_000       # 回数を減らして素早く検証
# COUNT = 1_000_000  # 大規模ストレステスト

REPEAT = 1           # 1 ラウンドのみ、素早く検証
# REPEAT = 5         # ラウンドを増やし統計的信頼性を向上

PAYLOAD_MODE = "small"  # 選択肢：int / small / medium / large
```

### 特定 IPC メカニズムのみをテスト

`main()` 内で選択的に実行：

```python
def main() -> None:
    # run_queue_case(name="MPQueue", ...)   # MPQueue をコメントアウト
    # run_queue_case(name="SimpleQueue", ...)
    run_pipe_case(...)                        # Pipe のみテスト
    # run_manager_queue_case(...)
```

修正後に実行：

```bash
python bench/bench_ipc_queue.py
```

## 依存関係

- `bench_utils.summarize`
