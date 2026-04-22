# bench_datastructures.py ベンチマーク説明

## 目標

シングルスレッド/マルチプロセス環境における複数の Python データ構造および外部ストレージの読み書き性能を比較し、CelestialFlow の内部キュー、共有状態、永続化バックエンドの選定に定量的な根拠を提供します。

## テスト内容

| テスト項目 | 説明 | 規模 |
|-----------|------|------|
| `test_builtin_dict` | ネイティブ辞書の put/get | N=10,000 |
| `test_queue_thread` | `queue.Queue` シングルスレッド読み書き | N=10,000 |
| `test_mpqueue` | `multiprocessing.Queue` プロセス間読み書き | N=10,000 |
| `test_manager_dict` | `Manager().dict` プロセス間読み書き | N=10,000 |
| `test_value_number` | `multiprocessing.Value` アトミックインクリメント | N=10,000 |
| `test_redis_plain` | Redis 逐次 set/get | N=10,000 |
| `test_redis_pipeline` | Redis Pipeline 一括 set/get | N=10,000 |
| `test_redis_multithread_plain` | Redis マルチスレッド並行書き込み | N=10,000 / 10 threads |
| `test_redis_hash` | Redis Hash 逐次 hset/hget | N=10,000 |
| `test_redis_list` | Redis List 逐次 rpush/lindex | N=10,000 |
| `test_redis_set` | Redis Set 逐次 sadd/sismember | N=10,000 |
| `test_redis_zset` | Redis Sorted Set 逐次 zadd/zscore | N=10,000 |

## 主要設定

- `N = 10000`：各テストの反復回数
- Redis 接続パラメータは `.env` から読み込みます（`REDIS_HOST`、`REDIS_PORT`、`REDIS_PASSWORD`）

## 発生しうる問題

1. **Redis 接続失敗**：`.env` に Redis 設定がないか、サービスが起動していない場合、Redis 関連のテストはスキップされ、警告のみ出力されます。
2. **Windows マルチプロセス起動オーバーヘッド**：`MPQueue` および `Manager().dict` テストは Windows の `spawn` モードではサブプロセスの起動自体に多くの時間がかかり、put/get の計測時間が不正確になる場合があります。
3. **MPQueue のバッファ制限**：`mpqueue_worker` では先に N 個の要素をすべて put してから get するため、N が大きい場合に OS パイプバッファの上限に達する可能性があります（特に Linux 上）。

## 実行方法

```bash
python bench/bench_datastructures.py
```

## ベンチマーク結果（実測）

> 環境：Windows、Python 3.10、ローカル Redis、N=10,000

| テスト項目 | put/set | get | 備考 |
|-----------|---------|-----|------|
| Built-in dict | 0.0008s | 0.0003s | シングルスレッド基準、最速 |
| Queue (thread) | 0.0101s | 0.0108s | スレッドセーフキュー |
| MPQueue | 0.0149s | 0.3072s | プロセス間キュー、シリアライゼーションにより get が大幅に遅延 |
| Manager.dict | 0.5156s | 0.5369s | Manager サーバー転送、50-100x 低速 |
| Value (number) | 0.0174s | — | 10,000 回のアトミックインクリメント |
| Redis plain | 2.8352s | 2.9026s | 逐次 RTT、ネットワーク遅延が支配的 |
| Redis pipeline | 0.1474s | 0.1202s | バッチ処理、plain より約 20x 高速 |
| Redis multi-thread | 1.1749s | 1.0765s | 10 スレッド並行、pipeline なし |
| Redis hash | 2.8391s | 2.7675s | hset/hget、plain と同等 |
| Redis list | 2.6853s | 2.8370s | rpush/lindex |
| Redis set | 2.7932s | 3.2969s | sadd/sismember |
| Redis zset | 3.1955s | 3.1854s | zadd/zscore |

**主要な結論**：
- 純粋なインメモリ構造（dict、スレッド Queue）は、あらゆる IPC/ネットワーク方式より 2-3 桁高速です
- Redis Pipeline はネットワークシナリオにおいて必須であり、遅延を約 2.8s から約 0.15s に削減します
- MPQueue の get は put より約 20x 遅く、主に pickle デシリアライゼーションのオーバーヘッドが原因です

## 依存関係

- `redis`
- `python-dotenv`
