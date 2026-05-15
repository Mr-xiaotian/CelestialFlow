# bench_ipc_queue.py ベンチマーク説明

> 📅 最終更新日: 2026/04/22

## 目的

実際のクロスプロセスシナリオで複数の Python IPC（プロセス間通信）メカニズムの性能を比較する：MPQueue、SimpleQueue、Pipe、Manager().Queue。CelestialFlow のマルチプロセスモードにおけるキュー選定にデータサポートを提供する。

## テスト内容

| メカニズム | 説明 | トポロジサポート |
|------------|------|-----------------|
| `MPQueue` | 標準マルチプロセスキュー | SPSC |
| `SimpleQueue` | ロックフリー簡易キュー | SPSC |
| `Pipe` | 双方向/単方向パイプ | SPSC |
| `Manager().Queue` | Manager サーバーベースのキュー | SPSC |

- **規模**：`COUNT = 100_000`、`REPEAT = 3`
- **ペイロードモード**：`int`（8 バイト）、`small`（~16 バイト）、`medium`（~144 バイト）、`large`（~4104 バイト）
- **検証**：チェックサムによるデータ整合性検証（損失なし、破損なし）

## 主要な実装

- `producer_queue` / `consumer_queue`：ストリーム終了を示す番兵オブジェクト `_SENTINEL = None` を使用
- `producer_pipe` / `consumer_pipe`：ハンドルリーク防止のため明示的な `conn.close()`
- `expected_checksum`：ペイロードモードに基づいて期待チェックサムを計算

## 発生し得る問題

1. **Pipe ハンドルリーク**：consumer/producer が接続を適切に閉じない場合、Windows 上で子プロセスが終了できなくなるかハンドル枯渇を引き起こす可能性がある。
2. **`Manager().Queue` のサーバーボトルネック**：すべてのデータは Manager サーバープロセスを経由して転送される。producer/consumer の並行度が高い場合、サーバープロセスがシングルポイントのボトルネックになる。
3. **大きなペイロードのメモリコピー**：`large` モードでは各ペイロードが約 4KB。10 万回の転送は約 400MB のデータコピーを意味し、キュー自体ではなくメモリ帯域幅のテストとなる。
4. **Windows `spawn` のシリアライズオーバーヘッド**：すべてのペイロードは pickle を通じて親子プロセス間で伝送される。大きなオブジェクトではシリアライズ/デシリアライズ時間が支配的になる。

## ベンチマーク結果（実測）

> 環境：Windows、Python 3.10、spawn モード、COUNT=100,000、REPEAT=3、ペイロード=int（8 バイト）

| メカニズム | 平均所要時間 | スループット | MPQueue 比 |
|------------|-------------|-------------|-----------|
| **MPQueue** | 1.328s | 75,277 items/s | 1.00x |
| **SimpleQueue** | 1.099s | 90,962 items/s | 1.21x |
| **Pipe** | 1.006s | 99,358 items/s | 1.32x |
| **Manager().Queue** | 7.884s | 12,684 items/s | 0.17x |

**主要な結論**：
- **Pipe が最速**：MPQueue より 32% 高速、キュー抽象化レイヤー不要
- **SimpleQueue が次点**：ロックフリー実装、MPQueue より 21% 高速だが、単一プロデューサー単一コンシューマーのみサポート
- **Manager().Queue が最も遅い**：MPQueue のスループットのわずか 17%。Manager サーバープロセスが絶対的なボトルネック
- CelestialFlow のマルチプロセスキュー選定では、Pipe と SimpleQueue が高スループットシナリオの最適解（トポロジが許容する場合）

## 実行方法

```bash
python bench/bench_ipc_queue.py
```

## 依存関係

- `bench_utils.summarize`
