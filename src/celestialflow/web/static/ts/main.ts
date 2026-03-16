// 全局配置对象
let webConfig: any = null;
let refreshRate = 5000;
let refreshIntervalId: ReturnType<typeof setInterval> | null = null;

const refreshSelect = document.getElementById("refresh-interval") as HTMLSelectElement;
const themeToggleBtn = document.getElementById("theme-toggle") as HTMLButtonElement;
// const shutdownBtn = document.getElementById("shutdown-btn");
const tabButtons = document.querySelectorAll<HTMLElement>(".tab-btn");
const tabContents = document.querySelectorAll<HTMLElement>(".tab-content");

const PANEL_SELECTOR_MAP = {
    left: ".left-panel",
    middle: ".middle-panel",
    right: ".right-panel",
};

/**
 * 从后端加载配置
 */
async function loadWebConfig() {
    try {
        const res = await fetch("/api/get_config");
        if (res.ok) {
            webConfig = await res.json();
            console.log("配置加载成功:", webConfig);
            return true;
        }
    } catch (e) {
        console.warn("配置加载失败:", e);
    }
    return false;
}

/**
 * 保存配置到后端
 */
async function saveWebConfig() {
    try {
        const res = await fetch("/api/save_config", {
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
    } catch (e) {
        console.warn("配置保存失败:", e);
    }
    return false;
}

/**
 * 应用配置到界面
 */
function applyConfig() {
    // 应用主题
    if (webConfig.theme === "dark") {
        document.body.classList.add("dark-theme");
        themeToggleBtn.textContent = "🌞 白天模式";
    } else {
        document.body.classList.remove("dark-theme");
        themeToggleBtn.textContent = "🌙 夜间模式";
    }
    
    // 应用刷新间隔
    const interval = Number(webConfig.refreshInterval);
    refreshRate = Number.isFinite(interval) && interval > 0 ? interval : 5000;
    webConfig.refreshInterval = refreshRate;
    refreshSelect.value = refreshRate.toString();

    if (typeof hiddenNodes !== "undefined" && hiddenNodes instanceof Set) {
        hiddenNodes = new Set(webConfig.hiddenNodes);
        localStorage.setItem("hiddenNodes", JSON.stringify([...hiddenNodes]));
    }
    
    // 应用仪表盘布局
    applyDashboardLayout();
}

/**
 * 应用仪表盘布局配置
 */
function applyDashboardLayout() {
    const dashboard = webConfig.dashboard;
    const cards = webConfig.cards;
    const allCardKeys = Array.from(
        new Set([
            ...Object.keys(cards),
            ...(dashboard.left || []),
            ...(dashboard.middle || []),
            ...(dashboard.right || []),
        ])
    );
    const cardElements: Record<string, HTMLElement | null> = Object.fromEntries(
        allCardKeys.map((key) => [key, document.querySelector(`.${key}-card`)])
    );
    const panelElements: Record<string, HTMLElement | null> = Object.fromEntries(
        Object.entries(PANEL_SELECTOR_MAP).map(([key, selector]) => [key, document.querySelector(selector)])
    );
    const assigned = new Set();

    // 1) 先把所有已知卡片隐藏，避免卡片从旧布局残留在错误栏位
    for (const cardEl of Object.values(cardElements)) {
        if (cardEl) cardEl.style.display = "none";
    }

    // 2) 按配置中的 left/middle/right 顺序遍历栏位
    //    每个栏位内部再按数组顺序依次 appendChild，实现“任意栏位 + 任意顺序”
    for (const panelKey of Object.keys(PANEL_SELECTOR_MAP)) {
        const panelEl = panelElements[panelKey];
        const panelCardKeys = dashboard[panelKey] || [];
        if (!panelEl) continue;

        // 3) 对当前栏位中的每一张卡片：
        //    - 通过 .{key}-card 找到真实 DOM
        //    - 移动到目标栏位
        //    - 应用 title 等配置
        for (const cardKey of panelCardKeys) {
            const cardEl = cardElements[cardKey];
            const cardConfig = cards[cardKey] || {};
            if (!cardEl || !cardConfig) continue;

            panelEl.appendChild(cardEl);
            cardEl.style.display = "";

            const titleEl = cardEl.querySelector(".card-title") as HTMLElement | null;
            if (titleEl && cardConfig.title) titleEl.textContent = cardConfig.title;

            assigned.add(cardKey);
        }
    }

    // 4) 兜底：没有被任何栏位接收的卡片统一隐藏
    //    防止“配置里删掉某卡片但 DOM 还存在”时出现幽灵卡片
    for (const cardKey of Object.keys(cardElements)) {
        if (assigned.has(cardKey)) continue;
        const cardEl = cardElements[cardKey];
        if (cardEl) cardEl.style.display = "none";
    }
}

/**
 * 切换卡片在面板中的显示
 * @param {string} panelKey - 面板键名 (left/middle/right)
 * @param {string} cardKey - 卡片键名
 */
async function toggleCardInPanel(panelKey, cardKey) {
    if (!webConfig.dashboard?.[panelKey]) return;
    
    const index = webConfig.dashboard[panelKey].indexOf(cardKey);
    if (index > -1) {
        webConfig.dashboard[panelKey].splice(index, 1);
    } else {
        webConfig.dashboard[panelKey].push(cardKey);
    }
    await saveWebConfig();
    applyDashboardLayout();
}

document.addEventListener("DOMContentLoaded", async () => {
    const loaded = await loadWebConfig();
    if (!loaded) return;
    
    // 应用配置
    applyConfig();

    refreshSelect.addEventListener("change", () => {
        refreshRate = parseInt(refreshSelect.value);
        webConfig.refreshInterval = refreshRate;
        saveWebConfig(); // 保存配置
        clearInterval(refreshIntervalId);
        refreshIntervalId = setInterval(refreshAll, refreshRate);
        pushRefreshRate(); // 立即同步到后端
    });

    themeToggleBtn.addEventListener("click", () => {
        const isDark = toggleDarkTheme();
        webConfig.theme = isDark ? "dark" : "light";
        saveWebConfig(); // 保存配置
        themeToggleBtn.textContent = isDark ? "🌞 白天模式" : "🌙 夜间模式";
        renderMermaidFromTaskStructure(); // 主题切换后重新渲染 Mermaid 图
        initChart(); // 主题切换后重新渲染折线图
        updateChartData(); // 由于initChart会重新建立图标实例, 需要重新注入数据
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

    // shutdownBtn.addEventListener("click", async () => {
    //   if (confirm("确认要关闭 Web 服务吗？")) {
    //     const res = await fetch("/shutdown", { method: "POST" });
    //     const text = await res.text();
    //     alert(text);
    //   }
    // });

    initSortableDashboard(); // 初始化拖拽
    refreshAll(); // 启动轮询
    pushRefreshRate(); // 初次加载也推送一次
    initChart(); // 初始化折线图
    refreshIntervalId = setInterval(refreshAll, refreshRate);
});

/**
 * 推送当前的刷新频率设置到后端
 * 尝试通过 API POST 请求更新服务器端的刷新间隔配置
 */
async function pushRefreshRate() {
  try {
    await fetch("/api/push_interval", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ interval: refreshRate }),
    });
  } catch (e) {
    console.warn("刷新频率推送失败", e);
  }
}

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
    loadStatuses(),    // 从后端拉取节点运行状态（处理数、等待数、失败数等），更新 nodeStatuses
    loadStructure(),   // 拉取任务结构（有向图），更新 structureData
    loadErrors(),      // 获取最新错误记录，更新 errors[]
    loadTopology(),    // 获取最新拓扑信息，更新 TopologyData
    loadSummary(),     // 获取最新汇总数据，更新 summaryData

    pushRefreshRate(), // 每次轮询时推送刷新频率到后端
  ]);

  const currentStatusesJSON = JSON.stringify(nodeStatuses);
  const currentStructureJSON = JSON.stringify(structureData);
  const currentErrorsJSON = JSON.stringify(errors);
  const currentTopologyJSON = JSON.stringify(topologyData);
  const currentSummaryJSON = JSON.stringify(summaryData);

  const statusesChanged = currentStatusesJSON !== previousNodeStatusesJSON;
  const structureChanged = currentStructureJSON !== previousStructureDataJSON;
  const errorsChanged = currentErrorsJSON !== previousErrorsJSON;
  const topologyChanged = currentTopologyJSON !== previousTopologyDataJSON;
  const summaryChanged = currentSummaryJSON !== previousSummaryDataJSON;

  if (statusesChanged || structureChanged) {
    previousNodeStatusesJSON = currentStatusesJSON;
    previousStructureDataJSON = currentStructureJSON;

    renderMermaidFromTaskStructure(); // 结构图依赖节点信息与结构信息
  }

  if (topologyChanged) {
    previousTopologyDataJSON = currentTopologyJSON;

    renderTopologyInfo(); // 渲染拓扑信息
  }

  if (summaryChanged) {
    previousSummaryDataJSON = currentSummaryJSON;

    renderSummary(); // 右下汇总数据
  }

  if (statusesChanged) {
    previousNodeStatusesJSON = currentStatusesJSON;

    renderDashboard();      // 中间节点状态卡片
    updateChartData();      // 右上折线图
    populateNodeFilter();   // 错误筛选器
    renderNodeList();       // 注入页节点列表
  }

  if (errorsChanged) {
    previousErrorsJSON = currentErrorsJSON;

    renderErrors();         // 错误表格
  }
  
}
