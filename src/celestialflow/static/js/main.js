let refreshRate = 5000;
let refreshIntervalId = null;

const refreshSelect = document.getElementById("refresh-interval");
const themeToggleBtn = document.getElementById("theme-toggle");
// const shutdownBtn = document.getElementById("shutdown-btn");
const tabButtons = document.querySelectorAll(".tab-btn");
const tabContents = document.querySelectorAll(".tab-content");

document.addEventListener("DOMContentLoaded", async () => {
  const savedRate = parseInt(localStorage.getItem("refreshRate"));
  if (!isNaN(savedRate)) {
    refreshRate = savedRate;
    refreshSelect.value = savedRate.toString();
  }

  refreshSelect.addEventListener("change", () => {
    refreshRate = parseInt(refreshSelect.value);
    localStorage.setItem("refreshRate", refreshRate); // 保存设置
    clearInterval(refreshIntervalId);
    refreshIntervalId = setInterval(refreshAll, refreshRate);
    pushRefreshRate(); // 立即同步到后端
  });

  themeToggleBtn.addEventListener("click", () => {
    const isDark = toggleDarkTheme();
    localStorage.setItem("theme", isDark ? "dark" : "light");
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
      document.getElementById(tab).classList.add("active");
    });
  });

  // shutdownBtn.addEventListener("click", async () => {
  //   if (confirm("确认要关闭 Web 服务吗？")) {
  //     const res = await fetch("/shutdown", { method: "POST" });
  //     const text = await res.text();
  //     alert(text);
  //   }
  // });

  // 初始化时应用之前选择的主题
  if (localStorage.getItem("theme") === "dark") {
    document.body.classList.add("dark-theme");
    themeToggleBtn.textContent = "🌞 白天模式";
  } else {
    themeToggleBtn.textContent = "🌙 夜间模式";
  }

  initSortableDashboard(); // 初始化拖拽
  refreshAll(); // 启动轮询
  pushRefreshRate(); // 初次加载也推送一次
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
