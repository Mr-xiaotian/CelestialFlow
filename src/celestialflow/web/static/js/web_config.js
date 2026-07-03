"use strict";
/** 页面初始化和回退场景共用的默认配置。 */
const DEFAULT_WEB_CONFIG = {
    global: {
        theme: "light",
        autoRefreshEnabled: true,
        refreshInterval: 5000,
        language: "zh-CN",
    },
    dashboard: {
        historyLimit: 20,
        showStructureEdgeDelta: false,
        useTotalPendingInStatus: false,
        layout: {
            left: ["mermaid", "analysis"],
            middle: ["status"],
            right: ["progress", "error-types", "summary"],
        },
    },
    errors: {
        pageSize: 50,
        sortOrder: "newest",
        jumpToInjectionAfterRetry: true,
    },
    injection: {
        showInjectableOnly: true,
    },
};
/** 仪表盘栏位 key 到真实 DOM 选择器的映射。 */
const PANEL_SELECTOR_MAP = {
    left: ".left-panel",
    middle: ".middle-panel",
    right: ".right-panel",
};
/**
 * 判断后端返回值是否已经是新的分组配置结构。
 * @param {unknown} rawConfig - 后端返回的原始配置。
 * @returns {boolean} 若为分组结构则返回 true。
 */
function isGroupedWebConfig(rawConfig) {
    if (!rawConfig || typeof rawConfig !== "object")
        return false;
    const config = rawConfig;
    return "global" in config || "errors" in config || "injection" in config;
}
/**
 * 基于默认布局补齐后端返回的栏位配置。
 * @param {Partial<DashboardLayout> | null | undefined} rawLayout - 原始仪表盘布局。
 * @returns {DashboardLayout} 补齐后的稳定布局对象。
 */
function normalizeDashboardLayout(rawLayout) {
    return {
        ...DEFAULT_WEB_CONFIG.dashboard.layout,
        ...(rawLayout ?? {}),
    };
}
/**
 * 基于默认配置补齐后端返回值，确保页面在缺字段时也能稳定启动。
 * @param {Partial<WebConfig> | LegacyWebConfig | null} [rawConfig] - 后端返回的原始配置；为空时仅使用默认值。
 * @returns {WebConfig} 补齐缺省字段后的可用配置对象。
 */
