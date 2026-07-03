/**
 * 全局类型声明文件
 * 包含外部库（Chart.js, Sortable.js, Mermaid）的最小类型定义
 * 以及由其他脚本导出的全局变量和函数
 */

type DashboardColumnKey = "left" | "middle" | "right"; // 仪表盘三栏布局 key

type DashboardLayout = Record<DashboardColumnKey, string[]>; // 每个栏位内的卡片 ID 顺序

type ApiVersionedResponse<T> = {
  rev: number; // 当前数据版本号
  data: T | null; // 当 known_rev 未变化时可能返回 null
};

type StatusPullResponse = ApiVersionedResponse<Record<string, NodeStatus>> & {
  timestamp: number; // 本次状态快照的统一时间戳
};

type StructurePullResponse = ApiVersionedResponse<StructureGraph>; // 结构图拉取响应

type AnalysisPullResponse = ApiVersionedResponse<AnalysisData>; // 分析信息拉取响应

type ErrorsPullResponse = {
  rev: number; // 错误数据版本号
  page: number; // 当前页码
  page_size: number; // 每页条数
  total: number; // 总记录数
  total_pages: number; // 总页数
  sort_order: "newest" | "oldest"; // 当前排序顺序
  data: ErrorData[] | null; // 当前页的错误记录
};

type ErrorTypeCount = {
  error_type: string; // 错误类型名称
  count: number; // 该类型的错误条数
};

type ErrorTypeCountsPullResponse = ApiVersionedResponse<ErrorTypeCount[]>; // 错误类型聚合响应

declare function preloadInjectionDraftFromError(
  nodeName: string,
  taskData: unknown,
): void;

type ChartPoint = { x: number; y: number }; // Chart.js 折线图点坐标

type ChartDataset = {
  label: string; // 数据集标签，通常为节点名
  data: ChartPoint[] | number[]; // 折线图点集合或环形图数值集合
  borderColor?: string | string[]; // 线条颜色或扇区边框色
  backgroundColor?: string | string[]; // 扇区背景色
  borderWidth?: number; // 边框宽度
  fill?: boolean; // 是否填充区域
  tension?: number; // 曲线平滑程度
  hidden?: boolean; // 是否隐藏该数据集
};

type ChartLegendItem = {
  datasetIndex: number; // 对应的数据集索引
  hidden?: boolean; // 当前图例项是否隐藏
};

type ChartLegend = {
  legendItems: ChartLegendItem[]; // 当前图例项集合
};

type ChartScaleConfig = {
  ticks: { color: string }; // 坐标刻度文字配置
  grid: { color: string }; // 网格线配置
  title: {
    display: boolean; // 是否显示标题
    text: string; // 轴标题文案
    color: string; // 标题颜色
  };
  border: { color: string }; // 轴边框颜色
};

type ChartOptions = {
  animation: boolean; // 是否启用动画
  responsive: boolean; // 是否自适应容器尺寸
  plugins: {
    legend?: {
      display?: boolean; // 是否显示内建图例
      labels?: {
        color: string; // 图例文字颜色
      };
      onClick?: (
        event: Event,
        legendItem: ChartLegendItem,
        legend: { chart: ChartInstance },
      ) => void; // 图例点击回调
    };
  };
  interaction?: {
    intersect: boolean; // 是否要求鼠标必须与点相交
    mode: string; // 交互模式
  };
  scales?: {
    x: ChartScaleConfig; // X 轴配置
    y: ChartScaleConfig; // Y 轴配置
  };
  cutout?: string; // 环形图内圈大小
};

interface ChartInstance {
  data: {
    labels: string[]; // 横轴标签
    datasets: ChartDataset[]; // 所有折线数据集
  };
  options: ChartOptions; // 图表配置
  legend?: ChartLegend; // 图例运行时对象
  destroy(): void; // 销毁实例
  update(): void; // 触发重绘
  getDatasetMeta(index: number): { hidden: boolean | null }; // 获取数据集元信息
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

type SortableInstance = {
  destroy(): void; // 销毁当前拖拽实例并释放监听器
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
  ): SortableInstance; // 创建一个可拖拽区域
};

type MermaidApi = {
  run(): void; // 扫描页面中的 Mermaid 源码并执行渲染
};

interface Window {
  mermaid: MermaidApi; // 挂在 window 上的 Mermaid 运行时对象
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
