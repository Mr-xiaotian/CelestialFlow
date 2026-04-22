# task_injection.ts

タスクインジェクションページのロジックです。ステージの選択、タスクデータの入力（JSON テキストまたはファイルアップロード）、バックエンドへの送信をサポートします。

## 型定義

```ts
type SelectedNode = { name: string; type: string; status?: number };
```

## グローバル変数

| 変数 | 型 | 説明 |
|------|------|------|
| `selectedNodes` | `SelectedNode[]` | 現在選択中のステージリスト |
| `currentInputMethod` | `string` | 現在の入力方法: `"json"` または `"file"` |
| `uploadedFile` | `{name, content} \| null` | アップロード済み JSON ファイルの内容 |

## 関数

### `setupEventListeners()`

ページイベントをバインドします: 検索ボックス入力、JSON テキストエリアのリアルタイムバリデーション、ファイル選択、送信ボタン。

---

### `renderNodeList(searchTerm?)`

ステージ選択リストをレンダリングします。

- `searchTerm` に基づいてステージ名をフィルタリング
- `nodeStatuses` からステージ状態を読み取りバッジをレンダリング
- ステータスが `2`（停止済み）のステージはクリック不可（`disabled-node` スタイル）

---

### `selectNode(nodeName)` / `removeNode(nodeName)`

ステージの選択状態を切り替え（選択済みステージの再クリックで選択解除）、`updateSelectedNodes()` を呼び出して選択リスト UI を更新します。

---

### `selectAllNodes()`

`status !== 2` のすべてのステージを全選択します（停止済みステージを除く）。

---

### `clearSelection()`

選択済みステージをすべてクリアします。

---

### `switchInputMethod(method)`

入力方法を切り替え（`"json"` / `"file"`）、対応するエリアの表示/非表示とボタンのアクティブ状態を更新します。

---

### `fillTermination()`

JSON テキストエリアに事前定義された終了信号 `["TERMINATION_SIGNAL"]` を入力します。ユーザーが素早く終了信号をインジェクションできるようにします。

---

### `handleFileUpload(e)`

ファイルアップロードを処理します: `.json` 形式のみ受け付け、JSON の妥当性を読み取り・検証し、`uploadedFile` に保存します。

---

### `handleSubmit()`

タスクインジェクションを送信します。

1. 選択済みステージを検証（少なくとも1つ必要）
2. 入力方法に基づいてタスクデータを解析
3. 選択された各ステージに対して `/api/push_injection_tasks` に POST し、すべて完了後に成功メッセージを表示
4. `clearForm()` を呼び出してフォームをリセット

---

### ヘルパー関数

| 関数 | 説明 |
|------|------|
| `showError(elementId, message)` | エラーメッセージテキストを表示 |
| `hideError(elementId)` | エラーメッセージを非表示 |
| `showStatus(message, isSuccess)` | 操作結果メッセージを表示（3秒後に自動非表示） |
| `setButtonLoading(loading)` | 送信ボタンのローディング状態を切り替え |
| `clearForm()` | すべての選択、入力、エラーメッセージをリセット |

## タスクインジェクションリクエストボディ

```json
{
    "node": "stage_tag",
    "task_datas": [...],
    "timestamp": "2024-01-01T00:00:00.000Z"
}
```

`POST /api/push_injection_tasks` に送信されます。サーバーは `injection_tasks` キューに保存し、`TaskReporter` が `GET /api/pull_task_injection` で定期的に取得して `TaskGraph` にインジェクションします。
