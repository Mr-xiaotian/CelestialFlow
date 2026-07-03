/**
 * 仪表盘主入口脚本
 * 负责全局事件监听、配置初始化以及主轮询逻辑的协调
 */

// 全局配置与状态变量
let refreshRate = 5000; // 轮询刷新间隔（毫秒）
let refreshIntervalId: ReturnType<typeof setInterval> | null = null; // 轮询定时器 ID

// DOM 元素引用
const refreshSelect = document.getElementById("refresh-interval") as HTMLSelectElement; // 刷新间隔下拉框
const historyLimitSelect = document.getElementById("history-limit") as HTMLSelectElement; // 历史长度下拉框
const settingsBtn = document.getElementById("settings-btn") as HTMLButtonElement; // 设置齿轮按钮
const settingsPanel = document.getElementById("settings-panel") as HTMLElement; // 设置悬浮面板
const settingsClose = document.getElementById("settings-close") as HTMLButtonElement; // 设置面板关闭按钮
const settingsStatus = document.getElementById("settings-status") as HTMLElement; // 设置保存状态提示
const themeToggleBtn = document.getElementById("theme-toggle") as HTMLButtonElement; // 主题切换按钮
const languageSelect = document.getElementById("language-select") as HTMLSelectElement; // 语言选择下拉框
const autoRefreshToggle = document.getElementById("auto-refresh-toggle") as HTMLInputElement; // 自动刷新开关
const errorPageSizeSelect = document.getElementById("error-page-size") as HTMLSelectElement; // 错误每页条数下拉框
const errorJumpToInjectionToggle = document.getElementById("error-jump-to-injection-toggle") as HTMLInputElement; // 错误页任务注入后是否跳转
const structureEdgeDeltaToggle = document.getElementById("structure-edge-delta") as HTMLInputElement; // 结构图边增量显示开关
const statusTotalPendingToggle = document.getElementById("status-total-pending-toggle") as HTMLInputElement; // 节点状态卡等待值模式开关
const injectableOnlyToggle = document.getElementById("injectable-only-toggle") as HTMLInputElement; // 注入页仅显示可注入节点开关
const settingsCurrentGroup = document.getElementById("settings-current-group") as HTMLElement; // 当前页设置分组
const settingsCurrentLabel = document.getElementById("settings-current-label") as HTMLElement; // 当前页设置分组标题
const settingsCurrentEmpty = document.getElementById("settings-current-empty") as HTMLElement; // 当前页无专属设置提示
const settingsCurrentItems = document.querySelectorAll<HTMLElement>("[data-settings-tab]"); // 当前页设置项列表
const tabButtons = document.querySelectorAll<HTMLElement>(".tab-btn"); // 页签按钮列表
const tabContents = document.querySelectorAll<HTMLElement>(".tab-content"); // 页签内容列表
let settingsStatusTimer: ReturnType<typeof setTimeout> | null = null; // 设置状态提示自动隐藏定时器

/**
 * 切换页面暗黑/明亮主题
 * @returns {boolean} 切换后是否为暗黑模式
 */
function toggleDarkTheme(): boolean {
    return document.body.classList.toggle("dark-theme");
}

/**
 * 根据当前配置重建自动刷新定时器。
 * @returns {void}
 */
function syncAutoRefreshTimer(): void {
    if (refreshIntervalId) {
        clearInterval(refreshIntervalId);
        refreshIntervalId = null;
    }
    if (webConfig.global.autoRefreshEnabled) {
        refreshIntervalId = setInterval(refreshAll, refreshRate);
    }
}

/**
 * 显示设置保存状态消息
 * @param {string} messageKey - 状态消息的翻译键
 * @returns {void}
 */
