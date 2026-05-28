# カードレイアウトエディター — `layout_editor`

> 📅 最終更新日: 2026/05/28

## 目的

`layout_editor.ts` はダッシュボード**カードレイアウトエディター**のフロントエンドモジュールです。フローティングウィンドウ（オーバーレイ）内でドラッグ＆ドロップインターフェースを提供し、ユーザーがダッシュボードの左・中央・右カラムにどのカードを配置するかを自由に調整し、結果を `config.json` に永続化できます。

エディターは [SortableJS](https://sortablejs.github.io/Sortable/) を使用してクロスゾーンのドラッグ＆ドロップソートを実現し、3カラムと「未使用カードプール」間の移動をサポートします。

---

## コア定数

### `DEFAULT_LAYOUT`

デフォルトの3カラムカードレイアウト設定。システム出荷時のカード割り当て方式を定義します：

```javascript
const DEFAULT_LAYOUT = {
  left:   ["mermaid", "analysis"],
  middle: ["status"],
  right:  ["progress", "summary"],
};
```

| カラム | デフォルトカード | 説明 |
|--------|---------------|------|
| `left` | mermaid, analysis | グラフレンダリング + トポロジ分析 |
| `middle` | status | ノード状態テーブル |
| `right` | progress, summary | 進捗 + グローバルサマリー |

---

## コア関数

### `renderCard(cardId: string): HTMLElement`

ドラッグ可能なカード DOM 要素を作成します。

| パラメータ | 型 | 説明 |
|-----------|------|------|
| `cardId` | `string` | カード識別子（例: `"mermaid"`, `"status"`） |

**戻り値:** `.layout-card` CSS クラス、`data-card-id` 属性、ドラッグハンドルを持つ `<div>` 要素。

```html
<div class="layout-card" data-card-id="mermaid">
  <span class="layout-card-name">グラフレンダリング</span>
  <span class="layout-card-handle" aria-hidden="true">⠿</span>
</div>
```

カード名は `CARD_META[cardId]` でローカライズ表示名を検索し、見つからない場合は生の `cardId` にフォールバックします。

---

### `openLayoutEditor()`

レイアウトエディターを開き、現在のレイアウトをレンダリングします。

**フロー:**

```
┌──────────────────────────────────┐
│  1. オーバーレイを表示            │
│  2. webConfig.dashboard を読み取り│
│     （null の場合は              │
│      DEFAULT_LAYOUT を使用）      │
│  3. コピーを originalLayout に保存│
│  4. 左/中/右の3カラムを         │
│     レンダリング                 │
│  5. 未使用カードプールを          │
│     レンダリング                 │
│  6. initSortable() を呼び出して  │
│     ドラッグ＆ドロップを有効化    │
└──────────────────────────────────┘
```

未使用カードプールには、`ALL_CARD_IDS` のうち3カラムのいずれにも参照されていないすべてのカードが含まれます。

---

### `closeLayoutEditor(restore: boolean = true)`

レイアウトエディターを閉じます。

| パラメータ | 型 | デフォルト | 説明 |
|-----------|------|----------|------|
| `restore` | `boolean` | `true` | 元のレイアウトを復元するか。`true` の場合、保存されていないすべてのドラッグ変更を元に戻す。`false` の場合、現在のメモリ内状態を保持 |

**動作:**
- `restore=true`（デフォルト）: `originalLayout` で `webConfig.dashboard` を上書きし、`applyConfig()` を呼び出してダッシュボードをリフレッシュ。閉じるボタンクリック時またはオーバーレイクリック時の動作です。
- `restore=false`: オーバーレイを非表示にするがデータは復元しない。保存成功後に呼び出される動作です。

---

### `initSortable()`

SortableJS を初期化し、4つのドロップゾーン間でのクロスゾーンドラッグ＆ドロップを有効にします。

**対象ゾーン:**

| ID | 説明 |
|----|------|
| `layout-dropzone-left` | 左カラムドロップゾーン |
| `layout-dropzone-middle` | 中央カラムドロップゾーン |
| `layout-dropzone-right` | 右カラムドロップゾーン |
| `layout-dropzone-unused` | 未使用カードプール |

**SortableJS 設定:**

| 設定項目 | 値 | 説明 |
|---------|-----|------|
| `group` | `"dashboard-layout"` | 共有グループ名。クロスゾーンドラッグを有効化 |
| `animation` | `150` | ドラッグアニメーション時間（ms） |
| `ghostClass` | `"dragging"` | ドラッグプレースホルダーの CSS クラス |
| `dragClass` | `"dragging"` | ドラッグ中のカード自体の CSS クラス |

---

### `syncLayout()`

DOM 内の現在の3カラムカード順序を `webConfig.dashboard` に同期します。

**フロー:**
1. `left`、`middle`、`right` のドロップゾーンを走査
2. 各ゾーンの `.layout-card` 要素から `data-card-id` を読み取り
3. 順序付き配列を `webConfig.dashboard` に書き込み

> この関数は**永続化しません**。メモリ内構造の更新のみを行います。永続化は `saveLayout()` が行います。

---

### `saveLayout()`

レイアウトを保存し、ダッシュボードをリフレッシュします。

**フロー:**

```
┌───────────────────────────────────┐
│  1. syncLayout()                  │
│  2. await saveWebConfig()         │
│     ├─ 成功 → applyConfig()       │
│     │         closeLayoutEditor(false)
│     └─ 失敗 → 保存失敗メッセージ  │
│              を表示               │
└───────────────────────────────────┘
```

`saveWebConfig()` は `POST /api/push_config` を通じて `webConfig` を `config.json` に永続化します。

---

### `resetLayout()`

レイアウトを `DEFAULT_LAYOUT` にリセットします。

**フロー:**

1. `webConfig.dashboard` を `DEFAULT_LAYOUT` のディープコピーにリセット
2. 左中右カラムをクリアして再レンダリング（デフォルトのカード順序で）
3. 未使用カードプールをクリアして再計算
4. `initSortable()` を再呼び出ししてドラッグ＆ドロップをバインド

> この操作は**自動保存されません**。ユーザーが保存ボタンをクリックする必要があります。

---

## イベントバインディング

モジュールは `DOMContentLoaded` 時に以下のイベントをバインドします：

| 対象要素 | イベント | ハンドラー |
|---------|--------|----------|
| `#open-layout-editor` | `click` | `openLayoutEditor()` |
| `#layout-editor-close` | `click` | `closeLayoutEditor()`（復元） |
| `#layout-editor-overlay` | `click` | オーバーレイ外クリック時に `closeLayoutEditor()`（復元） |
| `#layout-save-btn` | `click` | `saveLayout()` |
| `#layout-reset-btn` | `click` | `resetLayout()` |

---

## 使用例

### HTML 構造

レイアウトエディターは以下の DOM 構造に依存します：

```html
<!-- トリガーボタン -->
<button id="open-layout-editor">レイアウトを編集</button>

<!-- オーバーレイ -->
<div id="layout-editor-overlay" class="hidden">
  <div class="layout-editor-panel">
    <h2>カードレイアウト</h2>

    <!-- 3カラムドロップゾーン -->
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

### デフォルトレイアウトのカスタマイズ

`DEFAULT_LAYOUT` 定数を変更して出荷時レイアウトを変更します：

```typescript
const DEFAULT_LAYOUT = {
  left:   ["mermaid", "analysis", "custom-card"],
  middle: ["status", "errors"],
  right:  ["progress"],
};
```
