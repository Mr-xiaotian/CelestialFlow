let nodeStatuses = {};
let progressChart = null;
let draggingNodeName = null;
let hiddenNodes = new Set(
  JSON.parse(localStorage.getItem("hiddenNodes") || "[]")
);

const dashboardGrid = document.getElementById("dashboard-grid");
const totalProcessed = document.getElementById("total-processed");
const totalPending = document.getElementById("total-pending");
const totalErrors = document.getElementById("total-errors");
const totalNodes = document.getElementById("total-nodes");

async function loadStatuses() {
  try {
    const res = await fetch("/api/get_status");
    nodeStatuses = await res.json();
  } catch (e) {
    console.error("状态加载失败", e);
  }
}

function initSortableDashboard() {
  if (isMobile()) {
    console.log("移动端，禁用拖动功能");
    return;
  }

  const el = document.getElementById("dashboard-grid");
  new Sortable(el, {
    animation: 300,
    easing: "cubic-bezier(0.25, 1, 0.5, 1)",
    ghostClass: "sortable-ghost",
    chosenClass: "sortable-chosen",
    onStart: function (evt) {
      const title = evt.item.querySelector(".card-title").textContent;
      draggingNodeName = title;
    },
    onEnd: function (evt) {
      saveDashboardOrder();
      draggingNodeName = null;
    },
  });
}

function saveDashboardOrder() {
  const order = Array.from(
    document.querySelectorAll("#dashboard-grid .card-title")
  ).map((el) => el.textContent);
  localStorage.setItem("dashboardOrder", JSON.stringify(order));
}

function getDashboardOrder() {
  return JSON.parse(localStorage.getItem("dashboardOrder") || "[]");
}

function renderDashboard() {
  dashboardGrid.innerHTML = "";

  // 获取用户排序顺序
  const order = getDashboardOrder();
  const orderedEntries = Object.entries(nodeStatuses).sort((a, b) => {
    const indexA = order.indexOf(a[0]);
    const indexB = order.indexOf(b[0]);
    if (indexA === -1 && indexB === -1) return 0;
    if (indexA === -1) return 1;
    if (indexB === -1) return -1;
    return indexA - indexB;
  });

  for (const [node, data] of orderedEntries) {
    if (node === draggingNodeName) continue; // 正在拖动时，不渲染它

    // ✅ 计算进度
    const progress =
      data.tasks_processed + data.tasks_pending === 0
        ? 0
        : Math.floor(
            ((data.tasks_processed + data.tasks_failed) /
              (data.tasks_processed + data.tasks_failed + data.tasks_pending)) *
              100
          );

    // ✅ 根据 status 决定 badge 样式和文本
    let badgeClass = "badge-inactive";
    let badgeText = "未运行";
    if (data.status === 1) {
      badgeClass = "badge-running";
      badgeText = "运行中";
    } else if (data.status === 2) {
      badgeClass = "badge-completed";
      badgeText = "已停止";
    }

    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
          <div class="card-header">
            <h3 class="card-title">${node}</h3>
            <span class="badge ${badgeClass}">${badgeText}</span>
          </div>
          <div class="stats-grid">
            <div><div class="stat-label">已处理</div><div class="stat-value">${formatWithDelta(
              data.tasks_processed,
              data.add_tasks_processed
            )}</div></div>
            <div><div class="stat-label">等待中</div><div class="stat-value">${formatWithDelta(
              data.tasks_pending,
              data.add_tasks_pending
            )}</div></div>
            <div><div class="stat-label">错误</div><div class="stat-value text-red">${formatWithDelta(
              data.tasks_failed,
              data.add_tasks_failed
            )}</div></div>
            <div><div class="stat-label">重复</div><div class="stat-value text-yellow">${formatWithDelta(
              data.tasks_duplicated,
              data.add_tasks_duplicated
            )}</div></div>
            <div><div class="stat-label">节点模式</div><div class="stat-value">${
              data.stage_mode
            }</div></div>
            <div><div class="stat-label">运行模式</div><div class="stat-value">${
              data.execution_mode
            }</div></div>
          </div>
          <div class="text-sm text-gray">开始时间: ${data.start_time}</div>
          <div class="progress-container">
            <div class="progress-header">
              <span>任务完成率</span>
              <span class="time-estimate">
                <span class="elapsed">${data.elapsed_time}</span>
                &lt; 
                <span class="remaining">${data.remaining_time}</span>, 
                <span class="task-avg-time">${data.task_avg_time}</span>, 
                <span>${progress}%</span>
              </span>
            </div>
            <div class="progress-bar">
              <div class="progress-value" style="width: ${progress}%"></div>
            </div>
          </div>
        `;
    dashboardGrid.appendChild(card);
  }
}

function updateSummary() {
  let processed = 0,
    pending = 0,
    error = 0,
    active = 0;
  Object.values(nodeStatuses).forEach((s) => {
    processed += s.tasks_processed;
    pending += s.tasks_pending;
    error += s.tasks_failed;
    if (s.status === 1) active++;
  });
  totalProcessed.textContent = processed;
  totalPending.textContent = pending;
  totalErrors.textContent = error;
  totalNodes.textContent = active;
}

function initChart() {
  const ctx = document.getElementById("node-progress-chart").getContext("2d");
  progressChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [],
    },
    options: {
      animation: false, // 直接关掉所有动画
      responsive: true,
      plugins: {
        legend: {
          display: true,
          onClick: (e, legendItem, legend) => {
            const index = legendItem.datasetIndex;
            const nodeName = progressChart.data.datasets[index].label;

            // 更新隐藏集合
            if (hiddenNodes.has(nodeName)) {
              hiddenNodes.delete(nodeName);
            } else {
              hiddenNodes.add(nodeName);
            }

            // 持久化保存到 localStorage
            localStorage.setItem(
              "hiddenNodes",
              JSON.stringify([...hiddenNodes])
            );

            // 继续默认 Chart.js 的隐藏逻辑
            const meta = legend.chart.getDatasetMeta(index);
            meta.hidden =
              meta.hidden === null
                ? !legend.chart.data.datasets[index].hidden
                : null;
            legend.chart.update();
          },
        },
      },
      interaction: {
        intersect: false,
        mode: "index",
      },
      scales: {
        x: { display: true, title: { display: true, text: "时间" } },
        y: { display: true, title: { display: true, text: "完成任务数" } },
      },
    },
  });
}

function updateChartData(nodeDataMap) {
  const datasets = Object.entries(nodeDataMap).map(([node, data], index) => ({
    label: node,
    data: data,
    borderColor: getColor(index),
    fill: false,
    tension: 0.3,
    hidden: hiddenNodes.has(node), // 根据用户之前的选择
  }));

  const firstNode = Object.keys(nodeDataMap)[0];
  progressChart.data.labels = nodeDataMap[firstNode]?.map((p) =>
    new Date(p.x * 1000).toLocaleTimeString()
  );
  progressChart.data.datasets = datasets;

  progressChart.update();
}