function normalizeWebConfig(rawConfig) {
    if (!rawConfig) {
        return {
            ...DEFAULT_WEB_CONFIG,
            global: { ...DEFAULT_WEB_CONFIG.global },
            dashboard: {
                ...DEFAULT_WEB_CONFIG.dashboard,
                layout: { ...DEFAULT_WEB_CONFIG.dashboard.layout },
            },
            errors: { ...DEFAULT_WEB_CONFIG.errors },
            injection: { ...DEFAULT_WEB_CONFIG.injection },
        };
    }
    if (isGroupedWebConfig(rawConfig)) {
        return {
            ...DEFAULT_WEB_CONFIG,
            ...rawConfig,
            global: {
                ...DEFAULT_WEB_CONFIG.global,
                ...(rawConfig.global ?? {}),
            },
            dashboard: {
                ...DEFAULT_WEB_CONFIG.dashboard,
                ...(rawConfig.dashboard ?? {}),
                layout: normalizeDashboardLayout(rawConfig.dashboard?.layout),
            },
            errors: {
                ...DEFAULT_WEB_CONFIG.errors,
                ...(rawConfig.errors ?? {}),
            },
            injection: {
                ...DEFAULT_WEB_CONFIG.injection,
                ...(rawConfig.injection ?? {}),
            },
        };
    }
    const legacyConfig = rawConfig;
    return {
        global: {
            ...DEFAULT_WEB_CONFIG.global,
            theme: legacyConfig.theme ?? DEFAULT_WEB_CONFIG.global.theme,
            autoRefreshEnabled: legacyConfig.autoRefreshEnabled ??
                DEFAULT_WEB_CONFIG.global.autoRefreshEnabled,
            refreshInterval: legacyConfig.refreshInterval ?? DEFAULT_WEB_CONFIG.global.refreshInterval,
            language: legacyConfig.language ?? DEFAULT_WEB_CONFIG.global.language,
        },
        dashboard: {
            ...DEFAULT_WEB_CONFIG.dashboard,
            historyLimit: legacyConfig.historyLimit ?? DEFAULT_WEB_CONFIG.dashboard.historyLimit,
            showStructureEdgeDelta: legacyConfig.showStructureEdgeDelta ??
                DEFAULT_WEB_CONFIG.dashboard.showStructureEdgeDelta,
            useTotalPendingInStatus: legacyConfig.useTotalPendingInStatus ??
                DEFAULT_WEB_CONFIG.dashboard.useTotalPendingInStatus,
            layout: normalizeDashboardLayout(legacyConfig.dashboard),
        },
        errors: {
            ...DEFAULT_WEB_CONFIG.errors,
            pageSize: legacyConfig.errorPageSize ?? DEFAULT_WEB_CONFIG.errors.pageSize,
            sortOrder: legacyConfig.errorSortOrder ?? DEFAULT_WEB_CONFIG.errors.sortOrder,
            jumpToInjectionAfterRetry: DEFAULT_WEB_CONFIG.errors.jumpToInjectionAfterRetry,
        },
        injection: {
            ...DEFAULT_WEB_CONFIG.injection,
        },
    };
}
// 全局状态
let webConfig = normalizeWebConfig(); // 当前加载的 Web 配置
let saveConfigPending = false; // 是否还有新的配置变更等待落盘
let saveConfigPromise = null; // 当前正在执行的保存队列
/** 每张仪表盘卡片的 HTML 模板，供初始化和恢复布局时复用。 */
const CARD_TEMPLATES = {
    // ⚠️ 加新卡片只需在这里加一条，ID 会自动出现在布局编辑器中
    // 显示名称用 CARD_META 映射，ALL_CARD_IDS 从 keys 自动生成
    mermaid: `
    <div class="card mermaid-card">
      <h2 class="card-title" id="mermaid-title" data-i18n="card.mermaid.title">结构图</h2>
      <div id="mermaid-container" class="mermaid" style="white-space: pre-line">graph TD</div>
    </div>`,
    analysis: `
    <div class="card analysis-card" id="analysis-card">
      <h2 class="card-title" data-i18n="card.analysis.title">图分析信息</h2>
      <div id="analysis-info" class="analysis-info">
        <div class="empty-placeholder" data-i18n="analysis.noData">暂无分析信息</div>
      </div>
    </div>`,
    status: `
    <div class="card status-card">
      <h2 class="card-title" data-i18n="card.status.title">节点运行状态</h2>
      <div id="dashboard-grid"></div>
    </div>`,
    progress: `
    <div class="card progress-card">
      <div class="progress-card-header">
        <h2 class="card-title" data-i18n="card.progress.title">节点指标走向</h2>
      </div>
      <canvas id="node-progress-chart"></canvas>
      <div class="metric-indicators" role="radiogroup" aria-label="选择指标">
        <label class="metric-dot active" data-history-metric="tasks_processed">
          <span class="dot" style="background: var(--cornflower-500)"></span>
          <span class="label" data-i18n="chart.metric.processed">完成累计</span>
        </label>
        <label class="metric-dot" data-history-metric="tasks_succeeded">
          <span class="dot" style="background: var(--jade-500)"></span>
          <span class="label" data-i18n="chart.metric.succeeded">成功累计</span>
        </label>
        <label class="metric-dot" data-history-metric="tasks_failed">
          <span class="dot" style="background: var(--crimson-500)"></span>
          <span class="label" data-i18n="chart.metric.failed">错误累计</span>
        </label>
        <label class="metric-dot" data-history-metric="tasks_duplicated">
          <span class="dot" style="background: var(--marigold-500)"></span>
          <span class="label" data-i18n="chart.metric.duplicated">重复累计</span>
        </label>
        <span class="metric-sep" aria-hidden="true"></span>
        <label class="metric-dot" data-history-metric="tasks_pending">
          <span class="dot" style="background: var(--violet-500)"></span>
          <span class="label" data-i18n="chart.metric.pending">等待队列</span>
        </label>
        <label class="metric-dot" data-history-metric="total_tasks_pending">
          <span class="dot" style="background: var(--rose-500)"></span>
          <span class="label" data-i18n="chart.metric.pendingGlobal">全局等待队列</span>
        </label>
        <span class="metric-sep" aria-hidden="true"></span>
        <label class="metric-dot" data-history-metric="delta_tasks_processed">
          <span class="dot delta" style="border-color: var(--cornflower-500)"></span>
          <span class="label" data-i18n="chart.metric.deltaProcessed">完成趋势</span>
        </label>
        <label class="metric-dot" data-history-metric="delta_tasks_succeeded">
          <span class="dot delta" style="border-color: var(--jade-500)"></span>
          <span class="label" data-i18n="chart.metric.deltaSucceeded">成功趋势</span>
        </label>
        <label class="metric-dot" data-history-metric="delta_tasks_failed">
          <span class="dot delta" style="border-color: var(--crimson-500)"></span>
          <span class="label" data-i18n="chart.metric.deltaFailed">错误趋势</span>
        </label>
        <label class="metric-dot" data-history-metric="delta_tasks_duplicated">
          <span class="dot delta" style="border-color: var(--marigold-500)"></span>
          <span class="label" data-i18n="chart.metric.deltaDuplicated">重复趋势</span>
        </label>
      </div>
    </div>`,
    "error-types": `
    <div class="card error-types-card">
      <div class="error-types-card-header">
        <h2 class="card-title" data-i18n="card.errorTypes.title">错误类型分布</h2>
        <select
          id="error-type-node-filter"
          class="error-type-node-filter"
          data-i18n-aria-label="errorTypes.nodeFilter"
          aria-label="选择错误统计节点"
        >
          <option value="" data-i18n="errors.allNodes">全部节点</option>
        </select>
      </div>
      <div id="error-type-total" class="error-type-total">当前错误总数: 0</div>
      <div class="error-type-chart-shell">
        <canvas id="error-type-chart"></canvas>
      </div>
      <div id="error-type-legend" class="error-type-legend">
        <div class="empty-placeholder" data-i18n="errorTypes.noData">暂无错误数据</div>
      </div>
    </div>`,
    summary: `
    <div class="card summary-card">
      <h2 class="card-title" data-i18n="card.summary.title">总体状态摘要</h2>
      <div class="summary-grid">
        <div class="summary-item success"><div id="total-succeeded" class="summary-value success">0</div><div class="summary-label" data-i18n="summary.succeeded">总成功任务</div></div>
        <div class="summary-item pending"><div id="total-pending" class="summary-value pending">0</div><div class="summary-label" data-i18n="summary.pending">总等待任务</div></div>
        <div class="summary-item error"><div id="total-failed" class="summary-value error">0</div><div class="summary-label" data-i18n="summary.failed">总错误任务</div></div>
        <div class="summary-item duplicate"><div id="total-duplicated" class="summary-value duplicate">0</div><div class="summary-label" data-i18n="summary.duplicated">总重复任务</div></div>
        <div class="summary-item nodes"><div id="total-nodes" class="summary-value nodes">0</div><div class="summary-label" data-i18n="summary.nodes">活动节点</div></div>
        <div class="summary-item remain"><div id="total-remain" class="summary-value remain">00:00</div><div class="summary-label" data-i18n="summary.remain">总剩余时间</div></div>
      </div>
    </div>`,
};
/** 卡片 ID 到国际化标题 key 的映射。 */
const CARD_META = {
    mermaid: "card.mermaid.title",
    analysis: "card.analysis.title",
    status: "card.status.title",
    progress: "card.progress.title",
    "error-types": "card.errorTypes.title",
    summary: "card.summary.title",
};
/** 当前支持加入布局编辑器的全部卡片 ID。 */
const ALL_CARD_IDS = Object.keys(CARD_TEMPLATES);
/**
 * 确保所有卡片节点都已出现在隐藏池中，供后续布局重排直接移动。
 * @returns {void}
 */
