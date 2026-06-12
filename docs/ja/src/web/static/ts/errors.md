# errors.ts

> 📅 最終更新日: 2026/06/11

エラーログのページネーション取得、キーワード検索、ノードフィルタリング、ソート切り替え、テーブルレンダリング、およびタスク再注入機能を管理します。

> ⚠️ **変更済み**: エラーレコードフィールドが再構築されました（`error_id` が数値型に、`error_type`/`error_message` が新設、`task` は `unknown` 型）。ソート切り替え、再注入（retry）インタラクション列が新たに追加されました。

## 型定義

```typescript
type ErrorData = {
  ts: number;            // エラー発生タイムスタンプ、単位は秒
  stage: string;         // エラー発生ノード/ステージ名、ノードフィルタリングに使用
  error_id: number;      // エラーの一意識別 ID、グローバルで一意
  error_type: string;    // エラーの分類タイプ、異なるカテゴリのエラーを区別
  error_message: string; // エラーの具体的な説明情報
  task: unknown;         // このエラーをトリガーしたタスクデータ、表示とリトライ再投入に使用
};
```

## グローバル変数

| 変数 | 型 | 説明 |
|------|------|------|
| `errors` | `ErrorData[]` | 現在のページのエラーレコードリスト |
| `currentPage` | `number` | 現在表示中のページ番号、1 から開始 |
| `pageSize` | `number` | ページあたり表示レコード数、`webConfig` から同期 |
| `errorSortOrder` | `"newest" \| "oldest"` | エラーログソート方向、デフォルト `"newest"` |
| `totalPages` | `number` | バックエンドが計算した総ページ数 |
| `errorsRev` | `number` | データバージョン番号、初期値 `-1`、増分取得に使用 |
| `lastQueryKey` | `string` | 前回クエリのキャッシュキー、フィルター条件の変化判定に使用 |
| `errorsRequestSeq` | `number` | リクエストシーケンス番号、古いリクエストが新しい結果を上書きするのを防止 |

## DOM 要素参照

| 変数 | DOM セレクタ | 説明 |
|------|-----------|------|
| `searchInput` | `#error-search` | 検索キーワード入力ボックス |
| `nodeFilter` | `#node-filter` | ノードフィルタードロップダウン |
| `errorSortSelect` | `#error-sort-order` | ソート方法ドロップダウン |
| `errorsTableBody` | `#errors-table tbody` | エラーテーブル tbody |
| `paginationContainer` | `#pager-container` | ページネーションコントロールコンテナ |

## 関数

### `buildErrorsQueryKey(page, pageSizeValue, node, keyword, sortOrder): string`

エラークエリのキャッシュキー文字列を構築します。パラメータに `sortOrder`（新旧）を含み、`lastQueryKey` と連携してフィルター条件の変化を判定します。

---

### `loadErrors(forceReload?: boolean): Promise<boolean>`

非同期でエラーログデータを取得します。

- **クエリパラメータ**: `known_rev`, `page`, `page_size`, `node`, `keyword`, `sort_order`
- **競合保護**: `errorsRequestSeq` を使用して古いリクエストの結果が新しいリクエストを上書きしないようにします。
- **強制再読み込み**: `forceReload=true` またはフィルター条件が変化した場合、`known_rev` 増分メカニズムを無視します。
- **API エンドポイント**: `GET /api/pull_errors?{params}`

---

### `renderErrors(): void`

`errors` データを `#errors-table` テーブルにレンダリングします。

**テーブル列（全 7 列）：**

| # | 列名 (i18n key) | 説明 |
|---|----------------|------|
| 1 | `#` | グローバル表示連番（ページ番号に基づいて計算） |
| 2 | `errors.colId` | エラー ID |
| 3 | `errors.colMessage` | エラーメッセージ（`format_repr` で 50 文字に切り詰め、ホバーで全文表示） |
| 4 | `errors.colNode` | ノード名 |
| 5 | `errors.colTask` | タスクデータ（切り詰め表示） |
| 6 | `errors.colTime` | 発生時刻（`formatTimestamp` でフォーマット） |
| 7 | `errors.colRetry` | 再注入操作：`.retry-link`（再試行可能）または `.retry-disabled`（使用不可） |

> 第 7 列（再注入）：`task` が存在しプレースホルダーでない場合、クリック/キーボードで `preloadInjectionDraftFromError(stage, task, jumpToInjectionAfterRetry)` の呼び出しをトリガーし、注入ページにジャンプしてタスクデータを事前入力できます。

---

### `goToErrorsPage(nextPage: number): Promise<void>`

ページネーションジャンプロジック。ページ番号を `[1, totalPages]` の範囲に制限した後、`loadErrors(true)` をトリガーして再取得します。

---

### `buildPageList(current: number, total: number): Array<number | string>`

ページネーション番号リストを生成し、先頭・末尾ページ、現在のページ、前後 2 ページを含み、自動的に省略記号 `"…"` を挿入します。

---

### `renderPaginationControls(totalPages: number): void`

ページネーションコントロール（前へ/次へボタン + 数字ページ番号シーケンス）をレンダリングします。総ページ数 ≤ 1 の場合はレンダリングしません。

---

### `populateNodeFilter(statuses: Record<string, NodeStatus>): void`

ダッシュボードのノード状態に基づいて、エラーページの「ノードでフィルター」ドロップダウンを動的に更新します。ユーザーの現在のフィルター条件を可能な限り保持します。

---

## イベントバインディング（モジュールレベルで自動実行）

| 対象要素 | イベント | 動作 |
|----------|------|------|
| `searchInput` | `input` | 1 ページ目にリセット、強制再読み込み、テーブルレンダリング |
| `nodeFilter` | `change` | 1 ページ目にリセット、強制再読み込み、テーブルレンダリング |
| `errorSortSelect` | `change` | `errorSortOrder` と `webConfig` を更新、1 ページ目にリセット、再読み込みして設定保存 |

## 使用例

```typescript
// エラーレコードをシミュレート
const mockErrors: ErrorData[] = [
  { ts: 1745400100, stage: "StageA", error_id: 1001, error_type: "TimeoutError", error_message: "Connection timeout", task: { id: 1 } },
  { ts: 1745400050, stage: "StageB", error_id: 1002, error_type: "ValueError", error_message: "Invalid value", task: "task_data" },
];

// errors = mockErrors;
// currentPage = 1;
// totalPages = 5;
// renderErrors();        // テーブルをレンダリング
// renderPaginationControls(5); // ページネーションをレンダリング

// 3 ページ目にジャンプ
// await goToErrorsPage(3);

// 他のタブからエラーログにジャンプして自動フィルタリング
// switchToErrorsTab("StageA");
```

## データフロー

```mermaid
flowchart LR
    subgraph "main.ts"
        RA[refreshAll]
    end
    subgraph "errors.ts"
        LE[loadErrors]
        QK[buildErrorsQueryKey]
        RE[renderErrors]
        RP[renderPaginationControls]
    end
    subgraph "API"
        API[/api/pull_errors]
    end
    subgraph "DOM"
        TB[#errors-table]
        PG[#pager-container]
    end

    RA --> LE
    LE --> QK
    LE --> API
    API --> LE
    LE --> RE
    RE --> TB
    RE --> RP
    RP --> PG
```
