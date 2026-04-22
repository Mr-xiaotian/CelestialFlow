# bench_ipc_queue.py ベンチマーク説明

## 目標

実際のプロセス間シナリオにおいて、複数の Python IPC（プロセス間通信）メカニズムの性能を比較します：MPQueue、SimpleQueue、Pipe、Manager().Queue。CelestialFlow のマルチプロセスモードにおけるキュー選定のためのデータを提供します。

## テスト内容

| メカニズム | 説明 | トポロジサポート |
|-----------|------|----------------|
| `MPQueue` | 標準マルチプロセスキュー | SPSC |
| `SimpleQueue` | ロックフリー簡易キュー | SPSC |
| `Pipe` | 双方向/単方向パイプ | SPSC |
| `Manager().Queue` | Manager サーバーベースのキュー | SPSC |

- **規模**：`COUNT = 100_000`、`REPEAT = 3`
- **ペイロードモード**：`int`（8 バイト）、`small`（約 16 バイト）、`medium`（約 144 バイト）、`large`（約 4104 バイト）
- **検証**：チェックサムによるデータ整合性の検証（欠損なし、破損なし）

## 主要な実装

- `producer_queue` / `consumer_queue`：センチネルオブジェクト `_SENTINEL = None` を使用してストリーム終了を通知します
- `producer_pipe` / `consumer_pipe`：明示的な `conn.close()` でハンドルリークを防止します
- `expected_checksum`：ペイロードモードに基づいて期待されるチェックサムを計算します

## 発生しうる問題

1. **Pipe ハンドルリーク**：consumer/producer が接続を正しくクローズしない場合、Windows 上でサブプロセスが終了できなくなるか、ハンドルが枯渇する可能性があります。
2. **`Manager().Queue` のサーバーボトルネック**：すべてのデータは Manager サーバープロセスを経由して転送される必要があります。producer/consumer の並行性が高い場合、サーバープロセスが単一のボトルネックとなります。
3. **大きなペイロードのメモリコピー**：`large` モードでは各ペイロードが約 4KB です。100k 回の転送は約 400MB のデータコピーを意味し、主にメモリ帯域幅をテストしており、キュー自体のテストではありません。
4. **Windows `spawn` シリアライゼーションオーバーヘッド**：すべてのペイロードは pickle を介して親子プロセス間で転送される必要があります。大きなオブジェクトのシリアライゼーション/デシリアライゼーション時間が支配的になります。

## ベンチマーク結果（実測）

> 環境：Windows、Python 3.10、spawn モード、COUNT=100,000、REPEAT=3、ペイロード=int（8 バイト）

| メカニズム | 平均所要時間 | スループット | MPQueue 比 |
|-----------|------------|------------|-----------|
| **MPQueue** | 1.328s | 75,277 items/s | 1.00x |
| **SimpleQueue** | 1.099s | 90,962 items/s | 1.21x |
| **Pipe** | 1.006s | 99,358 items/s | 1.32x |
| **Manager().Queue** | 7.884s | 12,684 items/s | 0.17x |

**主要な結論**：
- **Pipe が最速**：MPQueue より 32% 高速で、キュー抽象化レイヤーが不要です
- **SimpleQueue が次点**：ロックフリー実装で MPQueue より 21% 高速ですが、単一プロデューサー・単一コンシューマーのみサポートします
- **Manager().Queue が最遅**：MPQueue のスループットのわずか 17%。Manager サーバープロセスが絶対的なボトルネックです
- CelestialFlow のマルチプロセスキュー選定において、Pipe と SimpleQueue は高スループットシナリオの最適解です（トポロジが許す場合）

## 実行方法

```bash
python bench/bench_ipc_queue.py
```

## 依存関係

- `bench_utils.summarize`
