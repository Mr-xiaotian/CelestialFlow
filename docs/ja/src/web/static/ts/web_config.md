# web_config.ts

> 📅 最終更新日: 2026/05/15

Web フロントエンドの設定の読み込み、保存、適用を管理します。テーマ、リフレッシュ間隔、履歴長、ダッシュボードレイアウトを含みます。

## グローバル変数

| 変数 | 型 | 説明 |
|------|------|------|
| `webConfig` | `WebConfig \| null` | バックエンドから読み込まれた現在の設定オブジェクト |
| `PANEL_SELECTOR_MAP` | `Record<string, string>` | 3カラムパネルの CSS セレクターマッピング |

## 型定義

```ts
type WebConfig = {
    theme: "light" | "dark";
    refreshInterval: number;
    historyLimit: number;
    dashboard: {
        left: string[];
        middle: string[];
        right: string[];
    };
    cards: Record<string, { title: string }>;
};
```

## 関数

### `loadWebConfig()`

`GET /api/pull_config` から非同期で設定を読み込み、`webConfig` に割り当てます。

- 成功時は `true`、失敗時は `false` を返します
- 失敗時はコンソールに警告を出力し、例外はスローしません

---

### `saveWebConfig()`

現在の `webConfig` を `/api/push_config` に非同期で POST し、バックエンドに永続化します。

- 成功時は `true`、失敗時は `false` を返します

---

### `applyConfig()`

`webConfig` の設定を UI に適用します：

1. **テーマ**: `webConfig.theme` に基づいて `dark-theme` CSS クラスとボタンテキストを切り替え
2. **リフレッシュ間隔**: `refreshRate` とドロップダウンの選択値を更新（境界保護付き）
3. **履歴長**: `historyLimit` を `#history-limit` ドロップダウンに同期（設定値が選択肢に存在する場合のみ設定し、空白表示を回避）
4. **ダッシュボードレイアウト**: `applyDashboardLayout()` を呼び出し

---

### `applyDashboardLayout()`

`webConfig.dashboard` と `webConfig.cards` の設定に基づいて、ダッシュボード内のカードを動的に配置します。

**フロー：**

1. すべての既知のカードキー（設定内 + DOM 内に存在するもの）を収集し、対応する `.{key}-card` DOM 要素を特定
2. まずすべての既知のカードを非表示にする
3. `left` / `middle` / `right` の順に、カードを `appendChild` で対応するカラムに移動し、表示状態に設定
4. フォールバックとして、どのカラムにも割り当てられなかったカードを非表示にする

> `appendChild` による移動で実装されているため、任意のカラム + 任意の順序の組み合わせ設定をサポートします。

## 設定構造

```json
{
    "theme": "light",
    "refreshInterval": 5000,
    "historyLimit": 20,
    "dashboard": {
        "left": ["mermaid", "analysis"],
        "middle": ["status"],
        "right": ["progress", "summary"]
    },
    "cards": {
        "mermaid": { "title": "任务结构图" },
        "analysis": { "title": "图分析信息" },
        "status": { "title": "节点运行状态" },
        "progress": { "title": "节点完成走向" },
        "summary": { "title": "总体状态摘要" }
    }
}
```

設定はバックエンドの `web/config.json` に永続化され、フロントエンドの変更は `saveWebConfig()` で同期されます。
