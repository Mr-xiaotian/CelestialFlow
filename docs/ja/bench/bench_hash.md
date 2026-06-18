# bench_hash.py ベンチマーク説明

> 📅 最終更新日: 2026/06/16

## 目的

9 種類のオブジェクト→ハッシュ文字列のシリアライズ＋ハッシュ戦略を体系的に比較し、`TaskEnvelope` の重複排除および追跡 ID 生成に最適な方式を選定する。評価軸は速度、安定性、衝突率、異なるデータ型への対応度。

## テスト戦略

| 方式 | シリアライズ方式 | ハッシュアルゴリズム | 特徴 |
|------|-----------------|---------------------|------|
| `pickle+md5` | `pickle.dumps` | MD5 | 任意のオブジェクトに対応、ただし非安定（プロトコルバージョンに敏感） |
| `pickle+sha1` | `pickle.dumps` | SHA1 | 同上、より長いダイジェスト |
| `pickle+blake2b16` | `pickle.dumps` | BLAKE2b(16B) | より高速、短いダイジェスト |
| `json+md5` | カスタム JSON | MD5 | 言語間で安定、ただし JSON シリアライズ可能な型のみ対応 |
| `json+sha256` | カスタム JSON | SHA256 | より安全、ただしより低速 |
| `repr+md5` | `repr(normalized)` | MD5 | 可読性が高い、ただし `set`/`dict` の順序に敏感 |
| `repr+sha1+uuid` | `repr(normalized)` | SHA1→UUID | 標準 UUID にフォーマット |
| `repr+blake2b16` | `repr(normalized)` | BLAKE2b(16B) | 高速 + 短いダイジェスト |
| `fast_mixed` | 型分岐（bytes/str/repr/pickle） | SHA1 | 基本型ではショートカット、複雑オブジェクトでは pickle にフォールバック |

## テストデータセット

11 種類の典型的なデータ形状をカバー：`int`、`short_str`、`long_str_4k`、`bytes_4k`、`small_tuple`、`small_list`、`list_100_ints`、`small_dict`、`dict_100_pairs`、`nested_dict`、`set_100_ints`。

## 主要実装

- `normalize_for_hash`：`set`、`dict`、`tuple`、`list`、`bytes` を安定構造に変換（キーソート、型マーキング）
- `benchmark_one`：`timeit.repeat`（7 回繰り返し、各回 10,000 回呼び出し）を使用、GC 無効化、平均と標準偏差を出力

## 発生し得る問題

1. **pickle の不安定性**：同一オブジェクトでも Python バージョンや実行ごとに `pickle.dumps` のバイトが異なる可能性があり（特に集合の順序）、ハッシュが不一致になる。**クロスセッション重複排除には不適**。
2. **`fast_mixed` の型分岐ブラインドスポット**：カスタムクラスが渡され `__repr__` が未実装の場合、`pickle.dumps` にフォールバックし、再び pickle の不安定性問題に直面する。
3. **UUID フォーマットの衝突**：`repr+sha1+uuid` は SHA1 を 16 バイトに切り詰めて UUID に変換する。確率は極めて低いが、厳密には暗号学的安全性が損なわれる。
4. **大規模オブジェクトのメモリ圧力**：`long_str_4k`、`bytes_4k` は 10,000 回の繰り返しテスト中に一時的に大量のメモリを消費する可能性がある。

## ベンチマーク結果（実測）

### 履歴結果 - Windows ハッシュ方式比較（日時未記録）

> 環境：Windows、Python 3.10、timeit repeat=7, number=10,000

#### 総合ランキング（全データ型平均）

| 方式 | 平均所要時間 | 特徴 |
|------|-------------|------|
| `fast_mixed` | ~2.5 us | 基本型でショートカット、総合最速 |
| `pickle+blake2b16` | ~3.0 us | pickle シリアライズ + 高速ハッシュ |
| `pickle+sha1` | ~3.2 us | 安定、互換性良好 |
| `repr+blake2b16` | ~15 us | repr 正規化 + 高速ハッシュ |
| `json+md5` / `json+sha256` | ~25 us | 言語間で安定、ただし最遅 |
| `repr+sha1+uuid` | ~25 us | UUID フォーマット出力、追加変換オーバーヘッドあり |

### 典型的データポイント（単位：マイクロ秒/回）

