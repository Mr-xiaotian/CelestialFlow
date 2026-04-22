# utils.ts

すべてのフロントエンドモジュールで共有される汎用ユーティリティ関数集です。

## 関数一覧

### `renderLocalTime(timestamp)`

Unix タイムスタンプ（秒）をローカル時刻文字列に変換します。

```ts
renderLocalTime(1700000000) // → "2023/11/15 上午10:13:20"（ロケールによる）
```

---

### `formatLargeNumber(n)`

大きな数値を概算科学記数法の HTML にフォーマットします。10000 未満の数値はそのまま文字列として返します。

```ts
formatLargeNumber(1234567890) // → "~1.23×10<sup>9</sup>"
formatLargeNumber(999)        // → "999"
```

---

### `formatWithDelta(value, delta, deltaClass, negClass)`

値とその増分をフォーマットします。増分はカラーの小文字テキストで表示されます。

- `deltaClass`: 正の増分の CSS クラス名
- `negClass`: 負の増分の CSS クラス名

```ts
formatWithDelta(100, 5, "text-delta-success", "text-delta-success")
// → '100<small class="text-delta-success" style="margin-left: 4px;">+5</small>'
formatWithDelta(100, 0, ...)   // → '100'
```

HTML 文字列を返し、`innerHTML` に直接挿入できます。

---

### `getColor(index)`

インデックスを循環させて、事前定義された9色の16進カラーパレットから色を返します。折れ線グラフの各ノードの線の色付けに使用されます。

```ts
getColor(0) // → "#3b82f6"（青）
getColor(9) // → "#3b82f6"（循環）
```

---

### `extractProgressData(nodeHistories)`

ノード履歴データからチャート用の `{x, y}` ポイントシーケンスを抽出します。

- **入力**: `Record<string, NodeHistory>` -- ノード名 → 履歴レコード配列
- **出力**: `Record<string, Array<{x: number, y: number}>>` -- ノード名 → 座標ポイント配列
  - `x`: Unix タイムスタンプ（秒）
  - `y`: その時点での処理済みタスク数

---

### `isMobile()`

現在のデバイスがモバイルかどうかを検出します（User-Agent に基づく）。`boolean` を返します。モバイルデバイスでのドラッグ&ドロップソートの無効化に使用されます。

---

### `validateJSON(text)`

文字列が有効な JSON かどうかを検証します。

- 空文字列は有効とみなされます（`true` を返し、エラーメッセージを非表示）
- 解析失敗時に `showError("json-error", ...)` を呼び出してメッセージを表示し、`false` を返します

---

### `escapeHtml(str)`

HTML 特殊文字（`&`, `<`, `>`, `"`）をエスケープし、XSS を防止します。

```ts
escapeHtml('<script>') // → "&lt;script&gt;"
```

---

### `toggleDarkTheme()`

`document.body` の `dark-theme` CSS クラスを切り替えます。切り替え後にダークモードかどうか（`boolean`）を返します。

---

### `switchToErrorsTab(nodeFilter?)`

「エラーログ」タブに切り替え、オプションでステージフィルターを指定されたステージに設定します。引数なしまたは空文字列ですべてのエラーを表示します。

---

### `formatDuration(seconds)`

秒数を `HH:MM:SS` または `MM:SS` 文字列にフォーマットします。

```ts
formatDuration(90)    // → "01:30"
formatDuration(3661)  // → "01:01:01"
formatDuration(-5)    // → "00:00"
```

---

### `formatTimestamp(timestamp)`

Unix タイムスタンプ（秒）を `YYYY-MM-DD HH:MM:SS` 文字列にフォーマットします。

```ts
formatTimestamp(1700000000) // → "2023-11-15 10:13:20"
```
