/**
 * Web 端全局配置结构定义
 */
type WebConfig = {
  theme: "light" | "dark"; // 界面主题
  refreshInterval: number; // 全局轮询刷新间隔（毫秒）
  historyLimit: number; // 节点处理历史记录保留条数
  language: Lang; // 界面语言
  errorPageSize: number; // 错误日志每页显示条数
  showStructureEdgeDelta: boolean; // 是否在结构图边上显示成功任务增量
  dashboard: {
    // 仪表盘布局：各列包含的卡片 ID 列表
    left: string[];
    middle: string[];
    right: string[];
  };
};

// 全局状态
let webConfig: WebConfig | null = null; // 当前加载的 Web 配置

const DEFAULT_WEB_CONFIG: WebConfig = {
  theme: "light",
  refreshInterval: 5000,
  historyLimit: 20,
  language: "zh-CN",
  errorPageSize: 50,
  showStructureEdgeDelta: false,
  dashboard: {
    left: ["mermaid", "analysis"],
    middle: ["status"],
    right: ["progress", "summary"],
  },
};

const PANEL_SELECTOR_MAP = {
  left: ".left-panel",
  middle: ".middle-panel",
  right: ".right-panel",
};

/**
 * 基于默认配置补齐后端返回值，确保页面在缺字段时也能稳定启动。
 * @param {Partial<WebConfig> | null} [rawConfig] - 后端返回的原始配置；为空时仅使用默认值。
 * @returns {WebConfig} 补齐缺省字段后的可用配置对象。
 */
function normalizeWebConfig(rawConfig?: Partial<WebConfig> | null): WebConfig {
  return {
    ...DEFAULT_WEB_CONFIG,
    ...rawConfig,
    dashboard: {
      ...DEFAULT_WEB_CONFIG.dashboard,
      ...(rawConfig?.dashboard ?? {}),
    },
  };
}

/**
 * 从后端加载配置；失败时自动回退到默认配置继续启动页面。
 * @returns {Promise<void>} 配置加载流程完成后结束；无论成功或降级都会保证 `webConfig` 可用。
 */
async function loadWebConfig(): Promise<void> {
  try {
    const res = await fetch("/api/pull_config");
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    webConfig = normalizeWebConfig(await res.json());
    console.log("配置加载成功:", webConfig);
    return;
  } catch (e) {
    console.warn("配置加载失败:", e);
    webConfig = normalizeWebConfig();
    console.warn("配置加载失败，已回退到默认配置启动页面");
  }
}

/**
 * 保存配置到后端
 * @returns {Promise<boolean>} 保存成功返回 `true`，否则返回 `false`。
 */
async function saveWebConfig() {
  try {
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
  } catch (e) {
    console.warn("配置保存失败:", e);
  }
  return false;
}

/**
 * 将配置对象应用到全局变量和页面 UI 元素上
 * 包含语言切换、主题应用、下拉框同步和仪表盘重排
 * @returns {void}
 */
function applyConfig() {
  // 应用语言
  webConfig.language = webConfig.language || "zh-CN";
  setLang(webConfig.language);
  const langSelect = document.getElementById(
    "language-select",
  ) as HTMLSelectElement;
  if (langSelect) langSelect.value = currentLang;

  // 应用主题
  if (webConfig.theme === "dark") {
    document.body.classList.add("dark-theme");
    themeToggleBtn.textContent = t("theme.light");
  } else {
    document.body.classList.remove("dark-theme");
    themeToggleBtn.textContent = t("theme.dark");
  }

  // 应用刷新间隔
  const interval = Number(webConfig.refreshInterval);
  refreshRate = Number.isFinite(interval) && interval > 0 ? interval : 5000;
  webConfig.refreshInterval = refreshRate;
  refreshSelect.value = refreshRate.toString();

  // 应用历史长度
  const limit = Number(webConfig.historyLimit);
  if (Number.isFinite(limit) && limit > 0) {
    const limitStr = limit.toString();
    const hasOption = Array.from(historyLimitSelect.options).some(
      (o) => o.value === limitStr,
    );
    if (hasOption) {
      historyLimitSelect.value = limitStr;
    }
  }

  // 应用错误日志每页条数
  webConfig.errorPageSize = webConfig.errorPageSize || 10;
  const eps = Number(webConfig.errorPageSize);
  if (Number.isFinite(eps) && eps > 0) {
    pageSize = eps;
    const epsStr = eps.toString();
    const errorPageSizeSelect = document.getElementById(
      "error-page-size",
    ) as HTMLSelectElement;
    if (errorPageSizeSelect) {
      const hasOption = Array.from(errorPageSizeSelect.options).some(
        (o) => o.value === epsStr,
      );
      if (hasOption) {
        errorPageSizeSelect.value = epsStr;
      }
    }
  }

  // 应用结构图边增量显示开关
  webConfig.showStructureEdgeDelta = webConfig.showStructureEdgeDelta !== false;
  structureEdgeDeltaToggle.checked = webConfig.showStructureEdgeDelta;

  // 应用仪表盘布局
  applyDashboardLayout();

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
  const dashboard = webConfig.dashboard;
  const allCardKeys = Array.from(
    new Set([
      "mermaid",
      "analysis",
      "status",
      "progress",
      "summary",
      ...(dashboard.left || []),
      ...(dashboard.middle || []),
      ...(dashboard.right || []),
    ]),
  );
  const cardElements: Record<string, HTMLElement | null> = Object.fromEntries(
    allCardKeys.map((key) => [key, document.querySelector(`.${key}-card`)]),
  );
  const panelElements: Record<string, HTMLElement | null> = Object.fromEntries(
    Object.entries(PANEL_SELECTOR_MAP).map(([key, selector]) => [
      key,
      document.querySelector(selector),
    ]),
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
    //    - 应用卡片显隐和排序
    for (const cardKey of panelCardKeys) {
      const cardEl = cardElements[cardKey];
      if (!cardEl) continue;

      panelEl.appendChild(cardEl);
      cardEl.style.display = "";

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
