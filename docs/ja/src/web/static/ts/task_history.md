# task_history.ts

> 📅 最終更新日: 2026/05/15

ノードのタスク処理履歴データの読み込みと折れ線グラフの初期化・更新を管理します。

## グローバル変数

| 変数 | 型 | 説明 |
|------|------|------|
| `nodeHistories` | `Record<string, NodeHistory>` | 各ノードの履歴データ、バックエンドから取得 |
| `progressChart` | `any` | Chart.js インスタンス |
| `hiddenNodes` | `Set<string>` | 折れ線グラフで非表示のノードセット、localStorage に永続化 |
| `historyRev` | `number` | 前回取得時のバージョン番号、増分取得（`known_rev`）に使用 |

## 型定義

```ts
type NodeHistory = Array<{ timestamp: number; tasks_processed: number }>;
```

## 関数

### `loadHistories()`

`GET /api/pull_history?known_rev=N` から非同期で履歴データを取得します。サーバーデータが変更されていない場合（`body.data === null`）、`false` を返します。それ以外の場合は `nodeHistories` と `historyRev` を更新し、`true` を返します。

---

### `initChart()`

Chart.js 折れ線グラフインスタンスを初期化（または再構築）します。

- 既存のインスタンスがある場合、まず `destroy()` で破棄
- 現在のテーマ（`dark-theme` CSS クラス）に基づいてテキスト色、グリッド色、軸線色を設定
- 凡例クリックイベントを設定：凡例項目のクリックでノードの表示/非表示を切り替え、localStorage に同期保存

**テーマ切り替え時にグラフインスタンスの再構築が必要**なため、`main.ts` ではテーマ切り替え後に `updateChartTheme()` を呼び出して色を更新します。

---

### `updateChartTheme()`

折れ線グラフのカラースキーム（テキスト色、グリッド線色、軸線色）をインスタンスの破棄・再構築なしで更新します。テーマ切り替え後に呼び出されます。

---

### `updateChartData()`

`nodeHistories` データを折れ線グラフに書き込み、リフレッシュします。

1. `extractProgressData(nodeHistories)` を呼び出して `{x, y}` 座標点に変換
2. 各ノードの dataset を生成。色は `getColor(index)` で割り当て、`hidden` 状態は `hiddenNodes` で決定
3. 最初のノードのタイムスタンプ列で X 軸ラベル（ローカル時間文字列）を生成。ノードデータがない場合は早期リターン
4. `progressChart.update()` を呼び出して再描画

## データフロー

```
/api/pull_history
  └─ { "node_tag": [{timestamp, tasks_processed}, ...], ... }
        └─ loadHistories() → nodeHistories
              └─ extractProgressData() → {x, y}[] per node
                    └─ updateChartData() → Chart.js 再描画
```
