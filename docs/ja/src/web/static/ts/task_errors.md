# task_errors.ts

> 📅 最終更新日: 2026/05/15

エラーログデータの読み込み、サーバーサイドページネーション/フィルタリング、レンダリングを管理します。

## グローバル変数

| 変数 | 型 | 説明 |
|------|------|------|
| `errors` | `any[]` | 現在のページのエラーレコード配列、バックエンドから取得 |
| `currentPage` | `number` | 現在のページ番号、デフォルト 1 |
| `pageSize` | `number` | ページあたりの件数、10 で固定 |
| `totalPages` | `number` | 総ページ数、バックエンドから返される |
| `errorsRev` | `number` | 前回取得時のバージョン番号、増分取得（`known_rev`）に使用 |
| `lastQueryKey` | `string` | 前回のクエリキャッシュキー、フィルタ条件の変化検出に使用 |
| `errorsRequestSeq` | `number` | リクエストシーケンス番号、古いリクエストが新しい結果を上書きするのを防止 |

## DOM 要素参照

| 変数 | セレクタ | 説明 |
|------|----------|------|
| `searchInput` | `#error-search` | キーワード検索ボックス |
| `nodeFilter` | `#node-filter` | ノードフィルタドロップダウン |
| `errorsTableBody` | `#errors-table tbody` | エラーテーブル本体 |
| `paginationContainer` | `#pager-container` | ページネーションコントロールコンテナ |

## 関数

### `buildErrorsQueryKey(page, pageSize, node, keyword)`

ページネーションとフィルタパラメータをキャッシュキー文字列（`page|pageSize|node|keyword`）に組み合わせ、クエリ条件の変化を検出するために使用します。

---

### `loadErrors(forceReload?)`

`GET /api/pull_errors` から非同期でエラーデータを取得し、サーバーサイドページネーションとフィルタリングをサポートします。

**リクエストパラメータ：**

| パラメータ | 説明 |
|-----------|------|
| `known_rev` | バージョン番号。フィルタ条件が変化するか `forceReload` 時に -1 にリセット |
| `page` | 現在のページ番号 |
| `page_size` | ページあたりの件数 |
| `node` | ノードフィルタ値 |
| `keyword` | 検索キーワード |

**競合状態保護：** `errorsRequestSeq` のインクリメントシーケンス番号を使用。レスポンス到着時にシーケンス番号の一致を検証し、期限切れのレスポンスを破棄します。

---

### `renderErrors()`

エラーテーブルをレンダリングします。列：番号、エラー ID、エラーメッセージ、ノード、タスク、時間。データがない場合はプレースホルダーメッセージを表示します。

---

### `goToErrorsPage(nextPage)`

指定ページに移動し、`loadErrors(true)` を呼び出して強制リロードと再レンダリングを実行します。

---

### `buildPageList(current, total)`

スマートページ番号配列を生成します。先頭と末尾のページ、現在のページとその前後 2 ページを含み、間のギャップは `"..."` で埋めます。

---

### `renderPaginationControls(totalPages)`

ページネーションコントロールをレンダリングします。「前へ」/「次へ」ボタンと数字ページボタンを含みます。1 ページのみの場合はコントロールを非表示にします。

---

### `populateNodeFilter(statuses)`

`statuses`（`Record<string, NodeStatus>`）からノード名を読み取ってフィルタドロップダウンを設定し、可能な限りユーザーの現在の選択を保持します。`main.ts` で `statusesChanged` 時に呼び出されます。

## イベントリスナー

- `searchInput` の `input` イベント → 1 ページ目にリセット、強制リロードと再レンダリング
- `nodeFilter` の `change` イベント → 1 ページ目にリセット、強制リロードと再レンダリング

## エラーレコードフィールド

| フィールド | 説明 |
|-----------|------|
| `error_id` | エラー ID（整数） |
| `error_repr` | エラーメッセージ文字列 |
| `stage` | 所属ノード tag |
| `task_repr` | タスク内容文字列 |
| `ts` | エラータイムスタンプ（Unix 秒） |
