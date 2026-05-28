# dashboard_analysis.ts

> 📅 最終更新日: 2026/05/28

グラフ分析情報の読み込みと分析パネルのレンダリングを管理します。循環検出や階層分析など、TaskGraph トポロジの深い洞察を提供します。

## グローバル変数

| 変数 | 型 | 説明 |
|------|------|------|
| `analysisData` | `Record<string, any>` | 分析データ。グラフ構造タイプ、DAG 状態などを含む |
| `analysisRev` | `number` | データバージョン番号。増分取得の判断に使用 |

## 関数

### `loadAnalysis()`

`GET /api/pull_analysis?known_rev=N` から非同期で分析データを取得します。

---

### `renderAnalysisInfo()`

分析データを `#analysis-info` コンテナにレンダリングします。データが空の場合、「分析情報はありません」と表示します。

**表示フィールド:**

| 表示ラベル | 対応フィールド | 説明 |
|-----------|--------------|------|
| `構造タイプ` | `className` | TaskGraph の具体的な Python クラス名 |
| `DAG か` | `isDAG` | 有向非巡回グラフかどうか。非 DAG の場合は黄色警告スタイル |
| `スケジュールモード` | `scheduleMode` | `eager` または `staged` |
| `階層数` | `layersDict` | グラフのトポロジカル階層の深さ |

## データフロー

```
GET /api/pull_analysis
  └─ loadAnalysis() -> analysisData を更新
        └─ renderAnalysisInfo() -> UI リスト表示
```

## 使用例

### 分析データ構造とレンダリング呼び出しチェーン

以下の例は TypeScript 側での分析データの構造とレンダリングフローを示します：

```typescript
// 分析データの典型的な構造（バックエンド GET /api/pull_analysis から）
// 注意：バックエンドはスネークケースフィールドを返し、フロントエンドは受信時にキャメルケースに変換
const analysisPayload = {
    analysis: {
        className: "TaskGraph",
        isDAG: true,
        scheduleMode: "eager",
        layersDict: {0: ["StageA"], 1: ["StageB", "StageC"], 2: ["StageD"]},
    }
};

// このデータは以下のチェーンで処理・レンダリングされます：

// 1. loadAnalysis() がデータを取得しグローバル変数を更新
// analysisData 構造: Record<string, any>
// 例: { className, isDAG, scheduleMode, layersDict }

// 2. renderAnalysisInfo() が #analysis-info コンテナにレンダリング
//    実際のレンダリングロジック（例示）：
function renderAnalysisInfoExample(data: Record<string, any>) {
    const container = document.getElementById("analysis-info");
    if (!container) return;

    if (!data || Object.keys(data).length === 0) {
        container.innerHTML = "<p>分析情報はありません</p>";
        return;
    }

    container.innerHTML = `
        <div class="analysis-item">
            <span class="analysis-label">構造タイプ</span>
            <span class="analysis-value">${escapeHtml(data.className || "-")}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">DAG か</span>
            <span class="analysis-value ${data.isDAG ? '' : 'warning'}">
                ${data.isDAG ? "はい（非巡回）" : "いいえ（循環あり）"}
            </span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">スケジュールモード</span>
            <span class="analysis-value">${escapeHtml(data.scheduleMode || "-")}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">階層数</span>
            <span class="analysis-value">
                ${data.layersDict ? Object.keys(data.layersDict).length : 0}
            </span>
        </div>
    `;
}

// 3. 完全な呼び出しチェーン
async function fullAnalysisFlow() {
    // fetch を呼び出してデータを取得
    const res = await fetch("/api/pull_analysis?known_rev=0");
    const data = await res.json();

    // グローバルキャッシュを更新
    // analysisData = data; (loadAnalysis 内部で管理)
    // analysisRev = data.rev ?? 0;

    // レンダリングをトリガー
    renderAnalysisInfoExample(data);
}
```
