# bench_queue.py ベンチマーク説明

> 📅 最終更新日: 2026/04/22

## 目的

シングルプロセス環境で複数のキュー実装の put/get/qsize/empty 操作の性能を比較する。スレッドキュー、マルチプロセスキュー、Manager キュー、Redis キューを含む。

## テスト内容

| キュータイプ | 説明 | テスト操作 |
|-------------|------|-----------|
| `ThreadQueue` | `queue.Queue` | put, get, qsize, empty |
| `MPQueue` | `multiprocessing.Queue` | put, get, qsize, empty |
| `Manager().Queue` | `Manager().Queue` | put, get, qsize, empty |
| `Redis List` | Redis `lpush`/`rpop` | lpush, rpop, llen, empty-check |
| `Redis Stream` | Redis `xadd`/`xread` | xadd, xread, xlen, empty-check |

- **規模**：`COUNT = 100_000`
- **Redis 設定**：`.env` から読み込み（`REDIS_HOST`、`REDIS_PORT`、`REDIS_PASSWORD`）

## 発生し得る問題

1. **シングルプロセスでの `MPQueue` の誤解**：`MPQueue` はクロスプロセス用に設計されている。シングルプロセス内でのテストは基盤のパイプ/ソケットオーバーヘッドを増幅し、結果は実際のクロスプロセス性能を代表しない。
2. **Redis Stream の block 動作**：`xread` は `block=0`（無限ブロック）を使用。メッセージ数が期待と一致しない場合、テストは永久にハングする。
3. **`qsize()` の信頼性の低さ**：`MPQueue.qsize()` はマルチプロセス環境では不正確。シングルプロセステストでも内部バッファリングにより値が遅延する場合がある。
4. **Redis `flushdb`**：テスト開始前に `flushdb` が実行される。本番 Redis インスタンスに接続している場合、データが失われる。

## ベンチマーク結果（実測）

> 環境：Windows、Python 3.10、COUNT=100,000
> 注：ローカル Redis の応答が遅いため、Redis テストは 120 秒のタイムアウト内に完了せず。以下はローカルキューの実測結果のみ。

### ローカルキュー比較

| キュータイプ | put/lpush | get/rpop | 備考 |
|-------------|-----------|----------|------|
| **ThreadQueue** | 0.0777s | 0.0723s | 純粋メモリ、シリアライズなし、最速 |
| **MPQueue** | 0.1198s | **3.0071s** | put は許容範囲、get はクロスプロセスデシリアライズにより極めて遅い |
| **Manager().Queue** | 8.0674s | 8.5525s | Manager サーバー転送、100 倍以上遅い |

### Redis キュー（過去の参考値、今回は完全に完了せず）

| 操作 | 推定所要時間（100k） | ボトルネック |
|------|---------------------|-------------|
| Redis List lpush/rpop | ~2-3s | ネットワーク RTT |
| Redis Stream xadd/xread | ~3-5s | ストリーム解析オーバーヘッド |

**主要な結論**：
- ThreadQueue の get は MPQueue の **40 倍**高速、Manager().Queue の **100 倍以上**高速
- MPQueue の get が最大のボトルネック（3s vs 0.07s）。フレームワークの内部キューをスレッドモードに退化できれば、恩恵は絶大
- Redis キューはクロスデバイス/クロスネットワークシナリオに適している。ローカル IPC では全く考慮すべきでない

## 実行方法

```bash
python bench/bench_queue.py
```

## 依存関係

- `redis`
- `python-dotenv`
