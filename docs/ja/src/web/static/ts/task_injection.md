# task_injection.ts

> 📅 最終更新日: 2026/04/22

タスクインジェクションページのロジック。ノード選択、タスクデータ入力（JSON テキストまたはファイルアップロード）、バックエンドへの送信をサポートします。

## 型定義

```ts
type SelectedNode = { name: string; type: string; status?: number };
```

## グローバル変数

| 変数 | 型 | 説明 |
|------|------|------|
| `selectedNodes` | `SelectedNode[]` | 現在選択されているノードリスト |
| `currentInputMethod` | `string` | 現在の入力方法：`"json"` または `"file"` |
| `uploadedFile` | `{name, content} \| null` | アップロードされた JSON ファイルの内容 |

## 関数

### `setupEventListeners()`

ページイベントをバインド：検索ボックス入力、JSON テキストエリアのリアルタイム検証、ファイル選択、送信ボタン。

---

### `renderNodeList(searchTerm?)`

ノード選択リストをレンダリングします。

- `searchTerm` に基づいてノード名をフィルタリング
- `nodeStatuses` からノードステータスを読み取り、バッジをレンダリング
- ステータスが `2`（停止済み）のノードはクリック不可（`disabled-node` スタイル）

---

### `selectNode(nodeName)` / `removeNode(nodeName)`

ノードの選択状態を切り替え（選択済みノードの再クリックで選択解除）、`updateSelectedNodes()` を呼び出して選択リスト UI を更新します。

---

### `selectAllNodes()`

`status !== 2` のすべてのノードを全選択（停止済みノードを除外）。

---

### `clearSelection()`

選択されたすべてのノードをクリアします。

---

### `switchInputMethod(method)`

入力方法を切り替え（`"json"` / `"file"`）、対応するエリアの表示/非表示とボタンのアクティブ状態を更新します。

---

### `fillTermination()`

JSON テキストエリアに事前定義の終了シグナル `["TERMINATION_SIGNAL"]` を入力し、ユーザーが素早く終了シグナルを注入できるようにします。

---

### `handleFileUpload(e)`

ファイルアップロードを処理：`.json` 形式のみ受け付け、JSON の妥当性を読み取り・検証し、`uploadedFile` に保存します。

---

### `handleSubmit()`

タスクインジェクションを送信します。

1. 選択されたノードを検証（最低 1 つ）
2. 入力方法に基づいてタスクデータを解析
3. 選択された各ノードに対して順次 `/api/push_injection_tasks` に POST し、すべて完了後に成功メッセージを表示
4. `clearForm()` を呼び出してフォームをリセット

---

### ヘルパー関数

| 関数 | 説明 |
|------|------|
| `showError(elementId, message)` | エラープロンプトテキストを表示 |
| `hideError(elementId)` | エラープロンプトを非表示 |
| `showStatus(message, isSuccess)` | 操作結果メッセージを表示（3 秒後に自動非表示） |
| `setButtonLoading(loading)` | 送信ボタンのローディング状態を切り替え |
| `clearForm()` | すべての選択、入力、エラープロンプトをリセット |

## タスクインジェクションリクエストボディ

```json
{
    "node": "stage_tag",
    "task_datas": [...],
    "timestamp": "2024-01-01T00:00:00.000Z"
}
```

`POST /api/push_injection_tasks` に送信されます。サーバーは `injection_tasks` キューに格納し、`TaskReporter` が `GET /api/pull_task_injection` を通じて定期的に取得して `TaskGraph` に注入します。
