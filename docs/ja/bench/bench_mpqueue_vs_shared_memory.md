# bench_mpqueue_vs_shared_memory.py ベンチマーク説明

> 📅 最終更新日: 2026/04/22

## 目的

より複雑な生産者-消費者トポロジ（SPSC、MPSC、SPMC）において、`multiprocessing.Queue` と `shared_memory` ベースのカスタムリングバッファの性能を比較する。CelestialFlow の高スループットシナリオにおける IPC 最適化に詳細なデータを提供する。

## テスト内容

| トポロジ | 生産者 | 消費者 | 説明 |
|----------|--------|--------|------|
| SPSC | 1 | 1 | 単一生産者単一消費者 |
| MPSC | 4 | 1 | 複数生産者単一消費者 |
| SPMC | 1 | 4 | 単一生産者複数消費者 |

- **規模**：`COUNT = 100_000`、`REPEAT = 3`
- **SharedMemory 設定**：`SLOT_COUNT = 1024`、各スロットサイズ = 4B 長さプレフィックス + ペイロード
- **同期プリミティブ**：`Lock`（読み書きインデックス保護）、`Semaphore`（空/満スロットカウント）

## 主要実装

### SharedMemory Ring プロトコル
1. **Producer**：`empty_slots.acquire()` → `write_lock` 下でペイロード書き込み → `full_slots.release()`
2. **Consumer**：`full_slots.acquire()` → `read_lock` 下でペイロード読み取り → `empty_slots.release()`
3. **主要設計**：`full_slots.release()` をロック外で実行し、並行度を最大化

## 発生し得る問題

1. **SharedMemory ライフサイクル管理**：`shm.unlink()` は全プロセスが終了した後にのみ実行可能。子プロセスが異常終了して `shm.close()` されなかった場合、`unlink` が失敗するかメモリリークが発生する可能性がある。
2. **slot_size 不足**：`payload_max_bytes(mode)` の計算が不正確、または実際のペイロードが `slot_size - 4` を超えた場合、`producer_shm_ring` が `RuntimeError` をスローする。
3. **MPSC 書き込み競合**：`write_lock` はインデックスと書き込み操作を保護するが、複数の生産者は依然として書き込みがシリアライズされる。MPSC における SharedMemory の優位性は期待より低くなる可能性がある。
4. **Windows 共有メモリ命名**：`SharedMemory(name=shm_name)` は Windows 上でグローバル名前空間に依存する。名前の衝突（複数の benchmark インスタンスの同時実行等）は予期しない動作を引き起こす可能性がある。

## ベンチマーク結果（実測）

> 環境：Windows、Python 3.10、spawn モード、COUNT=100,000、REPEAT=3、負荷=int（8 バイト）、SLOT_COUNT=1024

### SPSC（単一生産者単一消費者）

| メカニズム | 平均所要時間 | スループット | 勝者 |
|------------|-------------|-------------|------|
| MPQueue | 1.281s | 78,066 items/s | — |
| SharedMemory ring | **0.878s** | **113,853 items/s** | ✅ **SharedMemory**（1.46x 高速） |

### MPSC（4 生産者 1 消費者）

| メカニズム | 平均所要時間 | スループット | 勝者 |
|------------|-------------|-------------|------|
| MPQueue | **1.618s** | **61,787 items/s** | ✅ **MPQueue**（1.18x 高速） |
| SharedMemory ring | 1.905s | 52,487 items/s | — |

### SPMC（1 生産者 4 消費者）

| メカニズム | 平均所要時間 | スループット | 勝者 |
|------------|-------------|-------------|------|
| MPQueue | 2.851s | 35,070 items/s | — |
| SharedMemory ring | **1.989s** | **50,277 items/s** | ✅ **SharedMemory**（1.43x 高速） |

**主要な結論**：
- **SPSC**：SharedMemory の優位性が顕著、pickle シリアライズとカーネルモードキュー管理を回避
- **MPSC**：SharedMemory の write_lock がボトルネックに（4 生産者がシリアライズ書き込み）、MPQueue の方が高速
- **SPMC**：SharedMemory が再びリード、複数の消費者が異なるスロットを並列読み取り可能
- 戦略提案：単一生産者シナリオでは SharedMemory を優先、複数生産者シナリオでは MPQueue を優先

## 実行方法

```bash
python bench/bench_mpqueue_vs_shared_memory.py
```

## パラメータ調整

### テスト規模と設定の変更

`bench/bench_mpqueue_vs_shared_memory.py` の先頭で調整：

```python
COUNT = 10_000       # 回数を減らして素早く検証
# COUNT = 1_000_000  # 大規模ストレステスト

REPEAT = 1           # 1 ラウンドのみ
# REPEAT = 5         # ラウンドを増加

PAYLOAD_MODE = "int"  # 負荷タイプ: int / small / medium / large
SLOT_COUNT = 256     # リングバッファスロット数を削減
# SLOT_COUNT = 4096  # スロット数を増やし、バッファサイズのスループットへの影響を観察
```

### 特定トポロジのみをテスト

```python
TOPOLOGIES = [
    ("SPSC", 1, 1),     # 単一生産者単一消費者のみテスト
    # ("MPSC", 4, 1),   # 複数生産者シナリオをスキップ
    # ("SPMC", 1, 4),   # 単一生産者複数消費者シナリオをスキップ
]
```

修正後に実行：

```bash
python bench/bench_mpqueue_vs_shared_memory.py
```

## 依存関係

- `bench_utils.summarize`
