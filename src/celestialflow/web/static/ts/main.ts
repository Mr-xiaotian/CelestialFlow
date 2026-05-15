// 全局配置对象
let refreshRate = 5000; // 轮询刷新间隔（毫秒）
let refreshIntervalId: ReturnType<typeof setInterval> | null = null; // 轮询定时器 ID

// DOM 元素引用
const refreshSelect = document.getElementById("refresh-interval") as HTMLSelectElement; // 刷新间隔下拉框
const historyLimitSelect = document.getElementById("history-limit") as HTMLSelectElement; // 历史长度下拉框
const settingsBtn = document.getElementById("settings-btn") as HTMLButtonElement; // 设置齿轮按钮
const settingsPanel = document.getElementById("settings-panel") as HTMLElement; // 设置悬浮面板
const settingsClose = document.getElementById("settings-close") as HTMLButtonElement; // 设置面板关闭按钮
const themeToggleBtn = document.getElementById("theme-toggle") as HTMLButtonElement; // 主题切换按钮
const tabButtons = document.querySelectorAll<HTMLElement>(".tab-btn"); // 页签按钮列表
const tabContents = document.querySelectorAll<HTMLElement>(".tab-content"); // 页签内容列表

document.addEventListener("DOMContentLoaded", async () => {
    // ==== 初始化配置 ====
    const loaded = await loadWebConfig();
    if (!loaded) return;

    applyConfig();

    // ==== 事件绑定 ====
    // 点击齿轮按钮：切换设置面板显示/隐藏
    settingsBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        settingsPanel.classList.toggle("hidden");
    });

    // 点击关闭按钮：隐藏设置面板
    settingsClose.addEventListener("click", () => {
        settingsPanel.classList.add("hidden");
    });

    // 点击页面空白处：自动关闭设置面板
    document.addEventListener("click", (e) => {
        if (!settingsPanel.classList.contains("hidden") &&
            !settingsPanel.contains(e.target as Node) &&
            e.target !== settingsBtn) {
            settingsPanel.classList.add("hidden");
        }
    });

    // 切换刷新间隔：更新轮询频率并保存配置
    refreshSelect.addEventListener("change", () => {
        refreshRate = parseInt(refreshSelect.value);
        webConfig.refreshInterval = refreshRate;
        saveWebConfig(); // 保存配置
        clearInterval(refreshIntervalId);
        refreshIntervalId = setInterval(refreshAll, refreshRate);
    });

    // 切换历史长度限制：保存配置（后端下次快照时生效）
    historyLimitSelect.addEventListener("change", () => {
        webConfig.historyLimit = parseInt(historyLimitSelect.value);
        saveWebConfig(); // 保存配置
    });

    // 切换明暗主题：更新样式并重新渲染图表
    themeToggleBtn.addEventListener("click", () => {
        const isDark = toggleDarkTheme();
        webConfig.theme = isDark ? "dark" : "light";
        saveWebConfig(); // 保存配置
        themeToggleBtn.textContent = isDark ? "🌞 白天模式" : "🌙 夜间模式";
        renderMermaidStructure(nodeStatuses); // 主题切换后重新渲染 Mermaid 图
        updateChartTheme(); // 主题切换后更新折线图颜色
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
  // - errors 会被 loadErrors 更新后用于错误列表渲染
  const [statusesChanged, structureChanged, errorsChanged, analysisChanged, summaryChanged, historiesChanged] = await Promise.all([
    loadStatuses(),    // 从后端拉取节点运行状态（处理数、等待数、失败数等），更新 nodeStatuses
    loadStructure(),   // 拉取任务结构（有向图），更新 structureData
    loadErrors(),      // 获取新增错误记录，append 到 errors[]，返回是否有新数据
    loadAnalysis(),    // 获取最新分析信息，更新 analysisData
    loadSummary(),     // 获取最新汇总数据，更新 summaryData
    loadHistories(),   // 获取节点进度历史数据，更新 nodeHistories
  ]);

  if (statusesChanged || structureChanged) {
    renderMermaidStructure(nodeStatuses); // 左上结构图, 依赖节点信息与结构信息
  }

  if (analysisChanged) {
    renderAnalysisInfo();   // 左下分析信息
  }

  if (statusesChanged) {
    renderDashboard();                // 中间节点状态卡片
    populateNodeFilter(nodeStatuses); // 错误筛选器
    renderNodeList();                 // 注入页节点列表
  }

  if (historiesChanged) {
    updateChartData();      // 右上折线图
  }

  if (summaryChanged) {
    renderSummary();        // 右下汇总数据
  }

  if (errorsChanged) {
    renderErrors();         // 错误表格
  }

}
