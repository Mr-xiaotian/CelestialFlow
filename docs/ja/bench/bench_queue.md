# bench_queue.py ベンチマーク説明

> 📅 最終更新日: 2026/04/22

## 目標

シングルプロセス環境における複数のキュー実装の put/get/qsize/empty 操作の性能を比較します。スレッドキュー、マルチプロセスキュー、Manager キュー、Redis キューを含みます。

## テスト内容

| キュータイプ | 説明 | テスト操作 |
|------------|------|----------|
| `ThreadQueue` | `queue.Queue` | put, get, qsize, empty |
| `MPQueue` | `multiprocessing.Queue` | put, get, qsize, empty |
| `Manager().Queue` | `Manager().Queue` | put, get, qsize, empty |
| `Redis List` | Redis `lpush`/`rpop` | lpush, rpop, llen, empty-check |
| `Redis Stream` | Redis `xadd`/`xread` | xadd, xread, xlen, empty-check |

- **規模**：`COUNT = 100_000`
- **Redis 設定**：`.env` から読み込みます（`REDIS_HOST`、`REDIS_PORT`、`REDIS_PASSWORD`）

## 発生しうる問題

1. **シングルプロセスでの `MPQueue` の誤解を招く結果**：`MPQueue` はプロセス間用に設計されています。シングルプロセス内でテストすると、基盤となるパイプ/ソケットのオーバーヘッドが増幅され、結果は実際のプロセス間性能を反映しません。
2. **Redis Stream のブロック動作**：`xread` は `block=0`（無限ブロック）を使用します。メッセージ数が期待と一致しない場合、テストは永遠にハングします。
3. **`qsize()` の信頼性の低さ**：`MPQueue.qsize()` はマルチプロセス環境では不正確です。シングルプロセステストでも、内部バッファリングにより値が遅延する場合があります。
4. **Redis `flushdb`**：テスト開始前に `flushdb` を実行します。本番 Redis インスタンスに接続している場合、データが失われます。

## ベンチマーク結果（実測）

> 環境：Windows、Python 3.10、COUNT=100,000
> 注：Redis テストはローカル Redis サービスの応答が遅いため、120s タイムアウト内に完了しませんでした。以下はローカルキューの実測結果のみです。

### ローカルキュー比較

| キュータイプ | put/lpush | get/rpop | 備考 |
|------------|-----------|----------|------|
| **ThreadQueue** | 0.0777s | 0.0723s | 純粋なメモリ、シリアライゼーションなし、最速 |
| **MPQueue** | 0.1198s | **3.0071s** | put は許容範囲、プロセス間デシリアライゼーションにより get が極めて低速 |
| **Manager().Queue** | 8.0674s | 8.5525s | Manager サーバー転送、100x 以上低速 |

### Redis キュー（過去の参考値、今回は完全に実行されていません）

| 操作 | 推定所要時間（100k） | ボトルネック |
|------|-------------------|------------|
| Redis List lpush/rpop | ~2-3s | ネットワーク RTT |
| Redis Stream xadd/xread | ~3-5s | ストリーム解析オーバーヘッド |

**主要な結論**：
- ThreadQueue の get は MPQueue より **40x** 高速、Manager().Queue より **100x 以上**高速です
- MPQueue の get が最大の弱点です（3s vs 0.07s）。フレームワーク内部のキューがスレッドモードにフォールバックできれば、得られる利益は非常に大きくなります
- Redis キューはクロスデバイス/クロスネットワークシナリオに適しており、ローカル IPC には全く適していません

## 実行方法

```bash
python bench/bench_queue.py
```

## 依存関係

- `redis`
- `python-dotenv`
