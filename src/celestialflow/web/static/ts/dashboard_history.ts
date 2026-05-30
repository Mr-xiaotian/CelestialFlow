/**
 * 处理进度历史模块
 * 维护节点处理任务的历史序列，并使用 Chart.js 绘制进度折线图
 */

/** 历史图支持切换展示的指标字段键 */
type HistoryMetricKey =
  | "tasks_processed"
  | "tasks_succeeded"
  | "tasks_failed"
  | "tasks_duplicated"
  | "tasks_pending"
  | "delta_tasks_processed"
  | "delta_tasks_succeeded"
  | "delta_tasks_failed"
  | "delta_tasks_duplicated";

/** 单个节点在某一时刻的历史采样点 */
type NodeHistoryPoint = {
  timestamp: number;
  tasks_processed: number;
  tasks_succeeded: number;
  tasks_failed: number;
  tasks_duplicated: number;
  tasks_pending: number;
};

type NodeHistory = NodeHistoryPoint[];

// 全局状态
let nodeHistories: Record<string, NodeHistory> = {}; // 各节点的处理进度历史
let progressChart = null; // Chart.js 折线图实例
/** 用户在图例中手动隐藏的节点集合（持久化到 localStorage，刷新不丢失） */
let hiddenNodes = new Set<string>(
  JSON.parse(localStorage.getItem("hiddenNodes") || "[]"),
);
/** 当前历史图正在展示的指标类型，默认显示完成累计。 */
let currentHistoryMetric: HistoryMetricKey = "tasks_processed";

/** 历史图指标切换按钮集合。 */
const metricDots = document.querySelectorAll<HTMLLabelElement>(".metric-dot");

/**
 * 根据索引获取预定义的主题色，用于区分不同节点的折线
 * @param {number} index - 数据集索引
 * @returns {string} 当前主题下解析后的十六进制颜色值
 */
function getColor(index: number): string {
  const vars = [
    "--cornflower-500",
    "--jade-500",
    "--marigold-500",
    "--crimson-500",
    "--violet-500",
    "--rose-500",
    "--jade-400",
    "--sky-500",
    "--amber-500",
  ];
  const style = getComputedStyle(document.documentElement);
  return style.getPropertyValue(vars[index % vars.length]).trim();
}

/**
 * 从节点历史数据中提取图表所需的 `{x, y}` 点序列
 * @param {Record<string, NodeHistory>} histories - 以节点名为键的历史数据映射
 * @param {HistoryMetricKey} metric - 当前需要提取的指标字段
 * @returns {Record<string, Array<{ x: number; y: number }>>} 图表使用的坐标点映射
 */
function extractProgressData(
  histories: Record<string, NodeHistory>,
  metric: HistoryMetricKey,
): Record<string, Array<{ x: number; y: number }>> {
  const isDelta = metric.startsWith("delta_");
  const sourceMetric = isDelta
    ? (metric.replace("delta_", "") as keyof NodeHistoryPoint)
    : null;

  const result: Record<string, Array<{ x: number; y: number }>> = {};
  for (const [node, data] of Object.entries(histories)) {
    if (isDelta && sourceMetric) {
      result[node] = data.map((point, i) => {
        if (i === 0) return { x: point.timestamp, y: 0 };
        const prev = data[i - 1];
        const dt = point.timestamp - prev.timestamp || 1;
        const dy =
          Number(point[sourceMetric] || 0) - Number(prev[sourceMetric] || 0);
        return { x: point.timestamp, y: dy / dt };
      });
    } else {
      result[node] = data.map((point) => ({
        x: point.timestamp,
        y: Number(point[metric] || 0),
      }));
    }
  }
  return result;
}

/**
 * 将历史指标键映射为对应的国际化文案 key
 * @param {HistoryMetricKey} metric - 当前选中的历史图指标键。
 * @returns {string} 对应的国际化翻译 key。
 */
function getHistoryMetricLabelKey(metric: HistoryMetricKey) {
  switch (metric) {
    case "tasks_succeeded":
      return "chart.metric.succeeded";
    case "tasks_failed":
      return "chart.metric.failed";
    case "tasks_duplicated":
      return "chart.metric.duplicated";
    case "tasks_pending":
      return "chart.metric.pending";
    case "delta_tasks_processed":
      return "chart.metric.deltaProcessed";
    case "delta_tasks_succeeded":
      return "chart.metric.deltaSucceeded";
    case "delta_tasks_failed":
      return "chart.metric.deltaFailed";
    case "delta_tasks_duplicated":
      return "chart.metric.deltaDuplicated";
    case "tasks_processed":
    default:
      return "chart.metric.processed";
  }
}

/**
 * 根据当前选中的指标状态更新切换按钮的激活样式
 * @returns {void}
 */
function updateHistoryMetricButtons() {
  metricDots.forEach((dot) => {
    dot.classList.toggle(
      "active",
      dot.dataset.historyMetric === currentHistoryMetric,
    );
  });
}

