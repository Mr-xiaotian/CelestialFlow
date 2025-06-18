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

async function refreshAll() {
  await Promise.all([loadStatuses(), loadStructure(), loadErrors()]);
  renderDashboard();
  updateSummary();
  renderMermaidFromTaskStructure();
  renderErrors();
  populateNodeFilter();

  // 新增: 更新任务注入页面的节点列表
  if (typeof renderNodeList === "function") {
    renderNodeList();
  }

  // 在这里调用折线图更新
  const progressData = extractProgressData(nodeStatuses);
  updateChartData(progressData);
}

// 切换主题
function toggleTheme() {
  document.body.classList.toggle("dark-theme");
}
