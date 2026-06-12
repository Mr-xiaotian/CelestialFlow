# bench_hash_container.py ベンチマーク説明

> 📅 最終更新日: 2026/06/11

## 目的

ハッシュ型として `bytes` を使用することを決定した後、20 バイト SHA1 ハッシュを格納する異なるコンテナ構造のメモリオーバーヘッドと検索性能を比較し、`processed_set` のコンテナ選定（純粋な set vs. エビクション対応 LRU）にデータを提供する。

## テストコンテナ

| コンテナ | 説明 | 適用シナリオ |
|----------|------|-------------|
| `set[bytes]` | ベースライン、最もコンパクト | エビクション不要、タスク量が制御可能 |
| `dict[bytes, None]` | dict の最小オーバーヘッド | dict インターフェースが必要だが値を格納しない |
| `dict[bytes, float]` | タイムスタンプを格納 | 時間ベースで期限切れエントリを削除 |
| `OrderedDict[bytes, None]` | 順序保持 dict | LRU の基本構造 |
| LRU(unlimited) | OrderedDict + `move_to_end` | LRU セマンティクス、容量制限なし |
| LRU(50k) | 同上、容量上限 50,000 | メモリ制約シナリオ、最長未使用エントリを削除 |

## 測定軸

- **コンテナ総メモリ増分**：`tracemalloc` スナップショット差分
- **エントリあたり平均オーバーヘッド**：総増分 / エントリ数
- **構築所要時間**：N 回の挿入（LRU の `move_to_end` / `popitem` オーバーヘッドを含む）
- **検索レイテンシ**：ヒット / ミス各 0.3s 定常測定

## ベンチマーク結果（実測）

> 環境：Windows 11、Python 3.14、N=100,000

| コンテナ | エントリ数 | 総メモリ(MB) | エントリ毎(B) | 構築(ms) | Hit(ns) | Miss(ns) |
|----------|-----------|-------------|--------------|---------|---------|----------|
| `set[bytes]` | 100,000 | 4.00 | 42.0 | 8.52 | 112.7 | 112.0 |
| `dict[B,None]` | 100,000 | 5.00 | 52.4 | 8.87 | 113.9 | 112.7 |
| `dict[B,float]` | 100,000 | 7.29 | 76.4 | 65.29 | 113.8 | 111.9 |
| `OrderedDict` | 100,000 | 10.05 | 105.4 | 42.08 | 122.5 | 119.4 |
| LRU(unlimited) | 100,000 | 10.05 | 105.4 | 57.25 | 115.6 | 115.1 |
| LRU(50k) | 50,000 | 8.53 | 178.8 | 69.95 | 124.0 | 115.3 |

### メモリ比較（set[bytes] 比）

| コンテナ | 倍率 | 絶対値 |
|----------|------|--------|
| `dict[B,None]` | 125% | 5.00 MB |
| `dict[B,float]` | 182% | 7.29 MB |
| `OrderedDict` | 251% | 10.05 MB |
| LRU(unlimited) | 251% | 10.05 MB |
| LRU(50k) | 213% | 8.53 MB |

**主要な結論**：
- `set[bytes]` が最もコンパクト（42 B/エントリ）、ただし古いエントリを削除できず、長期実行ではメモリが線形増加
- `dict[B,None]` はわずか 25% のメモリ増加で済み、バッチクリーンアップ（バッチごとの `clear()` 等）のみが必要な場合に最適
- `OrderedDict` / LRU のメモリは set の 2.5 倍（双方向リンクリストのオーバーヘッド）、ただし O(1) のエビクション能力を提供
- LRU(50k) のメモリはタスク量に関わらず ~8.5 MB で上限固定。代償としてウィンドウ外の重複タスクは検出漏れが発生
- 全コンテナの検索性能は近似（112-124 ns）、コンテナ選択はスループットに影響しない
- **推奨**：デフォルトは `set[bytes]`。メモリ上限が必要な場合は `OrderedDict` で LRU を実装し、`maxsize` はビジネス許容度に応じて設定

## 実行方法

```bash
python bench/bench_hash_container.py
```

## パラメータ調整

### テスト規模の変更

`bench/bench_hash_container.py` の先頭で `N` 値を変更：

```python
N = 10_000          # 小規模で素早く検証
# N = 1_000_000     # 大規模テスト、メモリの線形増加を観察
```

### 特定コンテナのみをテスト

コンテナリストはスクリプト先頭の `configs` で定義されており、コメントアウトで選択できる：

```python
configs = [
    ("set[bytes]", build_set, all_hashes),
    ("dict[B,None]", build_dict_none, all_hashes),
    # ("dict[B,float]", build_dict_float, all_hashes),      # タイムスタンプシナリオをスキップ
    # ("OrderedDict", build_ordered_dict, all_hashes),
    ("LRU(unlimited)", build_lru, all_hashes, 0),
    ("LRU(50k)", build_lru, all_hashes, 50_000),
]
```

### LRU 容量の調整

```python
# configs 内の LRU maxsize パラメータを変更
("LRU(10k)", build_lru, all_hashes, 10_000)    # 1 万エントリに制限
# ("LRU(200k)", build_lru, all_hashes, 200_000) # 20 万エントリに拡大
```

修正後に実行：

```bash
python bench/bench_hash_container.py
```

## 依存関係

- 標準ライブラリのみ（`random`、`tracemalloc`、`collections`、`time`）
