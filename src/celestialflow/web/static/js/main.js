/**
 * 仪表盘主入口脚本
 * 负责全局事件监听、配置初始化以及主轮询逻辑的协调
 */
// 全局配置与状态变量
let refreshRate = 5000; // 轮询刷新间隔（毫秒）
let refreshIntervalId = null; // 轮询定时器 ID
// DOM 元素引用
const refreshSelect = document.getElementById("refresh-interval"); // 刷新间隔下拉框
const historyLimitSelect = document.getElementById("history-limit"); // 历史长度下拉框
const settingsBtn = document.getElementById("settings-btn"); // 设置齿轮按钮
const settingsPanel = document.getElementById("settings-panel"); // 设置悬浮面板
const settingsClose = document.getElementById("settings-close"); // 设置面板关闭按钮
const settingsStatus = document.getElementById("settings-status"); // 设置保存状态提示
const themeToggleBtn = document.getElementById("theme-toggle"); // 主题切换按钮
const languageSelect = document.getElementById("language-select"); // 语言选择下拉框
const errorPageSizeSelect = document.getElementById("error-page-size"); // 错误每页条数下拉框
const structureEdgeDeltaToggle = document.getElementById("structure-edge-delta"); // 结构图边增量显示开关
const tabButtons = document.querySelectorAll(".tab-btn"); // 页签按钮列表
const tabContents = document.querySelectorAll(".tab-content"); // 页签内容列表
let settingsStatusTimer = null;
document.addEventListener("DOMContentLoaded", async () => {
    // ==== 初始化配置 ====
    await loadWebConfig();
    applyConfig();
    // ==== 事件绑定 ====
    // 点击齿轮按钮：切换设置面板显示/隐藏
    settingsBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        toggleSettingsPanel();
    });
    // 点击关闭按钮：隐藏设置面板
    settingsClose.addEventListener("click", () => {
        closeSettingsPanel({ restoreFocus: true });
    });
    // 点击页面空白处：自动关闭设置面板
    document.addEventListener("click", (e) => {
        if (isSettingsPanelOpen() &&
            !settingsPanel.contains(e.target) &&
            !settingsBtn.contains(e.target)) {
            closeSettingsPanel();
        }
    });
    // 按下 Escape：关闭设置面板并把焦点还给设置按钮
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && isSettingsPanelOpen()) {
            e.preventDefault();
            closeSettingsPanel({ restoreFocus: true });
        }
    });
    // 切换刷新间隔：更新轮询频率并保存配置
    refreshSelect.addEventListener("change", async () => {
        refreshRate = parseInt(refreshSelect.value);
        webConfig.refreshInterval = refreshRate;
        showSettingsSaveStatus(await saveWebConfig() ? "settings.saveSuccess" : "settings.saveFailed");
        clearInterval(refreshIntervalId);
        refreshIntervalId = setInterval(refreshAll, refreshRate);
    });
    // 切换历史长度限制：保存配置（后端下次快照时生效）
    historyLimitSelect.addEventListener("change", async () => {
        webConfig.historyLimit = parseInt(historyLimitSelect.value);
        showSettingsSaveStatus(await saveWebConfig() ? "settings.saveSuccess" : "settings.saveFailed");
    });
    // 切换错误每页条数：更新分页并重新加载
    errorPageSizeSelect.addEventListener("change", async () => {
        pageSize = parseInt(errorPageSizeSelect.value);
        webConfig.errorPageSize = pageSize;
        currentPage = 1;
        await loadErrors(true);
        renderErrors();
        showSettingsSaveStatus(await saveWebConfig() ? "settings.saveSuccess" : "settings.saveFailed");
    });
    // 切换结构图边增量显示：立即重绘结构图并保存配置
    structureEdgeDeltaToggle.addEventListener("change", async () => {
        webConfig.showStructureEdgeDelta = structureEdgeDeltaToggle.checked;
        renderMermaidStructure(nodeStatuses);
        showSettingsSaveStatus(await saveWebConfig() ? "settings.saveSuccess" : "settings.saveFailed");
    });
    // 切换界面语言：更新所有文本并重新渲染动态内容
    languageSelect.addEventListener("change", async () => {
        webConfig.language = languageSelect.value;
        setLang(webConfig.language);
        applyI18nDOM();
        updateSettingsStatusText();
        themeToggleBtn.textContent = document.body.classList.contains("dark-theme") ? t("theme.light") : t("theme.dark");
        renderDashboard();
        renderErrors();
        renderAnalysisInfo();
        renderNodeList();
        initChart();
        updateChartData();
        showSettingsSaveStatus(await saveWebConfig() ? "settings.saveSuccess" : "settings.saveFailed");
    });
    // 切换明暗主题：更新样式并重新渲染图表
    themeToggleBtn.addEventListener("click", async () => {
        const isDark = toggleDarkTheme();
        webConfig.theme = isDark ? "dark" : "light";
        showSettingsSaveStatus(await saveWebConfig() ? "settings.saveSuccess" : "settings.saveFailed");
        themeToggleBtn.textContent = isDark ? t("theme.light") : t("theme.dark");
        renderMermaidStructure(nodeStatuses);
        updateChartTheme();
    });
    // 切换页签：高亮当前按钮并显示对应内容区
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
    // - errors 会被 loadErrors 刷新为当前筛选结果并用于错误列表渲染
    const [statusesChanged, structureChanged, errorsChanged, analysisChanged, summaryChanged, historiesChanged] = await Promise.all([
        loadStatuses(), // 从后端拉取节点运行状态（处理数、等待数、失败数等），更新 nodeStatuses
        loadStructure(), // 拉取任务结构（有向图），更新 structureData
        loadErrors(), // 获取当前分页与筛选条件下的错误记录，更新 errors
        loadAnalysis(), // 获取最新分析信息，更新 analysisData
        loadSummary(), // 获取最新汇总数据，更新 summaryData
        loadHistories(), // 获取节点进度历史数据，更新 nodeHistories
    ]);
    if (statusesChanged || structureChanged) {
        renderMermaidStructure(nodeStatuses); // 左上结构图, 依赖节点信息与结构信息
    }
    if (analysisChanged) {
        renderAnalysisInfo(); // 左下分析信息
    }
    if (statusesChanged) {
        renderDashboard(); // 中间节点状态卡片
        populateNodeFilter(nodeStatuses); // 错误筛选器
        renderNodeList(); // 注入页节点列表
    }
    if (historiesChanged) {
        updateChartData(); // 右上折线图
    }
    if (summaryChanged) {
        renderSummary(); // 右下汇总数据
    }
    if (errorsChanged) {
        renderErrors(); // 错误表格
    }
}