function ensureAllCards() {
    const pool = document.getElementById("card-pool"); // 统一承载尚未挂载到栏位的卡片节点
    for (const [key, html] of Object.entries(CARD_TEMPLATES)) {
        const cls = `${key}-card`; // 每张卡片的唯一类名入口
        if (!document.querySelector(`.${cls}`)) {
            const el = document.createElement("div"); // 临时容器，用于把字符串模板转成真实 DOM
            el.innerHTML = html;
            pool.appendChild(el.firstElementChild);
        }
    }
}
// 模块加载时立即创建所有卡片 DOM，确保后续脚本能通过 getElementById 找到元素
ensureAllCards();
/**
 * 从后端加载配置；失败时自动回退到默认配置继续启动页面。
 * @returns {Promise<void>} 配置加载流程完成后结束；无论成功或降级都会保证 `webConfig` 可用。
 */
async function loadWebConfig() {
    try {
        const res = await fetch("/api/pull_config");
        if (!res.ok) {
            throw new Error(`HTTP ${res.status}`);
        }
        webConfig = normalizeWebConfig((await res.json()));
        console.log("配置加载成功:", webConfig);
        return;
    }
    catch (e) {
        console.warn("配置加载失败:", e);
        webConfig = normalizeWebConfig();
        console.warn("配置加载失败，已回退到默认配置启动页面");
    }
}
/**
 * 执行一次真实的配置落盘请求。
 * 该函数不处理并发协调，仅负责把当前快照推送到后端。
 *
 * @returns {Promise<boolean>} 保存成功返回 `true`，否则返回 `false`。
 */
