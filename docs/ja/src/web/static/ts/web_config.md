# web_config.ts

> 📅 最終更新日: 2026/05/28

Web フロントエンドの設定の読み込み、正規化、保存、適用を管理します。テーマ、言語、ポーリング頻度、履歴長、ページサイズ、ダッシュボードレイアウトを含みます。

## 型定義

```ts
type WebConfig = {
    theme: "light" | "dark";         // UI テーマ
    refreshInterval: number;          // グローバルポーリングリフレッシュ間隔（ミリ秒）
    historyLimit: number;             // フロントエンドがローカルで維持する履歴レコード長
    language: Lang;                   // UI 言語（zh-CN, en, ja）
    errorPageSize: number;            // エラーログの1ページあたりの表示件数
    showStructureEdgeDelta: boolean;  // 構造図エッジに成功タスクのデルタを表示するか
    dashboard: {                      // ダッシュボードレイアウト設定
        left: string[];
        middle: string[];
        right: string[];
    };
};
```

## グローバル変数

| 変数 | 型 | 説明 |
|------|------|------|
| `webConfig` | `WebConfig \| null` | 現在のランタイム設定オブジェクト |
| `DEFAULT_WEB_CONFIG` | `WebConfig` | デフォルト設定テンプレート。初期化とフォールバックに使用 |
| `PANEL_SELECTOR_MAP` | `Record<string, string>` | `left` / `middle` / `right` パネルキーを CSS セレクター（`.left-panel`, `.middle-panel`, `.right-panel`）にマッピング |
| `CARD_TEMPLATES` | `Record<string, string>` | カード ID（mermaid, analysis, status, progress, summary）をキーとする HTML テンプレート文字列 |
| `CARD_META` | `Record<string, string>` | カード ID を i18n ラベルキー（例: `mermaid` → `card.mermaid.title`）にマッピング |
| `ALL_CARD_IDS` | `string[]` | `Object.keys(CARD_TEMPLATES)` から自動生成され、レイアウトエディターの正規カード ID リストとして使用 |

## 関数

### `loadWebConfig()`

`GET /api/pull_config` から非同期で設定を読み込みます。

- **堅牢性**: リクエストが失敗した場合（バックエンドが応答しない、ネットワークエラーなど）、例外をキャッチして自動的に `normalizeWebConfig()` を呼び出し、デフォルト設定で起動します。ページの基本機能を確保します。

---

### `saveWebConfig()`

現在の `webConfig` オブジェクトを `/api/push_config` に POST します。バックエンドが `web/config.json` に永続化します。

---

### `normalizeWebConfig(rawConfig?)`

バックエンドから返された生の設定（フィールドが欠落している可能性あり）を `DEFAULT_WEB_CONFIG` とマージします。

- `dashboard` 構造の整合性を確保。
- 深いマージロジックを提供。

---

### `applyConfig()`

`webConfig` の設定をページに同期します：

1. **言語**: `language` を適用し、ページ上のすべての `data-i18n` 要素を更新。
2. **テーマ**: `dark-theme` クラスを切り替え。
3. **パラメータ同期**: リフレッシュレート、履歴長、ページサイズ、デルタトグルを対応する DOM コントロール（Select/Checkbox）に同期。
4. **レイアウト**: `applyDashboardLayout()` を呼び出してカードを再配置。

---

### `ensureAllCards()`

モジュール読み込み時に即時実行。`CARD_TEMPLATES` を走査してすべてのカード DOM ノードを作成し、`#card-pool` コンテナに注入します。

- 重複を防ぐため、既存の `.{key}-card` クラス要素をチェック
- モジュールレベルのトップレベル実行（関数内ではない）。後続のスクリプトがレイアウト操作前に要素を ID で見つけられることを保証

---

### `applyDashboardLayout()`

コアレイアウトロジック：DOM 操作（`appendChild`）によってカードを3カラムパネル間で動的に移動します。

- **動的表示/非表示**: 設定に存在するカードのみ `display: block` に設定。
- **順序制御**: 設定配列の順序に厳密に従ってカードを挿入。

## デフォルト設定リファレンス

```json
{
    "theme": "light",
    "refreshInterval": 5000,
    "historyLimit": 20,
    "language": "zh-CN",
    "errorPageSize": 50,
    "showStructureEdgeDelta": false,
    "dashboard": {
        "left": ["mermaid", "analysis"],
        "middle": ["status"],
        "right": ["progress", "summary"]
    }
}
```

## 使用例

### 設定オブジェクトの構造と読み取り

以下の例は `WebConfig` オブジェクトの完全な構造と、ブラウザコンソールでの読み取り・変更方法を示します：

```typescript
// 1. WebConfig の完全な構造
// デフォルト設定を参照すると、完全な設定オブジェクトには以下が含まれます：
const fullConfig: WebConfig = {
    theme: "light",
    refreshInterval: 5000,
    historyLimit: 20,
    language: "zh-CN",
    errorPageSize: 50,
    showStructureEdgeDelta: false,
    dashboard: {
        left: ["mermaid", "analysis"],
        middle: ["status"],
        right: ["progress", "summary"],
    },
};

// 2. 現在の設定を読み取る（ブラウザコンソールで）
// グローバル変数 webConfig が現在のランタイム設定を保持
console.log("現在の設定:", webConfig);
console.log("テーマ:", webConfig.theme);                   // "light" | "dark"
console.log("リフレッシュ間隔:", webConfig.refreshInterval, "ms"); // 5000
console.log("履歴長:", webConfig.historyLimit);          // 20
console.log("言語:", webConfig.language);                // "zh-CN"
console.log("エラー毎頁:", webConfig.errorPageSize);     // 50
console.log("構造図デルタ:", webConfig.showStructureEdgeDelta); // false
console.log("ダッシュボードレイアウト:", webConfig.dashboard);
// { left: [...], middle: [...], right: [...] }

// 3. normalizeWebConfig を使用して設定をマージ
// バックエンドが一部のフィールドを欠落させて設定を返す場合、デフォルト値で補完：
const partialConfig = {
    theme: "dark",
    refreshInterval: 3000,
};
const normalized = normalizeWebConfig(partialConfig);
console.log("正規化後:", normalized);
// {
//   theme: "dark",
//   refreshInterval: 3000,
//   historyLimit: 20,           // デフォルト値
//   language: "zh-CN",          // デフォルト値
//   errorPageSize: 50,          // デフォルト値
//   showStructureEdgeDelta: false, // デフォルト値
//   dashboard: { left: [...], middle: [...], right: [...] } // デフォルトレイアウト
// }

// 4. 手動で設定を変更して保存
async function updateConfig() {
    // 設定の変更
    webConfig.theme = "dark";
    webConfig.refreshInterval = 2000;
    webConfig.language = "en";

    // 設定をページに適用
    applyConfig();

    // バックエンドに保存
    const saved = await saveWebConfig();
    console.log(saved ? "設定を保存しました" : "設定の保存に失敗しました");
}

// 5. ダッシュボードレイアウトを動的に調整
function rearrangeDashboard() {
    // ステータスカードを左カラムに、構造図を中央カラムに移動
    webConfig.dashboard = {
        left: ["status"],
        middle: ["mermaid"],
        right: ["analysis", "progress", "summary"],
    };
    applyDashboardLayout();
    saveWebConfig();
}

// 6. 起動時にデフォルト設定をフォールバックとして使用
// loadWebConfig() が失敗した場合（バックエンドが応答しないなど）、デフォルト設定にフォールバック：
// webConfig = normalizeWebConfig();
// これにより、どのような状況でもページが正常にレンダリングされることを保証
```
