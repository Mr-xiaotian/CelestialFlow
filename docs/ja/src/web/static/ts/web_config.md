# web_config.ts

> 📅 最終更新日: 2026/06/18

Web フロントエンドの設定読み込み、正規化、保存、適用を管理します。設定は**グループ構造**（`global`、`dashboard`、`errors`、`injection`）を採用し、旧版フラット形式の自動移行にも対応します。

> ⚠️ **変更済み**: 設定構造が旧版フラット `WebConfig` からグループ形式に再構築されました。`LegacyWebConfig` 互換型、`isGroupedWebConfig()` 検出関数、`normalizeDashboardLayout()` レイアウト正規化関数が新たに追加されました。

## 型定義

### 現在のグループ設定

```typescript
type WebGlobalConfig = {
  theme: "light" | "dark";
  autoRefreshEnabled: boolean;
  refreshInterval: number;
  language: Lang;
};

type WebDashboardConfig = {
  historyLimit: number;
  showStructureEdgeDelta: boolean;
  useTotalPendingInStatus: boolean;
  layout: DashboardLayout;
};

type WebErrorsConfig = {
  pageSize: number;
  sortOrder: "newest" | "oldest";
  jumpToInjectionAfterRetry: boolean;
};

type WebInjectionConfig = {
  showInjectableOnly: boolean;
};

type WebConfig = {
  global: WebGlobalConfig;
  dashboard: WebDashboardConfig;
  errors: WebErrorsConfig;
  injection: WebInjectionConfig;
};
```

### 旧版互換型

```typescript
type LegacyWebConfig = {
  theme?: string;
  autoRefreshEnabled?: boolean;
  refreshInterval?: number;
  language?: string;
  historyLimit?: number;
  showStructureEdgeDelta?: boolean;
  useTotalPendingInStatus?: boolean;
  pageSize?: number;
  sortOrder?: string;
  jumpToInjectionAfterRetry?: boolean;
  showInjectableOnly?: boolean;
  layout?: DashboardLayout;
};
```

## グローバル変数

| 変数 | 型 | 説明 |
|------|------|------|
| `webConfig` | `WebConfig` | 現在のランタイム設定オブジェクト、モジュールロード時に `DEFAULT_WEB_CONFIG` で初期化 |
| `saveConfigPending` | `boolean` | 保存リクエストが進行中かどうか（同時書き込み防止） |
| `saveConfigPromise` | `Promise<boolean> \| null` | 現在または直近の保存操作の Promise |
| `PANEL_SELECTOR_MAP` | `Record<string, string>` | パネルキーから CSS セレクタへのマッピング |
| `CARD_TEMPLATES` | `Record<string, string>` | カード ID から HTML テンプレートへのマッピング（mermaid, analysis, status, progress, summary） |
| `CARD_META` | `Record<string, string>` | カード ID から i18n ラベルキーへのマッピング |
| `ALL_CARD_IDS` | `string[]` | `Object.keys(CARD_TEMPLATES)` から自動生成される標準カード ID リスト |
| `DEFAULT_WEB_CONFIG` | `WebConfig` | デフォルト設定テンプレート、初期化とフォールバックに使用 |

## 関数

### `loadWebConfig(): Promise<void>`

非同期で `GET /api/pull_config` から設定を読み込みます。失敗時は自動的にデフォルト設定にフォールバックします。

---

### `saveWebConfig(): Promise<boolean>`

現在の `webConfig` を `POST /api/push_config` で永続化します。**同時実行防止**機構付き：保存が進行中の場合は同じ Promise を再利用します。

---

### `performSaveWebConfig(): Promise<boolean>`

実際の POST リクエストを実行します。`saveConfigPending` フラグを設定し書き込み結果を返します。

---

### `isGroupedWebConfig(config: unknown): boolean`

設定オブジェクトが新しいグループ形式（`global`、`dashboard`、`errors`、`injection` サブオブジェクトを含む）かどうかを検出します。

---

### `normalizeWebConfig(rawConfig?: unknown): WebConfig`

バックエンドから返された生の設定（旧版フラット形式またはフィールド欠落の可能性あり）を `DEFAULT_WEB_CONFIG` とディープマージします。

- 旧版フラット設定（`LegacyWebConfig`）を新しいグループ形式に自動検出・移行します。
- `dashboard.layout` の完全性を保証します。

---

### `normalizeDashboardLayout(layout?: Partial<DashboardLayout>): DashboardLayout`

ダッシュボードレイアウトが 3 カラムキー（`left`、`middle`、`right`）をすべて含むことを保証し、不足時は空配列で補填します。

---

### `applyConfig(): void`

`webConfig` 内の各設定をページに同期します：

1. **言語**: `global.language` を適用し全ページの `data-i18n` 要素を更新。
2. **テーマ**: `global.theme` に基づいて `dark-theme` クラスを切り替え。
3. **パラメータ同期**: リフレッシュレート、履歴長、ページあたり件数、増分スイッチなどを対応する DOM コントロールに同期。
4. **レイアウト**: `applyDashboardLayout()` を呼び出してカードを再配置。

---

### `ensureAllCards(): void`

モジュールロード時に即時実行され、`CARD_TEMPLATES` を走査してすべてのカード DOM ノードを作成し `#card-pool` コンテナに注入します。重複作成を避けるため、既存のクラス名要素の有無をチェックします。

---

### `applyDashboardLayout(): void`

コアレイアウトロジック：DOM 操作（`appendChild`）でカードを 3 カラムパネル間で動的に移動します。設定配列内の順序に厳密に従います。

## デフォルト設定リファレンス

```typescript
const DEFAULT_WEB_CONFIG: WebConfig = {
  global: {
    theme: "light",
    autoRefreshEnabled: true,
    refreshInterval: 5000,
    language: "zh-CN",
  },
  dashboard: {
    historyLimit: 20,
    showStructureEdgeDelta: false,
    useTotalPendingInStatus: false,
    layout: {
      left: ["mermaid", "analysis"],
      middle: ["status"],
      right: ["progress", "summary"],
    },
  },
  errors: {
    pageSize: 50,
    sortOrder: "newest",
    jumpToInjectionAfterRetry: true,
  },
  injection: {
    showInjectableOnly: false,
  },
};
```

## 使用例

```typescript
// 現在の設定を読み取り
console.log("テーマ:", webConfig.global.theme);
console.log("リフレッシュ間隔:", webConfig.global.refreshInterval);
console.log("履歴長:", webConfig.dashboard.historyLimit);
console.log("エラー毎ページ:", webConfig.errors.pageSize);
console.log("注入ページ注入可能のみ表示:", webConfig.injection.showInjectableOnly);

// 設定を変更して保存
webConfig.global.theme = "dark";
webConfig.dashboard.historyLimit = 50;
applyConfig();  // 即座にページに適用
const saved = await saveWebConfig();  // バックエンドに永続化

// 旧版フラット設定の自動移行
const legacy = { theme: "dark", refreshInterval: 3000, historyLimit: 10 };
const normalized = normalizeWebConfig(legacy);
// 自動移行結果: { global: { theme: "dark", ... }, dashboard: { historyLimit: 10, ... }, ... }
```
