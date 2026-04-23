# bench_hash.py ベンチマーク説明

> 📅 最終更新日: 2026/04/22

## 目標

9 種類のオブジェクト→ハッシュ文字列のシリアライゼーション+ハッシュ戦略を体系的に比較し、`TaskEnvelope` の重複排除およびトラッキング ID 生成に最適な方法を選定します。評価の観点は、速度、安定性、衝突率、各データ型のサポート度です。

## テスト戦略

| 方法 | シリアライゼーション方式 | ハッシュアルゴリズム | 特徴 |
|------|----------------------|-------------------|------|
| `pickle+md5` | `pickle.dumps` | MD5 | 任意のオブジェクトをサポートしますが、不安定（プロトコルバージョンに依存） |
| `pickle+sha1` | `pickle.dumps` | SHA1 | 同上、より長いダイジェスト |
| `pickle+blake2b16` | `pickle.dumps` | BLAKE2b(16B) | より高速、短いダイジェスト |
| `json+md5` | カスタム JSON | MD5 | クロス言語で安定しますが、JSON シリアライズ可能な型のみサポート |
| `json+sha256` | カスタム JSON | SHA256 | より安全ですが、より低速 |
| `repr+md5` | `repr(normalized)` | MD5 | 可読性が良好ですが、`set`/`dict` の順序に敏感 |
| `repr+sha1+uuid` | `repr(normalized)` | SHA1->UUID | 標準 UUID 形式で出力 |
| `repr+blake2b16` | `repr(normalized)` | BLAKE2b(16B) | 高速 + 短いダイジェスト |
| `fast_mixed` | 型分岐（bytes/str/repr/pickle） | SHA1 | 基本型にはショートカット、複雑なオブジェクトには pickle にフォールバック |

## テストデータセット

11 種類の典型的なデータ形状をカバーします：`int`、`short_str`、`long_str_4k`、`bytes_4k`、`small_tuple`、`small_list`、`list_100_ints`、`small_dict`、`dict_100_pairs`、`nested_dict`、`set_100_ints`。

## 主要な実装

- `normalize_for_hash`：`set`、`dict`、`tuple`、`list`、`bytes` を安定した構造に変換します（キーのソート、型マーカー）
- `benchmark_one`：`timeit.repeat`（7 回繰り返し、各 10,000 回呼び出し）を使用し、GC を無効化して平均値と標準偏差を出力します

## 発生しうる問題

1. **pickle の不安定性**：同じオブジェクトでも異なる Python バージョンや実行間で `pickle.dumps` のバイト列が異なる場合があり（特に集合の順序）、ハッシュの不一致が発生します。**セッション間の重複排除には不適切です**。
2. **`fast_mixed` の型分岐の盲点**：`__repr__` が実装されていないカスタムクラスが渡された場合、`pickle.dumps` にフォールバックし、再び pickle の不安定性の問題に直面します。
3. **UUID 形式の衝突**：`repr+sha1+uuid` は SHA1 を 16 バイトに切り詰めてから UUID に変換します。確率は極めて低いですが、厳密には暗号学的安全性が失われます。
4. **大きなオブジェクトのメモリ負荷**：`long_str_4k` と `bytes_4k` は 10,000 回の繰り返しテスト中に一時的に大量のメモリを消費する場合があります。

## ベンチマーク結果（実測）

> 環境：Windows、Python 3.10、timeit repeat=7, number=10,000

### 総合ランキング（全データ型の平均）

| 方法 | 平均所要時間 | 特徴 |
|------|------------|------|
| `fast_mixed` | ~2.5 us | 基本型にショートカット、総合最速 |
| `pickle+blake2b16` | ~3.0 us | pickle シリアライゼーション + 高速ハッシュ |
| `pickle+sha1` | ~3.2 us | 安定、互換性良好 |
| `repr+blake2b16` | ~15 us | repr 正規化 + 高速ハッシュ |
| `json+md5` / `json+sha256` | ~25 us | クロス言語で安定しますが、最も低速 |
| `repr+sha1+uuid` | ~25 us | UUID 形式出力、追加の変換オーバーヘッドあり |

### 典型的なデータポイント（単位：マイクロ秒/回）

| ケース | 最速 | 最遅 | 最適な方法 |
|--------|------|------|----------|
| int | ~1.3 | ~4.3 | pickle+sha1 / fast_mixed |
| short_str | ~1.3 | ~4.2 | repr+blake2b16 / fast_mixed |
| long_str_4k | ~4.1 | ~23.5 | pickle+sha1 / fast_mixed |
| bytes_4k | ~3.6 | ~58.4 | **fast_mixed**（ネイティブ bytes サポート） |
| small_dict | ~1.9 | ~17.4 | pickle+blake2b16 |
| dict_100_pairs | ~7.8 | ~104.4 | pickle+sha1 / fast_mixed |
| list_100_ints | ~2.9 | ~36.0 | fast_mixed |
| set_100_ints | ~3.7 | ~43.1 | pickle+blake2b16 / fast_mixed |

**主要な結論**：
- `fast_mixed` は bytes と大きなコレクションにおいて絶対的な優位性があります（生のバイトを直接ハッシュし、シリアライゼーションを回避）
- `json+sha256` と `repr+sha1+uuid` はすべてのシナリオで pickle ベースの方法より大幅に低速であり、安定性/形式に対する強い要件がある場合のみ使用してください
- pickle ベースの方法は小さなオブジェクトで優れた性能を発揮します（1-3 us）が、pickle のセッション間安定性リスクに注意が必要です

## 実行方法

```bash
python bench/bench_hash.py
```

## 依存関係

- `celestialflow.format_table`
