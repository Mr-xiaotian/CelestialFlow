/**
 * 处理进度历史模块
 * 维护节点处理任务的历史序列，并使用 Chart.js 绘制进度折线图
 */
// 全局状态
let nodeHistories = {}; // 各节点的处理进度历史
let progressChart = null; // Chart.js 折线图实例
/** 用户在图例中手动隐藏的节点集合（持久化到 localStorage，刷新不丢失） */
let hiddenNodes = new Set(JSON.parse(localStorage.getItem("hiddenNodes") || "[]"));
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
    const nextHistories = {};
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
 * 根据最新状态快照在前端追加进度历史点
 * @param {number} timestamp - 本轮状态快照的统一 Unix 时间戳（秒）。
 * @param {Record<string, NodeStatus>} statuses - 最新节点状态映射。
 * @param {Record<string, NodeStatus>} [previousStatuses={}] - 上一轮节点状态映射，用于识别节点重启。
 * @returns {boolean} 历史数据是否发生了变化。
 */
function appendStatusSnapshotToHistory(timestamp, statuses, previousStatuses = {}) {
    if (!Number.isFinite(timestamp) || timestamp <= 0) {
        return false;
    }
    const historyLimit = getCurrentHistoryLimit();
    let changed = false;
    const nextHistories = {};
    for (const [node, status] of Object.entries(statuses)) {
        const previousHistory = nodeHistories[node] || [];
        const previousStatus = previousStatuses[node];
        const lastPoint = previousHistory[previousHistory.length - 1];
        const restarted = Boolean(previousStatus && previousStatus.start_time !== status.start_time);
        const rolledBack = Boolean(lastPoint && status.tasks_processed < lastPoint.tasks_processed);
        const history = restarted || rolledBack ? [] : [...previousHistory];
        const nextPoint = {
            timestamp,
            tasks_processed: status.tasks_processed || 0,
        };
        if (!history.length) {
            history.push(nextPoint);
            changed = true;
        }
        else {
            const currentLastPoint = history[history.length - 1];
            if (currentLastPoint.timestamp === timestamp) {
                if (currentLastPoint.tasks_processed !== nextPoint.tasks_processed) {
                    history[history.length - 1] = nextPoint;
                    changed = true;
                }
            }
            else {
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
        text: style.getPropertyValue(isDark ? "--carbon-200" : "--carbon-900").trim(),
        grid: style.getPropertyValue(isDark ? "--carbon-600" : "--carbon-200").trim(),
        border: style.getPropertyValue(isDark ? "--carbon-500" : "--carbon-300").trim(),
    };
}
/**
 * 初始化节点进度折线图
 * 创建 Chart.js 实例，配置图表选项、图例点击事件等
 * @returns {void}
 */
function initChart() {
    const ctx = document.getElementById("node-progress-chart").getContext("2d");
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
                        }
                        else {
                            hiddenNodes.add(nodeName);
                        }
                        // 保存到 localStorage
                        localStorage.setItem("hiddenNodes", JSON.stringify([...hiddenNodes]));
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
 * @returns {void}
 */
function updateChartTheme() {
    if (!progressChart)
        return;
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
 * @returns {void}
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
    if (!firstNode) {
        progressChart.data.labels = [];
        progressChart.data.datasets = [];
        progressChart.update();
        return;
    }
    progressChart.data.labels = nodeDataMap[firstNode]?.map((p) => new Date(p.x * 1000).toLocaleTimeString());
    progressChart.data.datasets = datasets;
    progressChart.update();
}
