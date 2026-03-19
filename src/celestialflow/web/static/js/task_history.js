let nodeHistories = {};
let progressChart = null;
let hiddenNodes = new Set(JSON.parse(localStorage.getItem("hiddenNodes") || "[]"));
let previousNodeHistoriesJSON = "";
/**
 * 异步加载最新的节点状态数据
 * 从后端 API 获取节点状态并更新全局变量 nodeHistories
 */
async function loadHistories() {
    try {
        const res = await fetch("/api/pull_history");
        nodeHistories = await res.json();
    }
    catch (e) {
        console.error("状态加载失败", e);
    }
}
/**
 * 初始化节点进度折线图
 * 创建 Chart.js 实例，配置图表选项、图例点击事件等
 */
function initChart() {
    const ctx = document.getElementById("node-progress-chart").getContext("2d");
    // 销毁旧实例（关键）
    if (progressChart) {
        progressChart.destroy();
    }
    const isDark = document.body.classList.contains("dark-theme");
    const textColor = isDark ? "#e5e7eb" : "#111827"; // 字体颜色
    const gridColor = isDark ? "#4b5563" : "#e5e7eb"; // 网格线颜色
    const borderColor = isDark ? "#6b7280" : "#d1d5db"; // 轴线颜色
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
                    title: { display: true, text: "时间", color: textColor },
                    border: { color: borderColor },
                },
                y: {
                    ticks: { color: textColor },
                    grid: { color: gridColor },
                    title: { display: true, text: "完成任务数", color: textColor },
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
    if (!progressChart)
        return;
    const isDark = document.body.classList.contains("dark-theme");
    const textColor = isDark ? "#e5e7eb" : "#111827";
    const gridColor = isDark ? "#4b5563" : "#e5e7eb";
    const borderColor = isDark ? "#6b7280" : "#d1d5db";
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
    progressChart.data.labels = nodeDataMap[firstNode]?.map((p) => new Date(p.x * 1000).toLocaleTimeString());
    progressChart.data.datasets = datasets;
    progressChart.update();
}
