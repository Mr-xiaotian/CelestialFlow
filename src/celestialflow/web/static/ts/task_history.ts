/**
 * 处理进度历史模块
 * 维护节点处理任务的历史序列，并使用 Chart.js 绘制进度折线图
 */

type NodeHistory = Array<{ timestamp: number; tasks_processed: number }>;

// 全局状态
let nodeHistories: Record<string, NodeHistory> = {}; // 各节点的处理进度历史
let progressChart = null; // Chart.js 折线图实例
/** 用户在图例中手动隐藏的节点集合（持久化到 localStorage，刷新不丢失） */
let hiddenNodes = new Set<string>(
  JSON.parse(localStorage.getItem("hiddenNodes") || "[]")
);
let historyRev = -1; // 数据版本号，用于增量拉取

/**
 * 异步加载最新的节点状态数据
 * 从后端 API 获取节点状态并更新全局变量 nodeHistories
 */
async function loadHistories(): Promise<boolean> {
  try {
    const res = await fetch(`/api/pull_history?known_rev=${historyRev}`);
    const body = await res.json();
    if (body.data === null) return false;
    nodeHistories = body.data;
    historyRev = body.rev;
    return true;
  } catch (e) {
    console.error("状态加载失败", e);
    return false;
  }
}

/**
 * 从 CSS 变量读取图表主题颜色
 */
function getChartThemeColors() {
  const isDark = document.body.classList.contains("dark-theme");
  const style = getComputedStyle(document.documentElement);
  return {
    text:   style.getPropertyValue(isDark ? "--carbon-200" : "--carbon-900").trim(),
    grid:   style.getPropertyValue(isDark ? "--carbon-600" : "--carbon-200").trim(),
    border: style.getPropertyValue(isDark ? "--carbon-500" : "--carbon-300").trim(),
  };
}

/**
 * 初始化节点进度折线图
 * 创建 Chart.js 实例，配置图表选项、图例点击事件等
 */
function initChart() {
  const ctx = (document.getElementById("node-progress-chart") as HTMLCanvasElement).getContext("2d");

  // 销毁旧实例（关键）
  if (progressChart) {
    progressChart.destroy();
  }

  const { text: textColor, grid: gridColor, border: borderColor } = getChartThemeColors();

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
              JSON.stringify([...hiddenNodes])
            );

            const meta = legend.chart.getDatasetMeta(index);
            meta.hidden = !meta.hidden;
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
          title: { display: true, text: t("chart.tasksCompleted"), color: textColor },
          border: { color: borderColor },
        },
      },
    },
  });
}

/**
 * 更新折线图主题颜色（切换深色/浅色模式时调用，无需重建实例）
 */
function updateChartTheme() {
  if (!progressChart) return;

  const { text: textColor, grid: gridColor, border: borderColor } = getChartThemeColors();

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
 */
function updateChartData() {
  const nodeDataMap = extractProgressData(nodeHistories);
  const datasets = Object.entries(nodeDataMap).map(([node, data], index) => ({
    label: node,
    data: data,
    borderColor: getColor(index),
    fill: false,
    tension: 0.3,
    hidden: hiddenNodes.has(node), // 根据用户之前的选择
  }));

  const firstNode = Object.keys(nodeDataMap)[0];
  if (!firstNode) return;
  progressChart.data.labels = nodeDataMap[firstNode]?.map((p) =>
    new Date(p.x * 1000).toLocaleTimeString()
  );
  progressChart.data.datasets = datasets;

  progressChart.update();
}