/**
 * 更新图表坐标轴标题，使其与当前语言和指标类型保持一致
 * @returns {void}
 */
function updateChartAxisLabels() {
  if (!progressChart) return;
  progressChart.options.scales.x.title.text = t("chart.time");
  progressChart.options.scales.y.title.text = t(
    getHistoryMetricLabelKey(currentHistoryMetric),
  );
}

/**
 * 初始化历史图指标切换器
 * - 同步当前激活按钮
 * - 绑定点击事件，在切换指标后更新轴标题并重绘图表
 * @returns {void}
 */
function initHistoryMetricSwitcher() {
  updateHistoryMetricButtons();
  metricDots.forEach((dot) => {
    dot.addEventListener("click", () => {
      const metric = dot.dataset.historyMetric as HistoryMetricKey | undefined;
      if (!metric || metric === currentHistoryMetric) return;
      currentHistoryMetric = metric;
      updateHistoryMetricButtons();
      updateChartAxisLabels();
      updateChartData();
    });
  });
}

initHistoryMetricSwitcher();

/**
 * 获取当前历史曲线保留点数限制
 * @returns {number} 归一化后的历史长度限制，最小为 1。
 */
function getCurrentHistoryLimit() {
  const limit = Number(webConfig?.historyLimit);
  return Number.isFinite(limit) && limit > 0 ? Math.floor(limit) : 20;
}

/**
 * 按当前配置裁剪前端本地维护的历史点数量
 * @returns {boolean} 历史数据是否发生了变化。
 */
function trimNodeHistories() {
  const historyLimit = getCurrentHistoryLimit();
  let changed = false;
  const nextHistories: Record<string, NodeHistory> = {};

  for (const [node, history] of Object.entries(nodeHistories)) {
    const trimmed = history.slice(-historyLimit);
    nextHistories[node] = trimmed;
    if (trimmed.length !== history.length) {
      changed = true;
    }
  }

  nodeHistories = nextHistories;
  return changed;
}

/**
 * 根据最新状态快照在前端追加多指标历史点
 * @param {number} timestamp - 本轮状态快照的统一 Unix 时间戳（秒）。
 * @param {Record<string, NodeStatus>} statuses - 最新节点状态映射。
 * @param {Record<string, NodeStatus>} [previousStatuses={}] - 上一轮节点状态映射，用于识别节点重启。
 * @returns {boolean} 历史数据是否发生了变化。
 */
function appendStatusSnapshotToHistory(
  timestamp: number,
  statuses: Record<string, NodeStatus>,
  previousStatuses: Record<string, NodeStatus> = {},
) {
  if (!Number.isFinite(timestamp) || timestamp <= 0) {
    return false;
  }

  const historyLimit = getCurrentHistoryLimit();
  let changed = false;
  const nextHistories: Record<string, NodeHistory> = {};

  for (const [node, status] of Object.entries(statuses)) {
    const previousHistory = nodeHistories[node] || [];
    const previousStatus = previousStatuses[node];
    const lastPoint = previousHistory[previousHistory.length - 1];
    const restarted = Boolean(
      previousStatus && previousStatus.start_time !== status.start_time,
    );
    const rolledBack = Boolean(
      lastPoint && status.tasks_processed < lastPoint.tasks_processed,
    );
    const history = restarted || rolledBack ? [] : [...previousHistory];
    const nextPoint: NodeHistoryPoint = {
      timestamp,
      tasks_processed: status.tasks_processed || 0,
      tasks_succeeded: status.tasks_succeeded || 0,
      tasks_failed: status.tasks_failed || 0,
      tasks_duplicated: status.tasks_duplicated || 0,
      tasks_pending: status.tasks_pending || 0,
    };

    if (!history.length) {
      history.push(nextPoint);
      changed = true;
    } else {
      const currentLastPoint = history[history.length - 1];
      if (currentLastPoint.timestamp === timestamp) {
        const pointChanged =
          currentLastPoint.tasks_processed !== nextPoint.tasks_processed ||
          currentLastPoint.tasks_succeeded !== nextPoint.tasks_succeeded ||
          currentLastPoint.tasks_failed !== nextPoint.tasks_failed ||
          currentLastPoint.tasks_duplicated !== nextPoint.tasks_duplicated ||
          currentLastPoint.tasks_pending !== nextPoint.tasks_pending;
        if (pointChanged) {
          history[history.length - 1] = nextPoint;
          changed = true;
        }
      } else {
        history.push(nextPoint);
        changed = true;
      }
    }

    const trimmed = history.slice(-historyLimit);
    if (trimmed.length !== history.length) {
      changed = true;
    }
    nextHistories[node] = trimmed;
  }

  if (Object.keys(nodeHistories).some((node) => !(node in statuses))) {
    changed = true;
  }

  nodeHistories = nextHistories;
  return changed;
}

