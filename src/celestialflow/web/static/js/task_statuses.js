let nodeStatuses = {};
let previousNodeStatusesJSON = "";
let draggingNodeName = null;
const dashboardGrid = document.getElementById("dashboard-grid");
/**
 * 异步加载最新的节点状态数据
 * 从后端 API 获取节点状态并更新全局变量 nodeStatuses
 */
async function loadStatuses() {
    try {
        const res = await fetch("/api/get_status");
        nodeStatuses = await res.json();
    }
    catch (e) {
        console.error("状态加载失败", e);
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
        if (node === draggingNodeName)
            continue; // 正在拖动时，不渲染它
        // 计算进度
        const progress = data.tasks_processed + data.tasks_pending === 0
            ? 0
            : Math.floor((data.tasks_processed / (data.tasks_processed + data.tasks_pending)) * 100);
        // 根据 status 决定 badge 样式和文本
        let badgeClass = "badge-inactive";
        let badgeText = "未运行";
        if (data.status === 1) {
            badgeClass = "badge-running";
            badgeText = "运行中";
        }
        else if (data.status === 2) {
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
            <div><div class="stat-label">已成功</div><div class="stat-value">${formatWithDelta(data.tasks_successed, data.add_tasks_successed)}</div></div>
            <div><div class="stat-label">等待中</div><div class="stat-value">${formatWithDelta(data.tasks_pending, data.add_tasks_pending)}</div></div>
            <div><div class="stat-label">错误</div><div class="stat-value text-red error-clickable" data-node="${node}">${formatWithDelta(data.tasks_failed, data.add_tasks_failed)}</div></div>
            <div><div class="stat-label">重复</div><div class="stat-value text-yellow">${formatWithDelta(data.tasks_duplicated, data.add_tasks_duplicated)}</div></div>
            <div><div class="stat-label">节点模式</div><div class="stat-value">${data.stage_mode}</div></div>
            <div><div class="stat-label">运行模式</div><div class="stat-value">${data.execution_mode}</div></div>
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
              <div class="progress-value" style="width: ${progress}%"></div>
            </div>
          </div>
        `;
        // 为错误数添加点击事件（跳转到错误日志页面并筛选该节点）
        const errorValue = card.querySelector(".error-clickable");
        if (errorValue) {
            errorValue.addEventListener("click", (e) => {
                e.stopPropagation(); // 阻止事件冒泡
                const nodeName = errorValue.getAttribute("data-node");
                jumpToErrorsTab(nodeName);
            });
        }
        dashboardGrid.appendChild(card);
    }
}
/**
 * 跳转到错误日志标签页并筛选指定节点
 * @param {string} nodeName - 要筛选的节点名称
 */
function jumpToErrorsTab(nodeName) {
    // 1. 切换到错误日志标签页
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");
    tabButtons.forEach((b) => b.classList.remove("active"));
    tabContents.forEach((c) => c.classList.remove("active"));
    // 激活错误日志标签
    const errorsTabBtn = document.querySelector('.tab-btn[data-tab="errors"]');
    const errorsTabContent = document.getElementById("errors");
    if (errorsTabBtn && errorsTabContent) {
        errorsTabBtn.classList.add("active");
        errorsTabContent.classList.add("active");
    }
    // 2. 设置节点筛选器的值并触发筛选
    const nodeFilter = document.getElementById("node-filter");
    if (nodeFilter) {
        nodeFilter.value = nodeName;
        // 触发 change 事件
        nodeFilter.dispatchEvent(new Event("change"));
    }
}
