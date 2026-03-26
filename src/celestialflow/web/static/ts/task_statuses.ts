type NodeStatus = {
  status: number;
  tasks_processed: number;
  tasks_pending: number;
  tasks_successed: number;
  add_tasks_successed: number;
  add_tasks_pending: number;
  tasks_failed: number;
  add_tasks_failed: number;
  tasks_duplicated: number;
  add_tasks_duplicated: number;
  stage_mode: string;
  execution_mode: string;
  start_time: number;
  elapsed_time: number;
  remaining_time: number;
  task_avg_time: string;
};

let nodeStatuses: Record<string, NodeStatus> = {};
let statusRev = -1;
let draggingNodeName: string | null = null;

const dashboardGrid = document.getElementById("dashboard-grid") as HTMLElement;

/**
 * 异步加载最新的节点状态数据
 * 从后端 API 获取节点状态并更新全局变量 nodeStatuses
 */
async function loadStatuses(): Promise<boolean> {
  try {
    const res = await fetch(`/api/pull_status?known_rev=${statusRev}`);
    const body = await res.json();
    if (body.data === null) return false;
    nodeStatuses = body.data;
    statusRev = body.rev;
    return true;
  } catch (e) {
    console.error("状态加载失败", e);
    return false;
  }
}

/**
 * 初始化仪表盘的拖拽排序功能
 * 如果是移动端则跳过初始化
 */
function initSortableDashboard() {
  if (isMobile()) {
    console.log("移动端，禁用拖动功能");
    return;
  }

  const el = document.getElementById("dashboard-grid") as HTMLElement;
  new Sortable(el, {
    animation: 300,
    easing: "cubic-bezier(0.25, 1, 0.5, 1)",
    ghostClass: "sortable-ghost",
    chosenClass: "sortable-chosen",
    dragClass: "sortable-dragging",
    onStart: function (evt) {
      const title = evt.item.querySelector(".card-title").textContent;
      draggingNodeName = title;
    },
    onEnd: function (evt) {
      draggingNodeName = null;
    },
  });
}
/**
 * 根据排序顺序和节点状态生成 HTML，显示进度条、统计数据等
 */
function renderDashboard() {
  dashboardGrid.innerHTML = "";

  for (const [node, data] of Object.entries(nodeStatuses)) {
    if (node === draggingNodeName) continue; // 正在拖动时，不渲染它

    // 计算进度
    const total = data.tasks_processed + data.tasks_pending;
    const progress = total === 0 ? 0 : Math.floor((data.tasks_processed / total) * 100);

    // 计算四段进度条宽度百分比
    const pctSuccess   = total === 0 ? 0 : (data.tasks_successed  / total) * 100;
    const pctError     = total === 0 ? 0 : (data.tasks_failed     / total) * 100;
    const pctDuplicate = total === 0 ? 0 : (data.tasks_duplicated / total) * 100;
    const pctPending   = total === 0 ? 0 : (data.tasks_pending    / total) * 100;

    // 根据 status 决定 badge 样式和文本
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
    card.className = "node-card";
    card.innerHTML = `
          <div class="card-header">
            <h3 class="card-title">${escapeHtml(node)}</h3>
            <span class="badge ${badgeClass}">${badgeText}</span>
          </div>
          <div class="stat-grid">
            <div><div class="stat-label">成功</div><div class="stat-value text-success">${formatWithDelta(
              data.tasks_successed,
              data.add_tasks_successed,
              "text-delta-pos",
              "text-delta-neg"
            )}</div></div>
            <div><div class="stat-label">等待中</div><div class="stat-value text-pending">${formatWithDelta(
              data.tasks_pending,
              data.add_tasks_pending,
              "text-delta-pending",
              "text-delta-pending"
            )}</div></div>
            <div><div class="stat-label">错误</div><div class="stat-value text-error error-clickable" data-node="${escapeHtml(node)}">${formatWithDelta(
              data.tasks_failed,
              data.add_tasks_failed,
              "text-delta-neg",
              "text-delta-pos"
            )}</div></div>
            <div><div class="stat-label">重复</div><div class="stat-value text-duplicate">${formatWithDelta(
              data.tasks_duplicated,
              data.add_tasks_duplicated,
              "text-delta-duplicate",
              "text-delta-duplicate"
            )}</div></div>
            <div><div class="stat-label">节点模式</div><div class="stat-value">${escapeHtml(data.stage_mode)}</div></div>
            <div><div class="stat-label">运行模式</div><div class="stat-value">${escapeHtml(data.execution_mode)}</div></div>
          </div>
          <div class="text-sm text-gray">开始时间: ${formatTimestamp(data.start_time)}</div>
          <div class="progress-container">
            <div class="progress-header">
              <span>任务完成率</span>
              <span class="time-estimate">
                <span class="elapsed">${formatDuration(data.elapsed_time)}</span>
                &lt;
                <span class="remaining">${formatDuration(data.remaining_time)}</span>,
                <span class="task-avg-time">${data.task_avg_time}</span>,
                <span>${progress}%</span>
              </span>
            </div>
            <div class="progress-bar">
              <div class="progress-segment seg-success"   style="width: ${pctSuccess.toFixed(1)}%"></div>
              <div class="progress-segment seg-error"     style="width: ${pctError.toFixed(1)}%"></div>
              <div class="progress-segment seg-duplicate" style="width: ${pctDuplicate.toFixed(1)}%"></div>
              <div class="progress-segment seg-pending"   style="width: ${pctPending.toFixed(1)}%"></div>
            </div>
          </div>
        `;

    // 为错误数添加点击事件（跳转到错误日志页面并筛选该节点）
    const errorValue = card.querySelector(".error-clickable");
    if (errorValue) {
      errorValue.addEventListener("click", (e) => {
        e.stopPropagation(); // 阻止事件冒泡
        switchToErrorsTab(node); // 使用原始 node 值（非转义）作为筛选器的值
      });
    }
    
    dashboardGrid.appendChild(card);
  }
}

