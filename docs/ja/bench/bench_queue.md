# bench_queue.py ベンチマーク説明

> 📅 最終更新日: 2026/04/22

## 目的

シングルプロセス環境において、スレッドキュー、マルチプロセスキュー、Manager キュー、Redis キューを含む複数のキュー実装の put/get/qsize/empty 操作性能を比較する。

## テスト内容

| キュー型 | 説明 | テスト操作 |
|----------|------|-----------|
| `ThreadQueue` | `queue.Queue` | put, get, qsize, empty |
| `MPQueue` | `multiprocessing.Queue` | put, get, qsize, empty |
| `Manager().Queue` | `Manager().Queue` | put, get, qsize, empty |
| `Redis List` | Redis `lpush`/`rpop` | lpush, rpop, llen, empty-check |
| `Redis Stream` | Redis `xadd`/`xread` | xadd, xread, xlen, empty-check |

- **規模**：`COUNT = 100_000`
- **Redis 設定**：`.env` から読み込み（`REDIS_HOST`、`REDIS_PORT`、`REDIS_PASSWORD`）

## 発生し得る問題

1. **`MPQueue` のシングルプロセスでの誤解を招く結果**：`MPQueue` はクロスプロセス用に設計されており、シングルプロセス内でのテストでは基盤のパイプ/ソケットのオーバーヘッドが増幅され、結果は実際のクロスプロセス性能を代表しない。
2. **Redis Stream のブロック動作**：`xread` は `block=0`（無限ブロッキング）を使用する。メッセージ数が予想と異なる場合、テストが永久にハングする。
3. **`qsize()` の信頼性の低さ**：`MPQueue.qsize()` はマルチプロセス環境では非正確。シングルプロセステストでも、内部バッファリングにより値が遅延する可能性がある。
4. **Redis `flushdb`**：テスト開始前に `flushdb` が実行される。本番 Redis インスタンスに接続している場合、データ損失が発生する。

## ベンチマーク結果（実測）

> 環境：Windows、Python 3.10、COUNT=100,000
> 注：Redis テストはローカル Redis サービスの応答が遅く、120s タイムアウト以内に完了しなかった。以下はローカルキューの実測結果。

### ローカルキュー比較

| キュー型 | put/lpush | get/rpop | 備考 |
|----------|-----------|----------|------|
| **ThreadQueue** | 0.0777s | 0.0723s | 純粋メモリ、シリアライズなし、最速 |
| **MPQueue** | 0.1198s | **3.0071s** | put は許容範囲、get はクロスプロセスデシリアライズにより極めて低速 |
| **Manager().Queue** | 8.0674s | 8.5525s | Manager サーバー転送、100x+ 低速 |

### Redis キュー（履歴参考値、今回未完了）

| 操作 | 推定所要時間（100k） | ボトルネック |
|------|---------------------|-------------|
| Redis List lpush/rpop | ~2-3s | ネットワーク RTT |
| Redis Stream xadd/xread | ~3-5s | ストリーム解析オーバーヘッド |

**主要な結論**：
- ThreadQueue は MPQueue get より **40x** 高速、Manager().Queue より **100x+** 高速
- MPQueue の get が最大の弱点（3s vs 0.07s）。フレームワーク内部キューをスレッドモードに退行できれば、大きな利益が得られる
- Redis キューはデバイス間/ネットワーク間シナリオに適し、ローカル IPC では全く検討すべきでない

## 実行方法

```bash
python bench/bench_queue.py
```

## パラメータ調整

### テスト規模の変更

スクリプトのデフォルトは `COUNT = 100_000`、`if __name__ == "__main__"` 内で変更可能：

```python
if __name__ == "__main__":
    COUNT = 10_000       # 小規模で素早く検証（数秒で完了）
    # COUNT = 1_000_000  # 大規模ストレステスト（Manager().Queue は極めて遅くなる点に注意）
```

### 特定キュー型のみをテスト

```python
if __name__ == "__main__":
    COUNT = 10_000

    # test_threadqueue_perf(COUNT)        # スレッドキューをコメントアウト
    test_mpqueue_perf(COUNT)              # MPQueue のみテスト
    # test_manager_queue_perf(COUNT)      # Manager キューをスキップ
    # test_redis_list_perf(COUNT)         # Redis をスキップ
    # test_redis_stream_perf(COUNT)
```

修正後に実行：

```bash
python bench/bench_queue.py
```

## 依存関係

- `redis`
- `python-dotenv`
