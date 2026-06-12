# globals.d.ts

> 📅 最終更新日: 2026/06/11

TypeScript グローバル型宣言ファイル。CDN で導入されたサードパーティライブラリ（Chart.js、Sortable.js）、グローバル変数、モジュール間共有関数、バックエンド API 応答構造に対して完全な型定義を提供します。

> ⚠️ **変更済み**: 旧版ドキュメントでは `Chart`/`Sortable` の宣言が `any` に簡略化されていました。現在のバージョンでは完全な最小型定義に展開され、すべての API 応答型とフロントエンド内部構造型が新たに追加されました。

## API 応答型

```typescript
type ApiVersionedResponse<T> = {
  rev: number;       // 現在のデータバージョン番号
  data: T | null;    // known_rev が変化していない場合は null を返す可能性あり
};

type StatusPullResponse = ApiVersionedResponse<Record<string, NodeStatus>> & {
  timestamp: number; // 今回の状態スナップショットの統一タイムスタンプ
};

type StructurePullResponse = ApiVersionedResponse<StructureGraph>;

type AnalysisPullResponse = ApiVersionedResponse<AnalysisData>;

type ErrorsPullResponse = {
  rev: number;
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  sort_order: "newest" | "oldest";
  data: ErrorData[] | null;
};
```

## ダッシュボードレイアウト型

```typescript
type DashboardColumnKey = "left" | "middle" | "right";

type DashboardLayout = Record<DashboardColumnKey, string[]>;
```

## Chart.js 型

```typescript
type ChartPoint = { x: number; y: number };

type ChartDataset = {
  label: string;
  data: ChartPoint[];
  borderColor?: string;
  fill?: boolean;
  tension?: number;
  hidden?: boolean;
};

type ChartLegendItem = {
  datasetIndex: number;
  hidden?: boolean;
};

type ChartLegend = {
  legendItems: ChartLegendItem[];
};

type ChartScaleConfig = {
  ticks: { color: string };
  grid: { color: string };
  title: { display: boolean; text: string; color: string };
  border: { color: string };
};

type ChartOptions = {
  animation: boolean;
  responsive: boolean;
  plugins: {
    legend: {
      labels: { color: string };
      onClick: (event: Event, legendItem: ChartLegendItem, legend: { chart: ChartInstance }) => void;
    };
  };
  interaction: { intersect: boolean; mode: string };
  scales: { x: ChartScaleConfig; y: ChartScaleConfig };
};

interface ChartInstance {
  data: { labels: string[]; datasets: ChartDataset[] };
  options: ChartOptions;
  legend?: ChartLegend;
  destroy(): void;
  update(): void;
  getDatasetMeta(index: number): { hidden: boolean | null };
}

declare const Chart: {
  new (ctx: CanvasRenderingContext2D | null, config: {
    type: string;
    data: ChartInstance["data"];
    options: ChartOptions;
  }): ChartInstance;
};
```

## Sortable.js 型

```typescript
type SortableInstance = {
  destroy(): void;
};

declare const Sortable: {
  create(element: HTMLElement, options: {
    group: string;
    animation: number;
    ghostClass: string;
    dragClass: string;
  }): SortableInstance;
};
```

## Mermaid 型

```typescript
type MermaidApi = {
  run(): void; // ページ内の Mermaid ソースコードをスキャンしてレンダリングを実行
};

interface Window {
  mermaid: MermaidApi;
}
```

## 国際化型とグローバル宣言

```typescript
type Lang = "zh-CN" | "en" | "ja";

declare var currentLang: Lang;
declare function setLang(lang: Lang): void;
declare function t(key: string, ...args: string[]): string;
declare function applyI18nDOM(): void;
```

## モジュール間関数宣言

```typescript
declare function preloadInjectionDraftFromError(
  nodeName: string,
  taskData: unknown,
  jumpToInjectionAfterRetry?: boolean
): void;
```

`preloadInjectionDraftFromError` は `injection.ts` で定義され、`errors.ts` の再注入列から呼び出され、エラーに関連付けられたタスクデータを注入ページエディタに事前入力します。

## 型の関係

```mermaid
flowchart LR
    subgraph "globals.d.ts"
        direction TB
        subgraph "API 応答"
            AVR[ApiVersionedResponse]
            SPR[StatusPullResponse]
            STR[StructurePullResponse]
            APR[AnalysisPullResponse]
            EPR[ErrorsPullResponse]
        end
        subgraph "Chart.js"
            CPT[ChartPoint]
            CDS[ChartDataset]
            CLI[ChartLegendItem]
            CSC[ChartScaleConfig]
            COP[ChartOptions]
            CI[ChartInstance]
        end
        subgraph "外部ライブラリ"
            SORT[Sortable]
            SORTI[SortableInstance]
            MER[MermaidApi]
        end
        subgraph "グローバル関数"
            SL[setLang]
            T[t]
            AI[applyI18nDOM]
            PIDE[preloadInjectionDraftFromError]
        end
    end

    subgraph "実装ファイル"
        I[i18n.ts]
        DH[dashboard_history.ts]
        DS[dashboard_statuses.ts]
        DST[dashboard_structure.ts]
        DA[dashboard_analysis.ts]
        ER[errors.ts]
        INJ[injection.ts]
        LE[layout_editor.ts]
    end

    CI --> DH
    SPR --> DS
    STR --> DST
    APR --> DA
    EPR --> ER
    PIDE --> ER
    PIDE --> INJ
    SL --> I
    T --> I
    AI --> I
    SORT --> LE
```