async function performSaveWebConfig() {
    try {
        // 将当前前端配置完整推送到后端，避免局部字段丢失。
        const res = await fetch("/api/push_config", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(webConfig),
        });
        if (res.ok) {
            console.log("配置保存成功");
            return true;
        }
    }
    catch (e) {
        console.warn("配置保存失败:", e);
    }
    return false;
}
/**
 * 请求保存当前配置。
 * - 同一时刻只允许一条保存请求在飞
 * - 保存期间若有新的配置改动，会在当前请求结束后自动补发一次最新快照
 *
 * @returns {Promise<boolean>} 当前保存队列完全落空后的最终结果。
 */
async function saveWebConfig() {
    saveConfigPending = true;
    if (saveConfigPromise) {
        return saveConfigPromise;
    }
    saveConfigPromise = (async () => {
        let lastResult = true;
        try {
            while (saveConfigPending) {
                saveConfigPending = false;
                lastResult = await performSaveWebConfig();
            }
            return lastResult;
        }
        finally {
            saveConfigPromise = null;
        }
    })();
    return saveConfigPromise;
}
/**
 * 将配置对象应用到全局变量和页面 UI 元素上
 * 包含语言切换、主题应用、下拉框同步和仪表盘重排
 * @returns {void}
 */
function applyConfig() {
    // 应用语言
    webConfig.global.language = webConfig.global.language || "zh-CN";
    setLang(webConfig.global.language);
    const langSelect = document.getElementById("language-select");
    if (langSelect)
        langSelect.value = currentLang;
    // 应用主题
    if (webConfig.global.theme === "dark") {
        document.body.classList.add("dark-theme");
        themeToggleBtn.textContent = t("theme.light");
    }
    else {
        document.body.classList.remove("dark-theme");
        themeToggleBtn.textContent = t("theme.dark");
    }
    // 应用刷新间隔
    webConfig.global.autoRefreshEnabled = webConfig.global.autoRefreshEnabled !== false;
    const interval = Number(webConfig.global.refreshInterval); // 后端配置可能是字符串，先统一转数值
    refreshRate = Number.isFinite(interval) && interval > 0 ? interval : 5000;
    webConfig.global.refreshInterval = refreshRate;
    refreshSelect.value = refreshRate.toString();
    autoRefreshToggle.checked = webConfig.global.autoRefreshEnabled;
    // 应用历史长度
    const limit = Number(webConfig.dashboard.historyLimit); // 历史长度也统一走数值归一化
    if (Number.isFinite(limit) && limit > 0) {
        const limitStr = limit.toString(); // select 的 option 值是字符串
        const hasOption = Array.from(historyLimitSelect.options).some((o) => o.value === limitStr);
        if (hasOption) {
            historyLimitSelect.value = limitStr;
        }
    }
    // 应用错误日志每页条数
    webConfig.errors.pageSize = webConfig.errors.pageSize || 10;
    const eps = Number(webConfig.errors.pageSize); // 错误分页大小需要同步到运行时变量与下拉框
    if (Number.isFinite(eps) && eps > 0) {
        pageSize = eps;
        const epsStr = eps.toString(); // select 的 option 值是字符串
        const errorPageSizeSelect = document.getElementById("error-page-size");
        if (errorPageSizeSelect) {
            const hasOption = Array.from(errorPageSizeSelect.options).some((o) => o.value === epsStr);
            if (hasOption) {
                errorPageSizeSelect.value = epsStr;
            }
        }
    }
    // 应用错误日志排序方式
    webConfig.errors.sortOrder =
        webConfig.errors.sortOrder === "oldest" ? "oldest" : "newest";
    errorSortOrder = webConfig.errors.sortOrder;
    errorSortSelect.value = errorSortOrder;
    webConfig.errors.jumpToInjectionAfterRetry =
        webConfig.errors.jumpToInjectionAfterRetry !== false;
    const errorJumpToInjectionToggle = document.getElementById("error-jump-to-injection-toggle");
    if (errorJumpToInjectionToggle) {
        errorJumpToInjectionToggle.checked =
            webConfig.errors.jumpToInjectionAfterRetry;
    }
    // 应用结构图边增量显示开关
    webConfig.dashboard.showStructureEdgeDelta =
        webConfig.dashboard.showStructureEdgeDelta !== false;
    structureEdgeDeltaToggle.checked = webConfig.dashboard.showStructureEdgeDelta;
    // 应用节点状态等待模式开关
    webConfig.dashboard.useTotalPendingInStatus =
        webConfig.dashboard.useTotalPendingInStatus === true;
    statusTotalPendingToggle.checked =
        webConfig.dashboard.useTotalPendingInStatus;
    // 应用仪表盘布局
    applyDashboardLayout();
    // 应用注入页节点过滤开关
    webConfig.injection.showInjectableOnly =
        webConfig.injection.showInjectableOnly !== false;
    const injectableOnlyToggle = document.getElementById("injectable-only-toggle");
    if (injectableOnlyToggle) {
        injectableOnlyToggle.checked = webConfig.injection.showInjectableOnly;
    }
    // 应用国际化
    applyI18nDOM();
}
/**
 * 应用仪表盘卡片布局配置
 * 通过 DOM 操作（appendChild）将页面中的卡片元素移动到配置指定的左右中栏位中，
 * 并根据配置控制卡片的显隐和顺序。
 * @returns {void}
 */
