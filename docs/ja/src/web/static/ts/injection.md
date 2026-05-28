# injection.ts

> 📅 最終更新日: 2026/05/28

タスク手動注入ページのロジックを管理します。マルチノード選択、JSON テキスト入力、JSON ファイルアップロード、終了シグナルのクイック入力、注入送信をサポートします。

## グローバル変数

| 変数 | 型 | 説明 |
|------|------|------|
| `selectedNodes` | `{ name: string }[]` | ユーザーが現在選択している注入ターゲットノードのリスト。各ノードは `name` フィールドのみを含む |
| `currentInputMethod` | `string` | 現在の入力モード: `json` または `file` |
| `uploadedFile` | `object \| null` | アップロードされたファイルの名前と内容を保存 |

## 関数

### `setupEventListeners()`

**イベント委譲**パターンを使用してページイベントバインディングを初期化し、動的に生成されるノードリストの操作を最適化します。

- **検索**: `#search-input` リアルタイムフィルタリング。
- **検証**: `#json-textarea` リアルタイム形式検証。
- **切替**: `.input-toggle` 入力モードの切り替え。
- **選択**: `.button-group` 全選択/クリアの処理。
- **送信**: `#submit-btn` 注入フローのトリガー。

---

### `renderNodeList(searchTerm)`

`nodeStatuses` に基づいて選択可能なノードリストをレンダリングします。

- **状態フィルタリング**: ノードは対応する状態バッジ（実行中/停止/未実行）を表示。
- **操作制限**: 停止中のノードは `disabled-node` スタイルに設定され、注入対象として選択不可。

---

### `handleSubmit()`

タスク注入送信ロジックを実行します。

1. **データ取得**: 現在の `currentInputMethod` に基づいてテキストエリアの内容またはアップロードされたファイル内容を取得。
2. **データ検証**: 選択されたノードが空でないこと、データ形式が有効な JSON（リスト構造であること）を確認。
3. **並行注入**: 選択された各ノードに対して個別に `POST /api/push_injection_tasks` リクエストを送信。
4. **フィードバック表示**: 注入結果をページに表示（成功/失敗/一部成功）。

---

### `switchInputMethod(method)`

JSON テキストエリアとファイルアップロードエリアの間で UI を切り替えます。

---

### `handleFileUpload(e)`

ファイル選択イベントを処理し、`.json` ファイルの内容を読み取り、`validateJSON()` を呼び出して事前検証を行います。

---

### `fillTermination()`

補助関数：JSON 入力ボックスに標準のタスク終了シグナルシーケンスをワンクリックで入力します。

## データフロー

```
1. ページ操作 -> ノード選択 + データ入力
2. 送信クリック -> validateJSON() 検証
3. バックエンドリクエスト -> POST /api/push_injection_tasks
4. UI フィードバック -> 注入の成功/失敗状態を表示
```

## 使用例

### タスク注入のデータ形式と使用例

以下の例はタスク注入機能の典型的な操作フローとデータ構造を示します：

```typescript
// 1. 選択されたターゲットノードをシミュレート（name フィールドのみを含む）
const selectedNodes = [
    { name: "StageA" },
    { name: "StageB" },
];

// 2. タスク注入リクエストのデータ形式
// POST /api/push_injection_tasks
const injectionPayload = {
    node: "StageA",              // ターゲットノードラベル
    task_datas: [                // タスクデータリスト
        { id: 101, content: "file_a.csv" },
        { id: 102, content: "file_b.csv" },
        { id: 103, content: "file_c.csv" },
    ],
    timestamp: "2026-05-24T10:30:00",  // ISO 形式タイムスタンプ
};

// 3. fetch API を使用して手動で注入を送信
async function injectTasks(node: string, taskDatas: any[]) {
    const res = await fetch("/api/push_injection_tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            node,
            task_datas: taskDatas,
            timestamp: new Date().toISOString(),
        }),
    });
    return res.json();
}

// 4. JSON データの正当性を検証
function validateJSON(str: string): { valid: boolean; data?: any; error?: string } {
    try {
        const data = JSON.parse(str);
        if (!Array.isArray(data)) {
            return { valid: false, error: "データは JSON 配列形式である必要があります" };
        }
        return { valid: true, data };
    } catch (e) {
        return { valid: false, error: "JSON 形式が不正です" };
    }
}

// 5. validateJSON を使用して入力を検証
const validInput = '[{"id":1}, {"id":2}]';
const invalidInput = '{invalid json}';

console.log(validateJSON(validInput));
// { valid: true, data: [{ id: 1 }, { id: 2 }] }

console.log(validateJSON(invalidInput));
// { valid: false, error: "JSON 形式が不正です" }

// 6. 複数ノードへのバッチ注入
async function injectToMultipleNodes(nodes: string[], taskDatas: any[]) {
    const results = await Promise.allSettled(
        nodes.map(node => injectTasks(node, taskDatas))
    );
    
    const successCount = results.filter(r => r.status === "fulfilled").length;
    const failCount = results.filter(r => r.status === "rejected").length;
    
    console.log(`注入完了: ${successCount} 成功, ${failCount} 失敗`);
    return results;
}

// 7. 終了シグナル注入
// fillTermination() で入力ボックスに終了シグナルを入力
const terminationPayload = ["TERMINATION_SIGNAL"];
// バックエンドはこのシグナルを受信すると対応するノードのタスク処理を停止します
```
