let webConfig = null;
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
        const res = await fetch("/api/pull_config");
        if (res.ok) {
            webConfig = await res.json();
            console.log("配置加载成功:", webConfig);
            return true;
        }
    }
    catch (e) {
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
    }
    catch (e) {
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
    }
    else {
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
    const allCardKeys = Array.from(new Set([
        ...Object.keys(cards),
        ...(dashboard.left || []),
        ...(dashboard.middle || []),
        ...(dashboard.right || []),
    ]));
    const cardElements = Object.fromEntries(allCardKeys.map((key) => [key, document.querySelector(`.${key}-card`)]));
    const panelElements = Object.fromEntries(Object.entries(PANEL_SELECTOR_MAP).map(([key, selector]) => [key, document.querySelector(selector)]));
    const assigned = new Set();
    // 1) 先把所有已知卡片隐藏，避免卡片从旧布局残留在错误栏位
    for (const cardEl of Object.values(cardElements)) {
        if (cardEl)
            cardEl.style.display = "none";
    }
    // 2) 按配置中的 left/middle/right 顺序遍历栏位
    //    每个栏位内部再按数组顺序依次 appendChild，实现“任意栏位 + 任意顺序”
    for (const panelKey of Object.keys(PANEL_SELECTOR_MAP)) {
        const panelEl = panelElements[panelKey];
        const panelCardKeys = dashboard[panelKey] || [];
        if (!panelEl)
            continue;
        // 3) 对当前栏位中的每一张卡片：
        //    - 通过 .{key}-card 找到真实 DOM
        //    - 移动到目标栏位
        //    - 应用 title 等配置
        for (const cardKey of panelCardKeys) {
            const cardEl = cardElements[cardKey];
            const cardConfig = cards[cardKey] || {};
            if (!cardEl || !cardConfig)
                continue;
            panelEl.appendChild(cardEl);
            cardEl.style.display = "";
            const titleEl = cardEl.querySelector(".card-title");
            if (titleEl && cardConfig.title)
                titleEl.textContent = cardConfig.title;
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
