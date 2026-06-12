# カードレイアウトエディタ — `layout_editor`

> 📅 最終更新日: 2026/05/28

## 役割

`layout_editor.ts` はダッシュボード**カードレイアウトエディタ**のフロントエンドモジュールです。フローティングウィンドウ（overlay）内でドラッグ＆ドロップインターフェースを提供し、ユーザーがダッシュボードの左・中央・右の 3 カラムにどのカードを含めるかを自由に調整し、結果を `config.json` に永続化します。

エディタは [SortableJS](https://sortablejs.github.io/Sortable/) を使用してクロスエリアのドラッグソートを実現し、3 カラムと「未使用カードプール」間での相互ドラッグをサポートします。

---

## コア定数

### `DEFAULT_LAYOUT`

デフォルトの 3 カラムカードレイアウト設定で、システム出荷時のカード割り当て案を定義します：

```javascript
const DEFAULT_LAYOUT = {
  left:   ["mermaid", "analysis"],
  middle: ["status"],
  right:  ["progress", "summary"],
};
```

| カラム | デフォルトカード | 説明 |
|------|----------|------|
| `left` | mermaid, analysis | グラフレンダリング + トポロジー分析 |
| `middle` | status | ノード状態テーブル |
| `right` | progress, summary | 進捗 + グローバル集計 |

---

## コア関数

### `renderCard(cardId: string): HTMLElement`

ドラッグ可能なカード DOM 要素を作成します。

| パラメータ | 型 | 説明 |
|------|------|------|
| `cardId` | `string` | カード識別子（例：`"mermaid"`、`"status"`） |

**戻り値：** `.layout-card` CSS クラスを持ち、`data-card-id` 属性とドラッグハンドルを格納した `<div>` 要素。

```html
<div class="layout-card" data-card-id="mermaid">
  <span class="layout-card-name">グラフレンダリング</span>
  <span class="layout-card-handle" aria-hidden="true">⠿</span>
</div>
```

カード名は `CARD_META[cardId]` でローカライズ表示名を検索し、見つからない場合は元の `cardId` にフォールバックします。

---

### `openLayoutEditor()`

レイアウトエディタを開き、現在のレイアウトをレンダリングします。

**フロー：**

```
┌──────────────────────────────────┐
│  1. overlay を表示               │
│  2. webConfig.dashboard を読み取り│
│     （存在しない場合は DEFAULT_LAYOUT を使用）│
│  3. コピーを originalLayout に保存│
│  4. 左/中/右 3 カラムをレンダリング│
│  5. 未使用カードプールをレンダリング│
│  6. initSortable() を呼び出しドラッグ有効化│
└──────────────────────────────────┘
```

未使用カードプールは `ALL_CARD_IDS` のうち 3 カラムで参照されていないすべてのカードを含みます。

---

### `closeLayoutEditor(restore: boolean = true)`

レイアウトエディタを閉じます。

| パラメータ | 型 | デフォルト値 | 説明 |
|------|------|--------|------|
| `restore` | `boolean` | `true` | 元のレイアウトを復元するかどうか。`true` の場合、保存されていないすべてのドラッグ変更を取り消します；`false` の場合、現在のメモリ状態を保持します |

**動作：**
- `restore=true`（デフォルト）：`originalLayout` で `webConfig.dashboard` を上書きし、`applyConfig()` を呼び出してダッシュボードをリフレッシュ。これは閉じるボタンまたはオーバーレイクリック時の動作です。
- `restore=false`：overlay を非表示にするがデータは復元しません。これは保存成功後に呼び出される動作です。

---

### `initSortable()`

SortableJS を初期化し、4 つのドロップゾーンでクロスエリアドラッグを有効にします。

**対象エリア：**

| ID | 説明 |
|----|------|
| `layout-dropzone-left` | 左カラムドロップゾーン |
| `layout-dropzone-middle` | 中央カラムドロップゾーン |
| `layout-dropzone-right` | 右カラムドロップゾーン |
| `layout-dropzone-unused` | 未使用カードプール |

**SortableJS 設定：**

| 設定項目 | 値 | 説明 |
|--------|-----|------|
| `group` | `"dashboard-layout"` | 共有グループ名、4 エリア間で相互ドラッグ可能 |
| `animation` | `150` | ドラッグアニメーション時間（ms） |
| `ghostClass` | `"dragging"` | ドラッグ時のプレースホルダー CSS クラス |
| `dragClass` | `"dragging"` | ドラッグ時カード自体の CSS クラス |

---

### `syncLayout()`

DOM 内の現在の 3 カラムカード順序を `webConfig.dashboard` に同期します。

**フロー：**
1. `left`、`middle`、`right` の 3 つのドロップゾーンを走査
2. 各エリアの `.layout-card` 要素から `data-card-id` を読み取り
3. 順序配列を `webConfig.dashboard` に書き込み

> この関数は**永続化せず**、メモリ構造のみを更新します。永続化は `saveLayout()` が呼び出します。

---

### `saveLayout()`

レイアウトを保存しダッシュボードをリフレッシュします。

**フロー：**

```
┌───────────────────────────────────┐
│  1. syncLayout()                  │
│  2. await saveWebConfig()         │
│     ├─ 成功 → applyConfig()       │
│     │         closeLayoutEditor(false)
│     └─ 失敗 → 保存失敗のヒントを表示│
└───────────────────────────────────┘
```

`saveWebConfig()` は `webConfig` を `POST /api/push_config` で `config.json` に永続化します。

---

### `resetLayout()`

レイアウトを `DEFAULT_LAYOUT` にリセットします。

**フロー：**

1. `webConfig.dashboard` を `DEFAULT_LAYOUT` のディープコピーにリセット
2. 左中右 3 カラムをクリアして再レンダリング（デフォルトカード順）
3. 未使用カードプールをクリアして再計算
4. `initSortable()` を再呼び出ししてドラッグをバインド

> この操作は**自動保存されず**、ユーザーが保存ボタンをクリックして初めて永続化されます。

---

## イベントバインディング

モジュールは `DOMContentLoaded` 時に以下のイベントをバインドします：

| 対象要素 | イベント | 処理関数 |
|----------|------|----------|
| `#open-layout-editor` | `click` | `openLayoutEditor()` |
| `#layout-editor-close` | `click` | `closeLayoutEditor()`（復元） |
| `#layout-editor-overlay` | `click` | オーバーレイ外側クリック時に `closeLayoutEditor()`（復元） |
| `#layout-save-btn` | `click` | `saveLayout()` |
| `#layout-reset-btn` | `click` | `resetLayout()` |

---

## 使用例

### HTML 構造

レイアウトエディタは以下の DOM 構造に依存します：

```html
<!-- トリガーボタン -->
<button id="open-layout-editor">レイアウト編集</button>

<!-- オーバーレイ層 -->
<div id="layout-editor-overlay" class="hidden">
  <div class="layout-editor-panel">
    <h2>カードレイアウト</h2>

    <!-- 3 カラムドロップゾーン -->
    <div id="layout-dropzone-left"></div>
    <div id="layout-dropzone-middle"></div>
    <div id="layout-dropzone-right"></div>

    <!-- 未使用カードプール -->
    <div id="layout-dropzone-unused"></div>

    <!-- 操作ボタン -->
    <button id="layout-save-btn">保存</button>
    <button id="layout-reset-btn">リセット</button>
    <button id="layout-editor-close">閉じる</button>
  </div>
</div>
```

### カスタムデフォルトレイアウト

`DEFAULT_LAYOUT` 定数を変更することで出荷時レイアウトを変更できます：

```typescript
const DEFAULT_LAYOUT = {
  left:   ["mermaid", "analysis", "custom-card"],
  middle: ["status", "errors"],
  right:  ["progress"],
};
```
