# bench_mpqueue_vs_shared_memory.py ベンチマーク説明

> 📅 最終更新日: 2026/04/22

## 目標

より複雑なプロデューサー-コンシューマートポロジ（SPSC、MPSC、SPMC）において、`multiprocessing.Queue` と `shared_memory` ベースのカスタムリングバッファの性能を比較します。CelestialFlow の高スループットシナリオにおける IPC 最適化のための詳細なデータを提供します。

## テスト内容

| トポロジ | プロデューサー | コンシューマー | 説明 |
|---------|-------------|-------------|------|
| SPSC | 1 | 1 | 単一プロデューサー・単一コンシューマー |
| MPSC | 4 | 1 | 複数プロデューサー・単一コンシューマー |
| SPMC | 1 | 4 | 単一プロデューサー・複数コンシューマー |

- **規模**：`COUNT = 100_000`、`REPEAT = 3`
- **SharedMemory 設定**：`SLOT_COUNT = 1024`、各スロットサイズ = 4B 長さプレフィックス + ペイロード
- **同期プリミティブ**：`Lock`（読み書きインデックスの保護）、`Semaphore`（空/満スロットのカウント）

## 主要な実装

### SharedMemory リングプロトコル
1. **Producer**：`empty_slots.acquire()` -> `write_lock` 下でペイロードを書き込み -> `full_slots.release()`
2. **Consumer**：`full_slots.acquire()` -> `read_lock` 下でペイロードを読み取り -> `empty_slots.release()`
3. **重要な設計**：`full_slots.release()` はロック外で実行し、並行性を最大化します

## 発生しうる問題

1. **SharedMemory ライフサイクル管理**：`shm.unlink()` はすべてのプロセスがクローズした後にのみ実行する必要があります。サブプロセスが `shm.close()` を呼び出さずに異常終了した場合、`unlink` が失敗するかメモリリークが発生する可能性があります。
2. **slot_size の不足**：`payload_max_bytes(mode)` の計算が不正確であるか、実際のペイロードが `slot_size - 4` を超える場合、`producer_shm_ring` は `RuntimeError` をスローします。
3. **MPSC 書き込み競合**：`write_lock` がインデックスと書き込み操作を保護していますが、複数のプロデューサーは依然として書き込みをシリアライズします。MPSC では SharedMemory の優位性が期待ほどではない場合があります。
4. **Windows 共有メモリの命名**：`SharedMemory(name=shm_name)` は Windows 上でグローバル名前空間に依存します。名前の衝突（例：複数のベンチマークインスタンスの同時実行）は予測不能な動作を引き起こす可能性があります。

## ベンチマーク結果（実測）

> 環境：Windows、Python 3.10、spawn モード、COUNT=100,000、REPEAT=3、ペイロード=int（8 バイト）、SLOT_COUNT=1024

### SPSC（単一プロデューサー・単一コンシューマー）

| メカニズム | 平均所要時間 | スループット | 勝者 |
|-----------|------------|------------|------|
| MPQueue | 1.281s | 78,066 items/s | — |
| SharedMemory ring | **0.878s** | **113,853 items/s** | **SharedMemory**（1.46x 高速） |

### MPSC（4 プロデューサー 1 コンシューマー）

| メカニズム | 平均所要時間 | スループット | 勝者 |
|-----------|------------|------------|------|
| MPQueue | **1.618s** | **61,787 items/s** | **MPQueue**（1.18x 高速） |
| SharedMemory ring | 1.905s | 52,487 items/s | — |

### SPMC（1 プロデューサー 4 コンシューマー）

| メカニズム | 平均所要時間 | スループット | 勝者 |
|-----------|------------|------------|------|
| MPQueue | 2.851s | 35,070 items/s | — |
| SharedMemory ring | **1.989s** | **50,277 items/s** | **SharedMemory**（1.43x 高速） |

**主要な結論**：
- **SPSC**：SharedMemory は明確な優位性があり、pickle シリアライゼーションとカーネルモードのキュー管理を回避します
- **MPSC**：SharedMemory の write_lock がボトルネックとなり（4 プロデューサーが書き込みをシリアライズ）、MPQueue の方が高速です
- **SPMC**：SharedMemory が再びリードし、複数のコンシューマーが異なるスロットを並列に読み取ることができます
- 戦略的推奨：単一プロデューサーシナリオでは SharedMemory を優先し、複数プロデューサーシナリオでは MPQueue を優先してください

## 実行方法

```bash
python bench/bench_mpqueue_vs_shared_memory.py
```

## 依存関係

- `bench_utils.summarize`
