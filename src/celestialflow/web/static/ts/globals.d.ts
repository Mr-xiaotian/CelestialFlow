/**
 * 全局类型声明文件
 * 包含外部库（Chart.js, Sortable.js, Mermaid）的最小类型定义
 * 以及由其他脚本导出的全局变量和函数
 */

type DashboardColumnKey = "left" | "middle" | "right";

type DashboardLayout = Record<DashboardColumnKey, string[]>;

type ApiVersionedResponse<T> = {
  rev: number;
  data: T | null;
};

type StatusPullResponse = ApiVersionedResponse<Record<string, NodeStatus>> & {
  timestamp: number;
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

type ChartPoint = { x: number; y: number };

type ChartDataset = {
  label?: string;
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
  title: {
    display: boolean;
    text: string;
    color: string;
  };
  border: { color: string };
};

type ChartOptions = {
  animation: boolean;
  responsive: boolean;
  plugins: {
    legend: {
      labels: {
        color: string;
      };
      onClick: (
        event: Event,
        legendItem: ChartLegendItem,
        legend: { chart: ChartInstance },
      ) => void;
    };
  };
  interaction: {
    intersect: boolean;
    mode: string;
  };
  scales: {
    x: ChartScaleConfig;
    y: ChartScaleConfig;
  };
};

interface ChartInstance {
  data: {
    labels: string[];
    datasets: ChartDataset[];
  };
  options: ChartOptions;
  legend?: ChartLegend;
  destroy(): void;
  update(): void;
  getDatasetMeta(index: number): { hidden: boolean | null };
}

declare const Chart: {
  new (
    ctx: CanvasRenderingContext2D | null,
    config: {
      type: string;
      data: ChartInstance["data"];
      options: ChartOptions;
    },
  ): ChartInstance;
};

declare const Sortable: {
  create(
    element: HTMLElement,
    options: {
      group: string;
      animation: number;
      ghostClass: string;
      dragClass: string;
    },
  ): unknown;
};

type MermaidApi = {
  run(): void;
};

interface Window {
  mermaid: MermaidApi;
}

/** 支持的界面语言类型 */
type Lang = "zh-CN" | "en" | "ja";

/** 当前选中的语言标识 */
declare var currentLang: Lang;

/** 设置当前语言并更新 HTML 根节点 */
declare function setLang(lang: Lang): void;

/** 根据翻译键获取当前语言的文本 */
declare function t(key: string, ...args: string[]): string;

/** 将国际化属性应用到 DOM 元素 */
declare function applyI18nDOM(): void;
