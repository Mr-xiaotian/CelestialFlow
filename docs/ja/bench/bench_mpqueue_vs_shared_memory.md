# bench_mpqueue_vs_shared_memory.py ベンチマーク説明

> 📅 最終更新日: 2026/04/22

## 目的

より複雑なプロデューサー-コンシューマートポロジ（SPSC、MPSC、SPMC）において、`multiprocessing.Queue` と共有メモリベースのカスタムリングバッファの性能を比較する。CelestialFlow の高スループットシナリオにおける IPC 最適化に詳細なデータを提供する。

## テスト内容

| トポロジ | プロデューサー | コンシューマー | 説明 |
|----------|--------------|---------------|------|
| SPSC | 1 | 1 | 単一プロデューサー単一コンシューマー |
| MPSC | 4 | 1 | 複数プロデューサー単一コンシューマー |
| SPMC | 1 | 4 | 単一プロデューサー複数コンシューマー |

- **規模**：`COUNT = 100_000`、`REPEAT = 3`
- **SharedMemory 設定**：`SLOT_COUNT = 1024`、各スロットサイズ = 4B 長さプレフィックス + ペイロード
- **同期プリミティブ**：`Lock`（読み書きインデックスの保護）、`Semaphore`（空き/使用済みスロットカウント）

## 主要な実装

### SharedMemory リングプロトコル
1. **Producer**：`empty_slots.acquire()` → `write_lock` 下でペイロード書き込み → `full_slots.release()`
2. **Consumer**：`full_slots.acquire()` → `read_lock` 下でペイロード読み取り → `empty_slots.release()`
3. **設計のポイント**：`full_slots.release()` はロック外で実行し、並行度を最大化

## 発生し得る問題

1. **SharedMemory のライフサイクル管理**：`shm.unlink()` はすべてのプロセスが閉じた後にのみ実行する必要がある。子プロセスが `shm.close()` を呼ばずに異常終了した場合、`unlink` が失敗するかメモリリークが発生する可能性がある。
2. **slot_size の不足**：`payload_max_bytes(mode)` の計算が不正確か、実際のペイロードが `slot_size - 4` を超えた場合、`producer_shm_ring` は `RuntimeError` をスローする。
3. **MPSC の書き込み競合**：`write_lock` がインデックスと書き込み操作を保護しているが、複数のプロデューサーは依然として書き込みをシリアライズするため、MPSC では SharedMemory の優位性が期待ほどではない可能性がある。
4. **Windows の共有メモリ命名**：Windows 上の `SharedMemory(name=shm_name)` はグローバル名前空間に依存する。名前の衝突（例：複数のベンチマークインスタンスの同時実行）により予測不能な動作が発生する可能性がある。

## ベンチマーク結果（実測）

> 環境：Windows、Python 3.10、spawn モード、COUNT=100,000、REPEAT=3、ペイロード=int（8 バイト）、SLOT_COUNT=1024

### SPSC（単一プロデューサー単一コンシューマー）

| メカニズム | 平均所要時間 | スループット | 勝者 |
|------------|-------------|-------------|------|
| MPQueue | 1.281s | 78,066 items/s | — |
| SharedMemory ring | **0.878s** | **113,853 items/s** | ✅ **SharedMemory**（1.46 倍高速） |

### MPSC（4 プロデューサー 1 コンシューマー）

| メカニズム | 平均所要時間 | スループット | 勝者 |
|------------|-------------|-------------|------|
| MPQueue | **1.618s** | **61,787 items/s** | ✅ **MPQueue**（1.18 倍高速） |
| SharedMemory ring | 1.905s | 52,487 items/s | — |

### SPMC（1 プロデューサー 4 コンシューマー）

| メカニズム | 平均所要時間 | スループット | 勝者 |
|------------|-------------|-------------|------|
| MPQueue | 2.851s | 35,070 items/s | — |
| SharedMemory ring | **1.989s** | **50,277 items/s** | ✅ **SharedMemory**（1.43 倍高速） |

**主要な結論**：
- **SPSC**：SharedMemory が明確に優位。pickle シリアライズとカーネルモードキュー管理を回避
- **MPSC**：SharedMemory の write_lock がボトルネックに（4 プロデューサーが書き込みをシリアライズ）。MPQueue の方が高速
- **SPMC**：SharedMemory が再び優位。複数のコンシューマーが異なるスロットを並列に読み取り可能
- 戦略推奨：単一プロデューサーシナリオでは SharedMemory を優先。複数プロデューサーシナリオでは MPQueue を優先

## 実行方法

```bash
python bench/bench_mpqueue_vs_shared_memory.py
```

## 依存関係

- `bench_utils.summarize`
