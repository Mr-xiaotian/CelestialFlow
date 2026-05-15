# bench_datastructures.py ベンチマーク説明

> 📅 最終更新日: 2026/05/09

## 目的

シングルスレッド環境における複数の Python データ構造と外部ストレージのリード/ライト性能を比較し、CelestialFlow の内部キューおよび永続化バックエンド選定に定量的な根拠を提供する。

## テスト内容

| テスト項目 | 説明 | 規模 |
|------------|------|------|
| `test_builtin_dict` | ネイティブ辞書の put/get | N=10,000 |
| `test_queue_thread` | `queue.Queue` シングルスレッド読み書き | N=10,000 |
| `test_mpqueue` | `multiprocessing.Queue` クロスプロセス読み書き（非推奨、参考用に保持） | N=10,000 |
| `test_manager_dict` | `Manager().dict` クロスプロセス読み書き | N=10,000 |
| `test_value_number` | `multiprocessing.Value` アトミックインクリメント（非推奨、参考用に保持） | N=10,000 |
| `test_redis_plain` | Redis 逐次 set/get | N=10,000 |
| `test_redis_pipeline` | Redis Pipeline バッチ set/get | N=10,000 |
| `test_redis_multithread_plain` | Redis マルチスレッド並行書き込み | N=10,000 / 10 スレッド |
| `test_redis_hash` | Redis Hash 逐次 hset/hget | N=10,000 |
| `test_redis_list` | Redis List 逐次 rpush/lindex | N=10,000 |
| `test_redis_set` | Redis Set 逐次 sadd/sismember | N=10,000 |
| `test_redis_zset` | Redis Sorted Set 逐次 zadd/zscore | N=10,000 |

## 主要設定

- `N = 10000`：各テストの反復回数
- Redis 接続パラメータは `.env` から読み込み（`REDIS_HOST`、`REDIS_PORT`、`REDIS_PASSWORD`）

## 発生し得る問題

1. **Redis 接続失敗**：`.env` に Redis 設定がないかサービスが未起動の場合、Redis 関連テストはスキップされ、警告のみ出力される。
2. **MPQueue のバッファ制限**：`mpqueue_worker` では N 個すべての要素を put してから get するため、N が大きい場合に OS パイプバッファの上限に達する可能性がある（特に Linux 上）。

> **注意**：`test_mpqueue` と `test_value_number` で使用される `multiprocessing.Queue` および `multiprocessing.Value` は、フレームワーク内部ではもう使用されていない（`stage_mode="process"` は削除済み）。これらのベンチマークは歴史的参考としてのみ保持されている。

## 実行方法

```bash
python bench/bench_datastructures.py
```

## ベンチマーク結果（実測）

> 環境：Windows、Python 3.10、ローカル Redis、N=10,000

| テスト項目 | put/set | get | 備考 |
|------------|---------|-----|------|
| Built-in dict | 0.0008s | 0.0003s | シングルスレッド基準、最速 |
| Queue (thread) | 0.0101s | 0.0108s | スレッドセーフキュー |
| MPQueue | 0.0149s | 0.3072s | クロスプロセスキュー、シリアライズにより get が著しく遅い |
| Manager.dict | 0.5156s | 0.5369s | Manager サーバー転送、50-100 倍遅い |
| Value (number) | 0.0174s | — | 10,000 回のアトミックインクリメント |
| Redis plain | 2.8352s | 2.9026s | 逐次 RTT、ネットワーク遅延が主因 |
| Redis pipeline | 0.1474s | 0.1202s | バッチ処理、plain の約 20 倍高速 |
| Redis multi-thread | 1.1749s | 1.0765s | 10 スレッド並行、pipeline なし |
| Redis hash | 2.8391s | 2.7675s | hset/hget、plain と同等 |
| Redis list | 2.6853s | 2.8370s | rpush/lindex |
| Redis set | 2.7932s | 3.2969s | sadd/sismember |
| Redis zset | 3.1955s | 3.1854s | zadd/zscore |

**主要な結論**：
- 純粋なインメモリ構造（dict、thread Queue）は、あらゆる IPC/ネットワーク方式より 2-3 桁高速
- Redis Pipeline はネットワークシナリオでの必須選択肢であり、遅延を約 2.8s から約 0.15s に削減可能
- MPQueue の get は put の約 20 倍遅く、主に pickle デシリアライズのオーバーヘッドが原因

## 依存関係

- `redis`
- `python-dotenv`