/**
 * 从 CSS 变量读取图表主题颜色
 * @returns {{ text: string; grid: string; border: string }} 当前主题下图表文字、网格线和边框颜色。
 */
function getChartThemeColors() {
  const isDark = document.body.classList.contains("dark-theme");
  const style = getComputedStyle(document.documentElement);
  return {
    text: style
      .getPropertyValue(isDark ? "--carbon-200" : "--carbon-900")
      .trim(),
    grid: style
      .getPropertyValue(isDark ? "--carbon-600" : "--carbon-200")
      .trim(),
    border: style
      .getPropertyValue(isDark ? "--carbon-500" : "--carbon-300")
      .trim(),
  };
}

/**
 * 初始化节点进度折线图
 * 创建 Chart.js 实例，配置图表选项、图例点击事件等
 * @returns {void}
 */
function initChart() {
  const ctx = (
    document.getElementById("node-progress-chart") as HTMLCanvasElement
  ).getContext("2d");

  // 销毁旧实例（关键）
  if (progressChart) {
    progressChart.destroy();
  }

  const {
    text: textColor,
    grid: gridColor,
    border: borderColor,
  } = getChartThemeColors();

  progressChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [],
    },
    options: {
      animation: false,
      responsive: true,
      plugins: {
        legend: {
          labels: {
            color: textColor, // 图例文字颜色
          },
          onClick: (e, legendItem, legend) => {
            const index = legendItem.datasetIndex;
            const nodeName = progressChart.data.datasets[index].label;

            if (hiddenNodes.has(nodeName)) {
              hiddenNodes.delete(nodeName);
            } else {
              hiddenNodes.add(nodeName);
            }

            // 保存到 localStorage
            localStorage.setItem(
              "hiddenNodes",
              JSON.stringify([...hiddenNodes]),
            );

            const meta = legend.chart.getDatasetMeta(index);
            meta.hidden = !meta.hidden;
            legendItem.hidden = meta.hidden;
            legend.chart.update();
          },
        },
      },
      interaction: {
        intersect: false,
        mode: "index",
      },
      scales: {
        x: {
          ticks: { color: textColor },
          grid: { color: gridColor },
          title: { display: true, text: t("chart.time"), color: textColor },
          border: { color: borderColor },
        },
        y: {
          ticks: { color: textColor },
          grid: { color: gridColor },
          title: {
            display: true,
            text: t(getHistoryMetricLabelKey(currentHistoryMetric)),
            color: textColor,
          },
          border: { color: borderColor },
        },
      },
    },
  });
}

/**
 * 更新折线图主题颜色（切换深色/浅色模式时调用，无需重建实例）
 * @returns {void}
 */
function updateChartTheme() {
  if (!progressChart) return;

  const {
    text: textColor,
    grid: gridColor,
    border: borderColor,
  } = getChartThemeColors();

  updateChartAxisLabels();
  progressChart.options.plugins.legend.labels.color = textColor;
  progressChart.options.scales.x.ticks.color = textColor;
  progressChart.options.scales.x.grid.color = gridColor;
  progressChart.options.scales.x.title.color = textColor;
  progressChart.options.scales.x.border.color = borderColor;
  progressChart.options.scales.y.ticks.color = textColor;
  progressChart.options.scales.y.grid.color = gridColor;
  progressChart.options.scales.y.title.color = textColor;
  progressChart.options.scales.y.border.color = borderColor;

  progressChart.update();
}

/**
 * 更新折线图数据
 * 提取节点进度历史数据，更新 Chart.js 实例的数据集并重绘
 * @returns {void}
 */
function updateChartData() {
  updateChartAxisLabels();
  const nodeDataMap = extractProgressData(nodeHistories, currentHistoryMetric);
  const datasets = Object.entries(nodeDataMap).map(([node, data], index) => ({
    label: node,
    data: data,
    borderColor: getColor(index),
    fill: false,
    tension: 0.3,
    hidden: hiddenNodes.has(node), // 根据用户之前的选择
  }));

  const firstNode = Object.keys(nodeDataMap)[0];
  if (!firstNode) {
    progressChart.data.labels = [];
    progressChart.data.datasets = [];
    progressChart.update();
    return;
  }
  progressChart.data.labels = nodeDataMap[firstNode]?.map((p) =>
    new Date(p.x * 1000).toLocaleTimeString(),
  );
  progressChart.data.datasets = datasets;

  progressChart.update();

  // 同步 legendItem.hidden，确保刷新后 legend 渲染与 hiddenNodes 一致
  if (progressChart.legend?.legendItems) {
    progressChart.legend.legendItems.forEach((item) => {
      const dataset = progressChart.data.datasets[item.datasetIndex];
      if (dataset) {
        item.hidden = dataset.hidden || false;
      }
    });
  }
}