function showSettingsSaveStatus(messageKey: string): void {
    if (settingsStatusTimer) {
        clearTimeout(settingsStatusTimer);
    }

    settingsStatus.dataset.messageKey = messageKey;
    settingsStatus.textContent = t(messageKey);
    settingsStatus.classList.remove("hidden", "settings-status-success", "settings-status-error");
    settingsStatus.classList.add(
        messageKey === "settings.saveSuccess" ? "settings-status-success" : "settings-status-error"
    );

    settingsStatusTimer = setTimeout(() => {
        settingsStatus.classList.add("hidden");
        settingsStatus.dataset.messageKey = "";
    }, messageKey === "settings.saveSuccess" ? 2000 : 5000);
}

/**
 * 更新设置保存状态消息文本
 * @returns {void}
 */
function updateSettingsStatusText(): void {
    const messageKey = settingsStatus.dataset.messageKey;
    if (!messageKey) return;
    settingsStatus.textContent = t(messageKey);
}

/**
 * 检查设置面板是否打开
 * @returns {boolean} 如果设置面板打开则返回 true，否则返回 false
 */
function isSettingsPanelOpen(): boolean {
    return !settingsPanel.classList.contains("hidden");
}

/**
 * 打开设置面板
 * @returns {void}
 */
function openSettingsPanel(): void {
    settingsPanel.classList.remove("hidden");
    settingsBtn.setAttribute("aria-expanded", "true");
    settingsClose.focus();
}

/**
 * 关闭设置面板
 * @param {{ restoreFocus?: boolean }} [options={}] - 关闭选项；`restoreFocus` 为 `true` 时会把焦点还给设置按钮。
 * @returns {void}
 */
function closeSettingsPanel(options: { restoreFocus?: boolean } = {}): void {
    const { restoreFocus = false } = options;
    settingsPanel.classList.add("hidden");
    settingsBtn.setAttribute("aria-expanded", "false");
    if (restoreFocus) {
        settingsBtn.focus();
    }
}

/**
 * 切换设置面板的显示状态
 * @returns {void}
 */
function toggleSettingsPanel(): void {
    if (isSettingsPanelOpen()) {
        closeSettingsPanel();
        return;
    }
    openSettingsPanel();
}

/**
 * 获取当前激活的页面标签。
 * @returns {string} 当前激活 tab 的标识；默认返回 dashboard。
 */
function getActiveTab(): string {
    const activeButton = document.querySelector<HTMLElement>(".tab-btn.active");
    return activeButton?.getAttribute("data-tab") ?? "dashboard";
}

/**
 * 根据当前页筛选设置项，只保留与当前页相关的配置。
 * @returns {void}
 */
function updateCurrentPageSettings(): void {
    const activeTab = getActiveTab();
    let visibleCount = 0;
    const currentScopeKey = `settings.scope.${activeTab}`;

    settingsCurrentLabel.dataset.i18n = currentScopeKey;
    settingsCurrentLabel.textContent = t(currentScopeKey);

    settingsCurrentItems.forEach((item) => {
        const matched = item.dataset.settingsTab === activeTab;
        item.classList.toggle("hidden", !matched);
        if (matched) {
            visibleCount += 1;
        }
    });

    settingsCurrentEmpty.classList.toggle("hidden", visibleCount > 0);
    settingsCurrentGroup.classList.remove("hidden");
}

/**
 * 切换页签并同步设置面板中的当前页面设置分组。
 * @param {HTMLElement} button - 被点击的 tab 按钮。
 * @returns {void}
 */
function activateTab(button: HTMLElement): void {
    const tab = button.getAttribute("data-tab");
    tabButtons.forEach((b) => b.classList.remove("active"));
    tabContents.forEach((c) => c.classList.remove("active"));
    button.classList.add("active");
    if (tab) {
        document.getElementById(tab)?.classList.add("active");
        if (tab === "dashboard") {
            // 结构图使用 Mermaid 渲染，切页回来后需要在可见状态下重绘一次，
            // 否则可能保留隐藏期间的空白 SVG 布局。
            requestAnimationFrame(() => {
                renderMermaidStructure(nodeStatuses);
            });
        }
    }
    updateCurrentPageSettings();
}

