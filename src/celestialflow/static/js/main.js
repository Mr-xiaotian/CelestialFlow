let refreshRate = 5000;
let refreshIntervalId = null;

const themeToggleBtn = document.getElementById("theme-toggle");
const refreshSelect = document.getElementById("refresh-interval");
const tabButtons = document.querySelectorAll(".tab-btn");
const tabContents = document.querySelectorAll(".tab-content");
const shutdownBtn = document.getElementById("shutdown-btn");

// 初始化折叠节点记录
let collapsedNodeIds = new Set(
  JSON.parse(localStorage.getItem("collapsedNodes") || "[]")
);

document.addEventListener("DOMContentLoaded", async () => {
  const savedRate = parseInt(localStorage.getItem("refreshRate"));
  if (!isNaN(savedRate)) {
    refreshRate = savedRate;
    refreshSelect.value = savedRate.toString();
  }

  refreshSelect.addEventListener("change", () => {
    refreshRate = parseInt(refreshSelect.value);
    localStorage.setItem("refreshRate", refreshRate); // ✅ 保存设置
    clearInterval(refreshIntervalId);
    refreshIntervalId = setInterval(refreshAll, refreshRate);
    pushRefreshRate(); // ✅ 立即同步到后端
  });

  themeToggleBtn.addEventListener("click", () => {
    const isDark = document.body.classList.toggle("dark-theme");
    localStorage.setItem("theme", isDark ? "dark" : "light");
    themeToggleBtn.textContent = isDark ? "🌞 白天模式" : "🌙 夜间模式";
  });

  tabButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const tab = button.getAttribute("data-tab");
      tabButtons.forEach((b) => b.classList.remove("active"));
      tabContents.forEach((c) => c.classList.remove("active"));
      button.classList.add("active");
      document.getElementById(tab).classList.add("active");
    });
  });

  shutdownBtn.addEventListener("click", async () => {
    if (confirm("确认要关闭 Web 服务吗？")) {
      const res = await fetch("/shutdown", { method: "POST" });
      const text = await res.text();
      alert(text);
    }
  });

  // 初始化时应用之前选择的主题
  if (localStorage.getItem("theme") === "dark") {
    document.body.classList.add("dark-theme");
    themeToggleBtn.textContent = "🌞 白天模式";
  } else {
    themeToggleBtn.textContent = "🌙 夜间模式";
  }

  initSortableDashboard(); // 初始化拖拽
  refreshAll(); // 启动轮询
  pushRefreshRate(); // ✅ 初次加载也推送一次
  initChart(); // 初始化折线图
  refreshIntervalId = setInterval(refreshAll, refreshRate);
});

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

// 主刷新函数：每次调用时会拉取最新状态、结构、错误信息，并更新所有 UI 部件
async function refreshAll() {
  // 1️⃣ 并行获取节点状态、任务结构、错误日志（注意是异步 API 请求）
  // - nodeStatuses 会被 loadStatuses 更新
  // - 结构数据会被 loadStructure 使用来渲染 Mermaid 图
  // - errors 会被 loadErrors 更新后用于错误列表渲染
  await Promise.all([
    loadStatuses(),   // 从后端拉取节点运行状态（处理数、等待数、失败数等），更新 nodeStatuses
    loadStructure(),  // 拉取任务结构（有向图），内部调用 renderMermaidFromTaskStructure(...)
    loadErrors()      // 获取最新错误记录，更新 errors[]
  ]);

  // 2️⃣ 渲染任务结构图（Mermaid 图），使用 nodeStatuses 和结构图数据
  renderMermaidFromTaskStructure();

  // 3️⃣ 更新顶部摘要数字（总处理、等待、错误、活跃节点数）
  updateSummary();

  // 4️⃣ 渲染节点状态仪表盘（左中面板中的每个节点卡片）
  renderDashboard();

  // 5️⃣ 更新右侧折线图（任务完成数量随时间变化）
  updateChartData();

  // 6️⃣ 渲染错误表格页面中的内容
  renderErrors();

  // 7️⃣ 更新错误筛选下拉框（选项为所有节点名称）
  populateNodeFilter();

  // 8️⃣ 渲染任务注入页面中的节点选择列表（带运行状态）
  renderNodeList();
}

// 切换主题
function toggleTheme() {
  document.body.classList.toggle("dark-theme");
}