| ケース | 最良 | 最悪 | 最適方式 |
|--------|------|------|----------|
| int | ~1.3 | ~4.3 | pickle+sha1 / fast_mixed |
| short_str | ~1.3 | ~4.2 | repr+blake2b16 / fast_mixed |
| long_str_4k | ~4.1 | ~23.5 | pickle+sha1 / fast_mixed |
| bytes_4k | ~3.6 | ~58.4 | **fast_mixed**（bytes をネイティブサポート） |
| small_dict | ~1.9 | ~17.4 | pickle+blake2b16 |
| dict_100_pairs | ~7.8 | ~104.4 | pickle+sha1 / fast_mixed |
| list_100_ints | ~2.9 | ~36.0 | fast_mixed |
| set_100_ints | ~3.7 | ~43.1 | pickle+blake2b16 / fast_mixed |

**主要な結論**：
- `fast_mixed` は bytes と大規模集合に対して絶対的優位（生バイトを直接ハッシュし、シリアライズを回避）
- `json+sha256` と `repr+sha1+uuid` は全シナリオで pickle 方式より顕著に遅く、安定性/フォーマットへの強い要求がある場合のみ使用
- pickle シリーズの方式は小規模オブジェクトで優れた性能（1-3 us）、ただし pickle のクロスセッション安定性リスクに注意

### 2026/06/16 - ローカル再テスト

> 環境：Windows、現在の出力形式は case ごとに項目表示。下表は代表的な case を抜粋（単位：マイクロ秒/回）

#### 代表的なデータポイント（今回）

| Case | 最適方式 | 最適所要時間 | 次点の観察 |
|------|----------|----------|----------|
| `int` | `repr+blake2b16` | 0.872 us | `fast_mixed` 0.970 us |
| `short_str` | `fast_mixed` | 0.760 us | `repr+blake2b16` 0.863 us |
| `long_str_4k` | `fast_mixed` | 2.535 us | `pickle+sha1` 3.320 us |
| `bytes_4k` | `fast_mixed` | 2.347 us | `pickle+sha1` 3.328 us |
| `small_dict` | `pickle+blake2b16` | 1.742 us | `fast_mixed` 2.170 us |
| `dict_100_pairs` | `pickle+sha1` | 6.456 us | `fast_mixed` 6.842 us |
| `set_100_ints` | `pickle+sha1` | 3.104 us | `pickle+blake2b16` 3.139 us |

**今回の補足結論**：
- `fast_mixed` は文字列と大規模バイト列で引き続き明らかな優位性を維持。特に `long_str_4k` と `bytes_4k`
- `pickle` 系列は中〜大規模コンテナオブジェクトで引き続き安定してリード。特に `dict`、`set`、`tuple/list` といった複合構造
- `json` と `repr+sha1+uuid` は依然として顕著に遅く、安定性やフォーマット優先時の代替案としてより適しており、純粋な性能方案ではない

## 実行方法

```bash
python bench/bench_hash.py
```

## パラメータ調整

### 特定ハッシュ方式のみをテスト

`bench/bench_hash.py` では、テスト方式とデータセットがそれぞれ `METHODS` 辞書と `TEST_CASES` 辞書で定義されている。一時的にコメントアウトして特定方式を選択できる：

```python
METHODS: dict[str, Callable[[Any], str]] = {
    # "pickle+md5": method_pickle_md5,
    # "pickle+sha1": method_pickle_sha1,
    "json+md5": method_json_md5,        # JSON 方式のみテスト
    "json+sha256": method_json_sha256,   # JSON 方式のみテスト
    # "repr+md5": method_repr_md5,
    # ...
}
```

### 特定データ型のみをテスト

```python
TEST_CASES = {
    "int": 123456789,
    "short_str": "celestialflow",
    "long_str_4k": "x" * 4096,     # 大規模文字列のみテスト
    # "bytes_4k": b"x" * 4096,
    # ...
}
```

### timeit 繰り返し回数の調整

```python
# 繰り返しを減らして素早く検証（結果の安定性は低下）
# benchmark_one の呼び出し箇所で repeat と number を渡す
mean_us, std_us = benchmark_one(func, obj, repeat=3, number=1000)
# デフォルトは repeat=7, number=10000
```

修正後に実行：

```bash
python bench/bench_hash.py
```

## 依存関係

- `celestialflow.format_table`
