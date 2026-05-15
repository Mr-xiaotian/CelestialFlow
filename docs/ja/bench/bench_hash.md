# bench_hash.py ベンチマーク説明

> 📅 最終更新日: 2026/04/22

## 目的

9 種類のオブジェクト→ハッシュ文字列のシリアライズ+ハッシュ戦略を体系的に比較し、`TaskEnvelope` の重複排除およびトラッキング ID 生成の最適な方式を選定する。評価次元は速度、安定性、衝突率、異なるデータ型への対応度を含む。

## テスト戦略

| 方法 | シリアライズ方式 | ハッシュアルゴリズム | 特徴 |
|------|-----------------|---------------------|------|
| `pickle+md5` | `pickle.dumps` | MD5 | 任意のオブジェクトをサポートするが不安定（プロトコルバージョンに依存） |
| `pickle+sha1` | `pickle.dumps` | SHA1 | 同上、より長いダイジェスト |
| `pickle+blake2b16` | `pickle.dumps` | BLAKE2b(16B) | より高速、短いダイジェスト |
| `json+md5` | カスタム JSON | MD5 | クロス言語安定だが JSON シリアライズ可能な型のみ対応 |
| `json+sha256` | カスタム JSON | SHA256 | より安全だがより遅い |
| `repr+md5` | `repr(normalized)` | MD5 | 可読性が良いが `set`/`dict` の順序に敏感 |
| `repr+sha1+uuid` | `repr(normalized)` | SHA1→UUID | 標準 UUID 形式で出力 |
| `repr+blake2b16` | `repr(normalized)` | BLAKE2b(16B) | 高速 + 短いダイジェスト |
| `fast_mixed` | 型分岐（bytes/str/repr/pickle） | SHA1 | 基本型にはショートカット、複雑なオブジェクトは pickle にフォールバック |

## テストデータセット

11 種の典型的なデータ形状をカバー：`int`、`short_str`、`long_str_4k`、`bytes_4k`、`small_tuple`、`small_list`、`list_100_ints`、`small_dict`、`dict_100_pairs`、`nested_dict`、`set_100_ints`。

## 主要な実装

- `normalize_for_hash`：`set`、`dict`、`tuple`、`list`、`bytes` を安定した構造に変換（ソート済みキー、型マーカー）
- `benchmark_one`：`timeit.repeat`（7 回繰り返し、各 10,000 回呼び出し）を使用、GC 無効、平均と標準偏差を出力

## 発生し得る問題

1. **pickle の不安定性**：同じオブジェクトでも、異なる Python バージョンや実行間で `pickle.dumps` のバイトが異なる場合がある（特に集合の順序）。ハッシュの不一致を引き起こす。**クロスセッションの重複排除には不適**。
2. **`fast_mixed` の型分岐の盲点**：`__repr__` を実装していないカスタムクラスが渡された場合、`pickle.dumps` にフォールバックし、pickle の不安定性問題を引き継ぐ。
3. **UUID 形式の衝突**：`repr+sha1+uuid` は SHA1 を 16 バイトに切り詰めてから UUID に変換する。確率は極めて低いが、厳密には暗号学的安全性が犠牲になる。
4. **大きなオブジェクトのメモリ圧力**：`long_str_4k`、`bytes_4k` は 10,000 回の繰り返しテスト中に一時的に大量のメモリを消費する可能性がある。

## ベンチマーク結果（実測）

> 環境：Windows、Python 3.10、timeit repeat=7, number=10,000

### 総合ランキング（全データ型の平均）

| 方法 | 平均所要時間 | 特徴 |
|------|-------------|------|
| `fast_mixed` | ~2.5 us | 基本型にショートカット、総合最速 |
| `pickle+blake2b16` | ~3.0 us | pickle シリアライズ + 高速ハッシュ |
| `pickle+sha1` | ~3.2 us | 安定、互換性良好 |
| `repr+blake2b16` | ~15 us | repr 正規化 + 高速ハッシュ |
| `json+md5` / `json+sha256` | ~25 us | クロス言語安定だが最も遅い |
| `repr+sha1+uuid` | ~25 us | UUID 形式出力、追加変換オーバーヘッドあり |

### 典型的なデータポイント（単位：マイクロ秒/回）

| ケース | 最速 | 最遅 | 最適な方法 |
|--------|------|------|-----------|
| int | ~1.3 | ~4.3 | pickle+sha1 / fast_mixed |
| short_str | ~1.3 | ~4.2 | repr+blake2b16 / fast_mixed |
| long_str_4k | ~4.1 | ~23.5 | pickle+sha1 / fast_mixed |
| bytes_4k | ~3.6 | ~58.4 | **fast_mixed**（ネイティブ bytes サポート） |
| small_dict | ~1.9 | ~17.4 | pickle+blake2b16 |
| dict_100_pairs | ~7.8 | ~104.4 | pickle+sha1 / fast_mixed |
| list_100_ints | ~2.9 | ~36.0 | fast_mixed |
| set_100_ints | ~3.7 | ~43.1 | pickle+blake2b16 / fast_mixed |

**主要な結論**：
- `fast_mixed` は bytes と大規模コレクションで絶対的な優位性を持つ（生バイトを直接ハッシュし、シリアライズを回避）
- `json+sha256` と `repr+sha1+uuid` はすべてのシナリオで pickle 方式より著しく遅い。安定性/形式に厳格な要件がある場合のみ使用
- pickle 系列の方法は小さなオブジェクトで優れた性能を発揮（1-3 us）。ただし pickle のクロスセッション安定性リスクに注意

## 実行方法

```bash
python bench/bench_hash.py
```

## 依存関係

- `celestialflow.format_table`
