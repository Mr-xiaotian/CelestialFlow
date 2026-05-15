# utils.ts

> 📅 最終更新日: 2026/05/15

すべてのフロントエンドモジュールで共有される汎用ユーティリティ関数コレクション。

## 関数一覧

### `renderLocalTime(timestamp)`

Unix タイムスタンプ（秒）をローカル時間文字列に変換します。

```ts
renderLocalTime(1700000000) // → "2023/11/15 上午10:13:20"（ロケールにより異なる）
```

---

### `formatLargeNumber(n)`

大きな数値を概算科学的記数法の HTML にフォーマットします。1000 万未満の数はカンマ区切り、1000 万以上の数は科学的記数法に変換します。

```ts
formatLargeNumber(1234567890) // → "~1.23×10<sup>9</sup>"
formatLargeNumber(999)        // → "999"
```

---

### `formatWithDelta(value, delta, deltaClass, negClass)`

値とその差分をフォーマットし、差分をカラー付き小文字で表示します。

- `deltaClass`: 正の差分の CSS クラス名
- `negClass`: 負の差分の CSS クラス名

```ts
formatWithDelta(100, 5, "text-delta-success", "text-delta-success")
// → '100<small class="text-delta-success" style="margin-left: 4px;">+5</small>'
formatWithDelta(100, 0, ...)   // → '100'
```

HTML 文字列を返し、`innerHTML` に直接挿入します。

---

### `getColor(index)`

インデックスに基づいて事前定義された 9 色の 16 進カラーを循環して返します。折れ線グラフの各ノード線の着色に使用します。

```ts
getColor(0) // → "#3b82f6"（青）
getColor(9) // → "#3b82f6"（循環）
```

---

### `extractProgressData(nodeHistories)`

ノード履歴データからチャート用の `{x, y}` ポイントシーケンスを抽出します。

- **入力**: `Record<string, NodeHistory>` — ノード名 → 履歴レコード配列
- **出力**: `Record<string, Array<{x: number, y: number}>>` — ノード名 → 座標ポイント配列
  - `x`: Unix タイムスタンプ（秒）
  - `y`: その時点での処理済みタスク数

---

### `isMobile()`

現在のデバイスがモバイルかどうかを検出します（User-Agent ベース）。`boolean` を返します。モバイルデバイスでドラッグ＆ドロップソートを無効にするために使用します。

---

### `validateJSON(text)`

文字列が有効な JSON かどうかを検証します。

- 空文字列は有効と見なされます（`true` を返し、エラープロンプトを非表示）
- パース失敗時は `showError("json-error", ...)` を呼び出してプロンプトを表示し、`false` を返します

---

### `escapeHtml(str)`

HTML 特殊文字（`&`、`<`、`>`、`"`、`'`、`/`）をエスケープし、XSS を防止します。

```ts
escapeHtml('<script>') // → "&lt;script&gt;"
```

---

### `toggleDarkTheme()`

`document.body` の `dark-theme` CSS クラスを切り替えます。切り替え後にダークモードがアクティブかどうか（`boolean`）を返します。

---

### `switchToErrorsTab(nodeFilter?)`

「エラーログ」タブに切り替え、オプションでノードフィルタを指定ノードに設定します。引数なしまたは空文字列を渡すとすべてのエラーを表示します。

---

### `formatDuration(seconds)`

秒数を `HH:MM:SS` または `MM:SS` 文字列にフォーマットします。

```ts
formatDuration(90)    // → "01:30"
formatDuration(3661)  // → "01:01:01"
formatDuration(-5)    // → "00:00"
```

---

### `formatElapsedDuration(seconds, successCount, failedCount, duplicateCount)`

経過時間をカラー付き HTML 文字列にフォーマットします。各数字文字は `<span>` で囲まれ、成功/失敗/重複のタスク比率に応じてカラークラスが割り当てられます。

内部呼び出しチェーン：`getElapsedSegments()` → `buildElapsedDigitClasses()` → `renderElapsedDurationHtml()`。

---

### `formatTimestamp(timestamp)`

Unix タイムスタンプ（秒）を `YYYY-MM-DD HH:MM:SS` 文字列にフォーマットします。

```ts
formatTimestamp(1700000000) // → "2023-11-15 10:13:20"
```
