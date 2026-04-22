# task_history.ts

各ステージのタスク処理履歴データの読み込みと、折れ線グラフの初期化・更新を管理します。

## グローバル変数

| 変数 | 型 | 説明 |
|------|------|------|
| `nodeHistories` | `Record<string, NodeHistory>` | バックエンドから取得した各ステージの履歴データ |
| `progressChart` | `any` | Chart.js インスタンス |
| `hiddenNodes` | `Set<string>` | 折れ線グラフで非表示のステージ集合、localStorage に永続化 |
| `historyRev` | `number` | 前回取得時のバージョン番号、増分取得（`known_rev`）に使用 |

## 型定義

```ts
type NodeHistory = Array<{ timestamp: number; tasks_processed: number }>;
```

## 関数

### `loadHistories()`

`GET /api/pull_history?known_rev=N` から非同期で履歴データを取得します。サーバー側のデータが変更されていない場合（`body.data === null`）、`false` を返します。それ以外の場合は `nodeHistories` と `historyRev` を更新し、`true` を返します。

---

### `initChart()`

Chart.js 折れ線グラフインスタンスを初期化（または再構築）します。

- 既存のインスタンスがある場合、まず `destroy()` を呼び出して破棄します
- 現在のテーマ（`dark-theme` CSS クラス）に基づいてテキスト色、グリッド色、軸線色を設定します
- 凡例クリックイベントを設定: 凡例項目をクリックするとステージの表示/非表示を切り替え、状態を localStorage に同期保存します

**テーマ切り替え時にはグラフインスタンスの再構築が必要です**。そのため `main.ts` はテーマ切り替え後に `updateChartTheme()` を呼び出して色を更新します。

---

### `updateChartTheme()`

折れ線グラフのカラースキーム（テキスト色、グリッド線色、軸線色）を更新します。インスタンスの破棄と再構築は不要です。テーマ切り替え後に呼び出されます。

---

### `updateChartData()`

`nodeHistories` データを折れ線グラフに書き込み、リフレッシュします。

1. `extractProgressData(nodeHistories)` を呼び出して `{x, y}` 座標ポイントに変換
2. 各ステージの dataset を生成。色は `getColor(index)` で割り当て、`hidden` 状態は `hiddenNodes` で決定
3. 最初のステージのタイムスタンプシーケンスを使用して X 軸ラベル（ローカル時刻文字列）を生成
4. `progressChart.update()` を呼び出して再描画

## データフロー

```
/api/pull_history
  └─ { "node_tag": [{timestamp, tasks_processed}, ...], ... }
        └─ loadHistories() → nodeHistories
              └─ extractProgressData() → {x, y}[] per node
                    └─ updateChartData() → Chart.js 再描画
```