// 页面加载完成后初始化配置、设置面板和各模块交互。
document.addEventListener("DOMContentLoaded", async () => {
    // ==== 初始化配置 ====
    await loadWebConfig();
    applyConfig();
  const config = webConfig; // 使用局部引用，后续事件里直接修改同一配置对象
    updateCurrentPageSettings();
    
    // 先渲染一轮默认空态，避免页面在首次拉取完成前出现空白区域。
    renderMermaidStructure(nodeStatuses);
    renderDashboard();
    populateNodeFilter(nodeStatuses);
    populateErrorTypeNodeFilter(nodeStatuses);
    renderErrors();
    renderAnalysisInfo();
    renderInjectionPage();
    initHistoryChart();
    updateChartData();
    initErrorTypeChart();
    renderErrorTypeChart();
    renderSummary();

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
            !settingsPanel.contains(e.target as Node) &&
            !settingsBtn.contains(e.target as Node)) {
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
        config.global.refreshInterval = refreshRate;
        showSettingsSaveStatus(await saveWebConfig() ? "settings.saveSuccess" : "settings.saveFailed");
        syncAutoRefreshTimer();
    });

    // 切换自动刷新开关：控制全局轮询并保存配置
    autoRefreshToggle.addEventListener("change", async () => {
        config.global.autoRefreshEnabled = autoRefreshToggle.checked;
        syncAutoRefreshTimer();
        showSettingsSaveStatus(await saveWebConfig() ? "settings.saveSuccess" : "settings.saveFailed");
    });

    // 切换历史长度限制：立即裁剪当前页面中的历史曲线并保存配置
    historyLimitSelect.addEventListener("change", async () => {
        config.dashboard.historyLimit = parseInt(historyLimitSelect.value);
        if (trimNodeHistories()) {
            updateChartData();
        }
        showSettingsSaveStatus(await saveWebConfig() ? "settings.saveSuccess" : "settings.saveFailed");
    });

    // 切换错误每页条数：更新分页并重新加载
    errorPageSizeSelect.addEventListener("change", async () => {
        pageSize = parseInt(errorPageSizeSelect.value);
        config.errors.pageSize = pageSize;
        currentPage = 1;
        await loadErrors(true);
        renderErrors();
        showSettingsSaveStatus(await saveWebConfig() ? "settings.saveSuccess" : "settings.saveFailed");
    });

    // 切换错误页任务注入后是否跳转注入页：保存配置
    errorJumpToInjectionToggle.addEventListener("change", async () => {
        config.errors.jumpToInjectionAfterRetry = errorJumpToInjectionToggle.checked;
        showSettingsSaveStatus(await saveWebConfig() ? "settings.saveSuccess" : "settings.saveFailed");
    });

    // 切换结构图边增量显示：立即重绘结构图并保存配置
    structureEdgeDeltaToggle.addEventListener("change", async () => {
        config.dashboard.showStructureEdgeDelta = structureEdgeDeltaToggle.checked;
        renderMermaidStructure(nodeStatuses);
        showSettingsSaveStatus(await saveWebConfig() ? "settings.saveSuccess" : "settings.saveFailed");
    });

    // 切换节点状态等待统计模式：重绘节点卡片并保存配置
    statusTotalPendingToggle.addEventListener("change", async () => {
        config.dashboard.useTotalPendingInStatus = statusTotalPendingToggle.checked;
        renderDashboard();
        showSettingsSaveStatus(await saveWebConfig() ? "settings.saveSuccess" : "settings.saveFailed");
    });

    // 切换注入页节点过滤模式：立即刷新节点列表与草稿预览并保存配置
    injectableOnlyToggle.addEventListener("change", async () => {
        config.injection.showInjectableOnly = injectableOnlyToggle.checked;
        renderInjectionPage();
        showSettingsSaveStatus(await saveWebConfig() ? "settings.saveSuccess" : "settings.saveFailed");
    });

    // 切换界面语言：更新所有文本并重新渲染动态内容
    languageSelect.addEventListener("change", async () => {
        config.global.language = languageSelect.value as Lang;
        setLang(config.global.language);
        applyI18nDOM();
        updateCurrentPageSettings();
        updateSettingsStatusText();
        themeToggleBtn.textContent = document.body.classList.contains("dark-theme") ? t("theme.light") : t("theme.dark");
        renderMermaidStructure(nodeStatuses);
        renderDashboard();
        populateNodeFilter(nodeStatuses);
        populateErrorTypeNodeFilter(nodeStatuses);
        renderErrors();
        renderAnalysisInfo();
        renderNodeList();
        refreshInjectionLocalizedText();
        initHistoryChart();
        updateChartData();
        initErrorTypeChart();
        renderErrorTypeChart();
        showSettingsSaveStatus(await saveWebConfig() ? "settings.saveSuccess" : "settings.saveFailed");
    });

    // 切换明暗主题：更新样式并重新渲染图表
    themeToggleBtn.addEventListener("click", async () => {
        const isDark = toggleDarkTheme();
        config.global.theme = isDark ? "dark" : "light";
        showSettingsSaveStatus(await saveWebConfig() ? "settings.saveSuccess" : "settings.saveFailed");
        themeToggleBtn.textContent = isDark ? t("theme.light") : t("theme.dark");
        renderMermaidStructure(nodeStatuses);
        updateChartTheme();
    });

    // 切换页签：高亮当前按钮并显示对应内容区
    tabButtons.forEach((button) => {
        // 点击顶部标签时切换当前页面并同步当前页设置分组。
        button.addEventListener("click", () => {
            activateTab(button);
        });
    });

    // ==== 启动流程 ====
    refreshAll(); // 启动轮询
    syncAutoRefreshTimer();
});

