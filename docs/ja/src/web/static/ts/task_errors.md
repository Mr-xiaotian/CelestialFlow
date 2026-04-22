# task_errors.ts

エラーログデータの読み込み、フィルタリング、ページネーション、レンダリングを管理します。

## グローバル変数

| 変数 | 型 | 説明 |
|------|------|------|
| `errors` | `any[]` | バックエンドから取得したエラーレコード配列 |
| `errorsOffset` | `number` | 同期済みエラー件数、増分取得に使用 |
| `currentPage` | `number` | 現在のページ番号、デフォルト 1 |
| `pageSize` | `number` | 1ページあたりの件数、10 固定 |

## 関数

### `loadErrors()`

`GET /api/pull_errors?offset=N` から非同期でエラーリストの増分を取得し、`errors` を更新します。

- `data.total < errorsOffset`（サーバー再起動後に error_store がクリアされた場合）は全量再同期を実行
- 新規エントリは `errors` の末尾に追加され、`true` を返します。新規データがなければ `false` を返します

---

### `renderErrors()`

エラーテーブルをレンダリングします。ステージフィルタリングとキーワード検索をサポートし、タイムスタンプ降順で並べ替えます。

**フィルタルール:**
- ステージフィルター: `e.stage === filter` に一致
- キーワード検索: `e.error_repr` または `e.task_repr` にあいまい一致（大文字小文字を区別しない）

テーブル列: エラーID、エラーメッセージ、ステージ、タスク、時刻。

---

### `buildPageList(current, total)`

スマートなページ番号配列を生成します。先頭ページと最終ページ、現在のページとその前後2ページを含み、間のギャップは `"..."` で埋めます。

---

### `renderPaginationControls(totalPages)`

「前へ」/「次へ」ボタンと数字ページボタンを含むページネーションコントロールをレンダリングします。1ページのみの場合、コントロールは非表示になります。

---

### `populateNodeFilter(statuses)`

`statuses`（`Record<string, NodeStatus>`）からステージ名を読み取り、フィルタードロップダウンを設定します。可能な限りユーザーの現在の選択を保持します。`main.ts` の `statusesChanged` 時に呼び出されます。

## イベントリスナー

- `searchInput` の `input` イベント → 1ページ目にリセットして再レンダリング
- `nodeFilter` の `change` イベント → 1ページ目にリセットして再レンダリング

## エラーレコードフィールド

| フィールド | 説明 |
|-----------|------|
| `error_id` | エラーID（整数） |
| `error_repr` | エラーメッセージ文字列 |
| `stage` | ステージタグ |
| `task_repr` | タスク内容文字列 |
| `ts` | エラータイムスタンプ（Unix 秒） |
