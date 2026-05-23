/**
 * 节点状态监控模块
 * 负责各节点运行指标（成功、失败、等待、重复、速率等）的实时展示和拖拽排序
 */
// 全局状态
let nodeStatuses = {}; // 当前各节点运行状态
let lastNodeStatuses = {}; // 上一轮状态快照，用于计算增量
let statusRev = -1; // 数据版本号，用于增量拉取
let draggingNodeName = null; // 当前拖拽中的节点名
// DOM 元素引用
const dashboardGrid = document.getElementById("dashboard-grid");
/**
 * 异步加载最新的节点状态数据
 * 从后端 API 获取节点状态并更新全局变量 nodeStatuses
 * @returns {Promise<boolean>} 当状态版本发生变化并成功更新时返回 `true`，否则返回 `false`。
 */
async function loadStatuses() {
    try {
        const res = await fetch(`/api/pull_status?known_rev=${statusRev}`);
        const body = await res.json();
        if (body.data === null)
            return false;
        lastNodeStatuses = nodeStatuses;
        nodeStatuses = body.data;
        statusRev = body.rev;
        return true;
    }
    catch (e) {
        console.error("状态加载失败", e);
        return false;
    }
}
/**
 * 初始化仪表盘的拖拽排序功能
 * 如果是移动端则跳过初始化
 * @returns {void}
 */
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
 * 渲染时会跳过当前正在被用户拖拽的卡片，防止闪烁
 * @returns {void}
 */
function renderDashboard() {
    dashboardGrid.innerHTML = "";
    if (!Object.keys(nodeStatuses).length) {
        dashboardGrid.innerHTML = `<div class="empty-placeholder" style="grid-column: 1 / -1;">${t("status.noData")}</div>`;
        return;
    }
    for (const [node, data] of Object.entries(nodeStatuses)) {
        if (node === draggingNodeName)
            continue; // 正在拖动时，不渲染它
        const last = lastNodeStatuses[node] || {};
        const addSucceeded = data.tasks_succeeded - (last.tasks_succeeded || 0);
        const addPending = data.tasks_pending - (last.tasks_pending || 0);
        const addFailed = data.tasks_failed - (last.tasks_failed || 0);
        const addDuplicated = data.tasks_duplicated - (last.tasks_duplicated || 0);
        // 计算进度
        const total = data.tasks_processed + data.tasks_pending;
        const progress = total === 0 ? 0 : Math.floor((data.tasks_processed / total) * 100);
        // 计算四段进度条宽度百分比
        const pctSuccess = total === 0 ? 0 : (data.tasks_succeeded / total) * 100;
        const pctError = total === 0 ? 0 : (data.tasks_failed / total) * 100;
        const pctDuplicate = total === 0 ? 0 : (data.tasks_duplicated / total) * 100;
        const pctPending = total === 0 ? 0 : (data.tasks_pending / total) * 100;
        const card = document.createElement("div");
        if (data.status === 1) {
            card.className = "node-card status-running";
        }
        else if (data.status === 2) {
            card.className = "node-card status-stopped";
        }
        else {
            card.className = "node-card";
        }
        card.innerHTML = `
          <div class="card-header">
            <h3 class="card-title">${escapeHtml(node)}</h3>
          </div>
          <div class="stat-grid">
            <div><div class="stat-label">${t("status.succeeded")}</div><div class="stat-value text-success">${formatWithDelta(data.tasks_succeeded, addSucceeded, "text-delta-success", "text-delta-success")}</div></div>
            <div><div class="stat-label">${t("status.pending")}</div><div class="stat-value text-pending">${formatWithDelta(data.tasks_pending, addPending, "text-delta-pending", "text-delta-pending")}</div></div>
            <div><div class="stat-label">${t("status.error")}</div><div class="stat-value text-error error-clickable" data-node="${escapeHtml(node)}">${formatWithDelta(data.tasks_failed, addFailed, "text-delta-error", "text-delta-error")}</div></div>
            <div><div class="stat-label">${t("status.duplicated")}</div><div class="stat-value text-duplicate">${formatWithDelta(data.tasks_duplicated, addDuplicated, "text-delta-duplicate", "text-delta-duplicate")}</div></div>
            <div><div class="stat-label">${t("status.stageMode")}</div><div class="stat-value">${escapeHtml(data.stage_mode)}</div></div>
            <div><div class="stat-label">${t("status.executionMode")}</div><div class="stat-value">${escapeHtml(data.execution_mode)}</div></div>
          </div>
          <div class="text-sm text-carbon">${t("status.startTime")}${formatTimestamp(data.start_time)}</div>
          <div class="progress-container">
            <div class="progress-header">
              <span>${t("status.completionRate")}</span>
              <span class="time-estimate">
                <span class="elapsed">${formatElapsedDuration(data.elapsed_time, data.tasks_succeeded, data.tasks_failed, data.tasks_duplicated)}</span>
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
