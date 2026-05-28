# errors.ts

> 📅 最終更新日: 2026/05/28

エラーログのページネーション取得、キーワード検索、ノードフィルタリング、テーブルレンダリングを管理します。

## グローバル変数

| 変数 | 型 | 説明 |
|------|------|------|
| `errors` | `any[]` | 現在のページのエラーレコードリスト |
| `currentPage` | `number` | 現在表示されているページ番号。1 から開始 |
| `pageSize` | `number` | 1ページあたりの表示件数。`webConfig` から同期 |
| `totalPages` | `number` | バックエンドが計算した総ページ数 |
| `errorsRev` | `number` | データバージョン番号。増分取得の判断に使用 |

## 関数

### `buildErrorsQueryKey(page, pageSizeValue, node, keyword)`

エラークエリのキャッシュキー文字列を構築し、フィルタ条件が変更されたかどうかを判断して強制再取得が必要かを決定します。

- **パラメータ**: 現在のページ番号、ページサイズ、ノードフィルタ、検索キーワード
- **戻り値**: `|` で区切られた結合文字列（例: `"1|10|StageA|timeout"`）
- `lastQueryKey` と組み合わせてクエリキャッシュの比較に使用

---

### `buildPageList(current, total)`

ページネーション番号リストを生成し、先頭・末尾ページ、現在ページとその前後ページを含み、ジャンプ箇所に省略記号（`…`）を自動挿入します。

- **パラメータ**: `current` 現在のページ番号、`total` 総ページ数
- **戻り値**: `Array<number | string>`、数値ページ番号または省略記号文字列
- `renderPaginationControls()` 内部でページ番号ナビゲーションを生成するために使用

---

### `loadErrors(forceReload)`

エラーログデータを非同期で取得。`known_rev` に基づく増分取得をサポート。

- **パラメータ**: `forceReload`（オプション）- `true` の場合、キャッシュを無視して強制再取得（検索条件変更時など）。
- **クエリパラメータ**: `page`, `page_size`, `node`（ノードフィルタ）, `keyword`（あいまい検索）。
- **競合状態保護**: `errorsRequestSeq` を使用して、古いリクエストの結果が新しいものを上書きしないよう保証。

---

### `renderErrors()`

`errors` データを `#errors-table` テーブルにレンダリングし、`renderPaginationControls()` を呼び出してページネーションバーを更新します。

**テーブル列:**
1. 番号（ページ番号から計算）
2. エラー ID
3. エラー情報（オーバーフロー時に省略記号表示、ホバーで全文表示）
4. ノード（ノードタグ）
5. タスク（タスク表現）
6. 時間（ローカルフォーマット時間）

---

### `goToErrorsPage(nextPage)`

ページネーションジャンプロジック。`loadErrors(true)` をトリガーして特定ページのデータを再取得。

---

### `populateNodeFilter(statuses)`

ダッシュボードのノード状態に基づいて、エラーページの「ノードでフィルタ」ドロップダウンを動的に更新。

---

### `renderPaginationControls(totalPages)`

ページネーションコントロールをレンダリング。前へ/次へボタンと省略記号付きの数字ページシーケンスを含む。

## インタラクティブ機能

- **検索連動**: 検索ボックス入力またはノードフィルタ変更時に `currentPage` をリセットし強制リフレッシュ。
- **レスポンシブ対応**: 小画面デバイスでは、エラーテーブルが自動的にカードスタイルレイアウトに切り替わります（`errors.css` メディアクエリによる）。
- **外部ナビゲーション**: グローバル関数 `switchToErrorsTab(node?)`（`utils.ts` で定義）により、ダッシュボードカードからワンクリックでエラーログタブにジャンプし、フィルタ条件を自動入力。

## 使用例

### エラーデータの形式と処理

以下の例はエラーログのデータ構造とブラウザコンソールでの手動操作方法を示します：

```typescript
// 1. エラーレコードのデータ構造（バックエンドから）
const errorRecord = {
    ts: 1745400000,           // タイムスタンプ（秒）
    error_id: "err_001",     // エラー ID
    error_repr: "30秒後に接続タイムアウト",  // エラー説明
    error: {                  // 生のエラーオブジェクト
        type: "TimeoutError",
        message: "30秒後に接続タイムアウト",
        stack: "...",
    },
    stage: "DataLoader",     // 所属ノード
    task_repr: "file_123.json", // タスク識別子
};

// 2. エラーデータのバッチをシミュレート
const mockErrors = [
    { ts: 1745400100, error_id: "E001", error_repr: "接続タイムアウト", stage: "StageA", task_repr: "task_1", error: {} },
    { ts: 1745400050, error_id: "E002", error_repr: "メモリ不足", stage: "StageB", task_repr: "task_5", error: {} },
    { ts: 1745400000, error_id: "E003", error_repr: "ファイルが見つかりません", stage: "StageA", task_repr: "task_2", error: {} },
    { ts: 1745399950, error_id: "E004", error_repr: "権限不足", stage: "StageC", task_repr: "task_3", error: {} },
];

// 3. 手動でエラーレンダリングを呼び出し
// グローバル変数を使用:
// errors = mockErrors;
// currentPage = 1;
// renderErrors();
// これにより #errors-table に列: 番号、エラーID、エラー情報、ノード、タスク、時間 でレンダリング

// 4. ページナビゲーション
// goToErrorsPage(2);  // 2ページ目にジャンプ、loadErrors(true) をトリガー

// 5. URL パラメータを使用して手動でエラーを取得
async function fetchErrorsManually(page: number, pageSize: number, node?: string, keyword?: string) {
    const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
    });
    if (node) params.set("node", node);
    if (keyword) params.set("keyword", keyword);

    const res = await fetch(`/api/pull_errors?${params}`);
    const data = await res.json();
    return data;
}

// 例: StageA の最初の5件のエラーを取得
// fetchErrorsManually(1, 5, "StageA").then(data => console.log(data));

// 6. ページネーションコントロールのレンダリング
// renderPaginationControls(totalPages);
// 例: totalPages が 5 の場合: < 1 2 3 4 5 > を生成

// 7. 別タブからエラーログに自動フィルタ付きでジャンプ
// switchToErrorsTab("StageA");
// これにより:
//   - エラーログタブに切り替え
//   - ノードフィルタドロップダウンを "StageA" に設定
//   - クエリをトリガー
```
