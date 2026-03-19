// 全局配置对象
let refreshRate = 5000;
let refreshIntervalId = null;
const refreshSelect = document.getElementById("refresh-interval");
const themeToggleBtn = document.getElementById("theme-toggle");
const tabButtons = document.querySelectorAll(".tab-btn");
const tabContents = document.querySelectorAll(".tab-content");
document.addEventListener("DOMContentLoaded", async () => {
    // ==== 初始化配置 ====
    const loaded = await loadWebConfig();
    if (!loaded)
        return;
    applyConfig();
    // ==== 事件绑定 ====
    refreshSelect.addEventListener("change", () => {
        refreshRate = parseInt(refreshSelect.value);
        webConfig.refreshInterval = refreshRate;
        saveWebConfig(); // 保存配置
        clearInterval(refreshIntervalId);
        refreshIntervalId = setInterval(refreshAll, refreshRate);
    });
    themeToggleBtn.addEventListener("click", () => {
        const isDark = toggleDarkTheme();
        webConfig.theme = isDark ? "dark" : "light";
        saveWebConfig(); // 保存配置
        themeToggleBtn.textContent = isDark ? "🌞 白天模式" : "🌙 夜间模式";
        renderMermaidStructure(nodeStatuses); // 主题切换后重新渲染 Mermaid 图
        updateChartTheme(); // 主题切换后更新折线图颜色
    });
    tabButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const tab = button.getAttribute("data-tab");
            tabButtons.forEach((b) => b.classList.remove("active"));
            tabContents.forEach((c) => c.classList.remove("active"));
            button.classList.add("active");
            if (tab) {
                document.getElementById(tab)?.classList.add("active");
            }
        });
    });
    // ==== 启动流程 ====
    initSortableDashboard(); // 初始化拖拽
    refreshAll(); // 启动轮询
    initChart(); // 初始化折线图
    refreshIntervalId = setInterval(refreshAll, refreshRate);
});
/**
 * 主刷新函数：协调所有数据的更新和 UI 渲染
 * 并行拉取节点状态、结构、错误、拓扑和汇总数据
 * 对比新旧数据，仅在数据变更时触发相应的 UI 更新函数
 */
async function refreshAll() {
    // 并行获取节点状态、任务结构、错误日志（注意是异步 API 请求）
    // - nodeStatuses 会被 loadStatuses 更新
    // - 结构数据会被 loadStructure 使用来渲染 Mermaid 图
    // - errors 会被 loadErrors 更新后用于错误列表渲染
    await Promise.all([
        loadStatuses(), // 从后端拉取节点运行状态（处理数、等待数、失败数等），更新 nodeStatuses
        loadStructure(), // 拉取任务结构（有向图），更新 structureData
        loadErrors(), // 获取最新错误记录，更新 errors[]
        loadTopology(), // 获取最新拓扑信息，更新 TopologyData
        loadSummary(), // 获取最新汇总数据，更新 summaryData
        loadHistories(), // 获取节点进度历史数据，更新 nodeHistories
    ]);
    // 将当前数据转换为 JSON 字符串进行对比，判断哪些数据发生了变化
    const currentStatusesJSON = JSON.stringify(nodeStatuses);
    const currentStructureJSON = JSON.stringify(structureData);
    const currentErrorsJSON = JSON.stringify(errors);
    const currentTopologyJSON = JSON.stringify(topologyData);
    const currentSummaryJSON = JSON.stringify(summaryData);
    const currentHistoriesJSON = JSON.stringify(nodeHistories);
    const statusesChanged = currentStatusesJSON !== previousNodeStatusesJSON;
    const structureChanged = currentStructureJSON !== previousStructureDataJSON;
    const errorsChanged = currentErrorsJSON !== previousErrorsJSON;
    const topologyChanged = currentTopologyJSON !== previousTopologyDataJSON;
    const summaryChanged = currentSummaryJSON !== previousSummaryDataJSON;
    const historiesChanged = currentHistoriesJSON !== previousNodeHistoriesJSON;
    if (statusesChanged || structureChanged) {
        previousNodeStatusesJSON = currentStatusesJSON;
        previousStructureDataJSON = currentStructureJSON;
        renderMermaidStructure(nodeStatuses); // 左上结构图, 依赖节点信息与结构信息
    }
    if (topologyChanged) {
        previousTopologyDataJSON = currentTopologyJSON;
        renderTopologyInfo(); // 左下拓扑信息
    }
    if (statusesChanged) {
        renderDashboard(); // 中间节点状态卡片
        populateNodeFilter(nodeStatuses); // 错误筛选器
        renderNodeList(); // 注入页节点列表
    }
    if (historiesChanged) {
        previousNodeHistoriesJSON = currentHistoriesJSON;
        updateChartData(); // 右上折线图
    }
    if (summaryChanged) {
        previousSummaryDataJSON = currentSummaryJSON;
        renderSummary(); // 右下汇总数据
    }
    if (errorsChanged) {
        previousErrorsJSON = currentErrorsJSON;
        renderErrors(); // 错误表格
    }
}