function applyDashboardLayout() {
    ensureAllCards();
    const dashboard = webConfig.dashboard.layout; // 当前配置中的三栏布局
    const allCardKeys = Array.from(new Set([
        "mermaid",
        "analysis",
        "status",
        "progress",
        "error-types",
        "summary",
        ...(dashboard.left || []),
        ...(dashboard.middle || []),
        ...(dashboard.right || []),
    ]));
    const cardElements = Object.fromEntries(allCardKeys.map((key) => [key, document.querySelector(`.${key}-card`)])); // 所有可能涉及的卡片 DOM 引用
    const panelElements = Object.fromEntries(Object.entries(PANEL_SELECTOR_MAP).map(([key, selector]) => [
        key,
        document.querySelector(selector),
    ])); // 三个栏位容器的 DOM 引用
    const assigned = new Set(); // 记录已经被成功挂到某个栏位的卡片
    // 1) 先把所有已知卡片隐藏，避免卡片从旧布局残留在错误栏位
    for (const cardEl of Object.values(cardElements)) {
        if (cardEl)
            cardEl.style.display = "none";
    }
    // 2) 按配置中的 left/middle/right 顺序遍历栏位
    //    每个栏位内部再按数组顺序依次 appendChild，实现“任意栏位 + 任意顺序”
    for (const panelKey of Object.keys(PANEL_SELECTOR_MAP)) {
        const panelEl = panelElements[panelKey]; // 当前处理的栏位容器
        const panelCardKeys = dashboard[panelKey] || []; // 当前栏位配置中的卡片顺序
        if (!panelEl)
            continue;
        // 3) 对当前栏位中的每一张卡片：
        //    - 通过 .{key}-card 找到真实 DOM
        //    - 移动到目标栏位
        //    - 应用卡片显隐和排序
        for (const cardKey of panelCardKeys) {
            const cardEl = cardElements[cardKey]; // 实际存在于 DOM 中的卡片节点
            if (!cardEl)
                continue;
            panelEl.appendChild(cardEl);
            cardEl.style.display = "";
            assigned.add(cardKey);
        }
    }
    // 4) 兜底：没有被任何栏位接收的卡片统一隐藏
    //    防止“配置里删掉某卡片但 DOM 还存在”时出现幽灵卡片
    for (const cardKey of Object.keys(cardElements)) {
        if (assigned.has(cardKey))
            continue;
        const cardEl = cardElements[cardKey];
        if (cardEl)
            cardEl.style.display = "none";
    }
}