/**
 * 主刷新函数：协调所有数据的更新和 UI 渲染
 * 并行拉取节点状态、结构、错误、拓扑和汇总数据
 * 对比新旧数据，仅在数据变更时触发相应的 UI 更新函数
 * @returns {Promise<void>}
 */
async function refreshAll(): Promise<void> {
  // 并行获取节点状态、任务结构、错误日志（注意是异步 API 请求）
  // - nodeStatuses 会被 loadStatuses 更新
  // - 结构数据会被 loadStructure 使用来渲染 Mermaid 图
  // - errors 会被 loadErrors 刷新为当前筛选结果并用于错误列表渲染
  let [statusesChanged, structureChanged, errorsChanged, analysisChanged, errorTypeCountsChanged] = await Promise.all([
    loadStatuses(),    // 从后端拉取节点运行状态（处理数、等待数、失败数等），更新 nodeStatuses
    loadStructure(),   // 拉取任务结构（有向图），更新 structureData
    loadErrors(),      // 获取当前分页与筛选条件下的错误记录，更新 errors
    loadAnalysis(),    // 获取最新分析信息，更新 analysisData
    loadErrorTypeCounts(), // 获取错误类型聚合结果，更新仪表盘扇形图
  ]);

  // 结构图依赖结构数据，也会用节点状态给节点着色。
  if (statusesChanged || structureChanged) {
    renderMermaidStructure(nodeStatuses); // 左上结构图, 依赖节点信息与结构信息
  }

  // 分析信息只在分析数据变更时刷新，避免无效重绘。
  if (analysisChanged) {
    renderAnalysisInfo();   // 左下分析信息
  }

  // 节点状态变化会联动影响多个区域：状态卡、筛选器、注入页、折线图和汇总卡。
  if (statusesChanged) {
    renderDashboard();                // 中间节点状态卡片
    populateNodeFilter(nodeStatuses); // 错误筛选器
    populateErrorTypeNodeFilter(nodeStatuses); // 错误类型卡片筛选器
    renderInjectionPage();            // 注入页节点列表 + 当前节点编辑区
    updateChartData();                // 右上折线图
    renderSummary();                  // 右下汇总数据
  }

  // 错误分页与筛选结果变更后再重绘错误表格。
  if (errorsChanged) {
    renderErrors();         // 错误表格
  }

  if (errorTypeCountsChanged) {
    renderErrorTypeChart(); // 错误类型分布卡片
  }

}
