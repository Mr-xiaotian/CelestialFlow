# bench_datastructures.py ベンチマーク説明

> 📅 最終更新日: 2026/06/16

## 目的

複数の Python データ構造と外部ストレージのシングルスレッド環境下におけるリード/ライト性能を比較し、CelestialFlow の内部キューおよび永続化バックエンド選定に定量的な根拠を提供する。

## テスト内容

| テスト項目 | 説明 | 規模 |
|------------|------|------|
| `test_builtin_dict` | ネイティブ辞書 put/get | N=10,000 |
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
2. **MPQueue のバッファ制限**：`mpqueue_worker` では全 N 要素を put してから get するため、N が大きい場合に OS パイプバッファの上限に達する可能性がある（特に Linux 上）。

> **注意**：`test_mpqueue` と `test_value_number` で使用される `multiprocessing.Queue` および `multiprocessing.Value` は、フレームワーク内部では既に使用されていない（`stage_mode="process"` は削除済み）。これらのベンチマークは引き続きスクリプト内でデフォルト実行され、主に純粋なインメモリ方式とのクロスプロセス性能ベースライン比較のために参考用として保持されている。

## 実行方法

```bash
python bench/bench_datastructures.py
```

## パラメータ調整

### テスト規模の変更

`bench/bench_datastructures.py` 内の `N = 10000` の値を変更することでテスト規模を調整できる：

```python
# 小規模で素早く検証
N = 1000

# 大規模ストレステスト
N = 100_000
```

### 特定テストの単独実行

スクリプトはデフォルトで全テストを実行する。特定のデータ構造のみを検証したい場合は、`main()` 内で他の呼び出しをコメントアウトする：

```python
if __name__ == "__main__":
    print(f"\nRunning benchmarks with N={N}\n")

    test_builtin_dict()          # 組み込み dict のみテスト
    # test_queue_thread()
    # test_mpqueue()
    # test_manager_dict()
    # ...
    # test_redis_plain(r)
    # test_redis_pipeline(r)
```

### Redis スレッド数の調整

`test_redis_multithread_plain` はカスタムの並行スレッド数に対応：

```python
# 関数呼び出し時に num_threads パラメータを渡す
test_redis_multithread_plain(r, num_threads=5)   # 5 スレッド
# test_redis_multithread_plain(r, num_threads=20)  # 20 スレッド
```

## ベンチマーク結果（実測）

### 履歴結果 - Windows ローカル Redis（日時未記録）

> 環境：Windows、Python 3.10、ローカル Redis、N=10,000

| テスト項目 | put/set | get | 備考 |
|--------|---------|-----|------|
| Built-in dict | 0.0008s | 0.0003s | シングルスレッド基準、最速 |
| Queue (thread) | 0.0101s | 0.0108s | スレッドセーフキュー |
| MPQueue | 0.0149s | 0.3072s | クロスプロセスキュー、シリアライズにより get が著しく低速化 |
| Manager.dict | 0.5156s | 0.5369s | Manager サーバー転送、50-100x 低速 |
| Value (number) | 0.0174s | — | 10,000 回のアトミックインクリメント |
| Redis plain | 2.8352s | 2.9026s | 逐次 RTT、ネットワーク遅延が主因 |
| Redis pipeline | 0.1474s | 0.1202s | バッチ処理、plain 比約 20x 高速 |
| Redis multi-thread | 1.1749s | 1.0765s | 10 スレッド並行、pipeline なし |
| Redis hash | 2.8391s | 2.7675s | hset/hget、plain と同等 |
| Redis list | 2.6853s | 2.8370s | rpush/lindex |
| Redis set | 2.7932s | 3.2969s | sadd/sismember |
| Redis zset | 3.1955s | 3.1854s | zadd/zscore |

**主要な結論**：
- 純粋なインメモリ構造（dict、thread Queue）は、あらゆる IPC/ネットワーク方式より 2-3 桁高速
- Redis Pipeline はネットワークシナリオでの必須選択肢であり、遅延を ~2.8s から ~0.15s に削減可能
- MPQueue の get は put より約 20x 遅く、主に pickle デシリアライズが原因

### 2026/06/16 - ローカル Redis 利用可能時の再テスト

> 環境：Windows、N=10,000、今回 Redis サービス利用可能

| テスト項目 | put/set | get | 備考 |
|--------|---------|-----|------|
| Built-in dict | 0.0004s | 0.0002s | シングルスレッド基準、最速 |
| Queue (thread) | 0.0057s | 0.0063s | スレッドセーフキュー |
| MPQueue | 0.0075s | 0.1294s | get は依然として put より著しく遅い |
| Manager.dict | 0.3494s | 0.3848s | プロキシ転送オーバーヘッドが顕著 |
| Value (number) | 0.0097s | — | 10,000 回のアトミックインクリメント |
| Redis plain | 2.5804s | 2.4552s | 逐次 RTT が主因 |
| Redis pipeline | 0.0874s | 0.0574s | 今回最速の Redis 読み書き方式 |
| Redis multi-thread | 0.8925s | 0.8135s | 10 スレッド、pipeline なし |
| Redis hash | 2.4163s | 2.5311s | plain と近い |
| Redis list | 2.4061s | 2.5197s | rpush/lindex |
| Redis set | 2.4366s | 2.4330s | sadd/sismember |
| Redis zset | 2.7509s | 2.7586s | zadd/zscore |

**今回の補足結論**：
- 純粋なインメモリ構造は依然としてすべての Redis 方式より 2-4 桁優位。ネットワーク RTT が引き続き主因
- `Redis pipeline` は引き続きその必要性を証明。書き込みは `plain` 比で約 **29x** 高速、読み取りは約 **43x** 高速
- `MPQueue` は今回履歴より顕著に高速だが、`get` は依然として `put` よりはるかに遅く、シリアライズ/デシリアライズのコストが残存

## 依存関係

- `redis`
- `python-dotenv`
