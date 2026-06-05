/**
 * 节点状态监控模块
 * 负责各节点运行指标（成功、失败、等待、重复、速率等）的实时展示和拖拽排序
 */
// 全局状态
let nodeStatuses = {}; // 当前各节点运行状态
let lastNodeStatuses = {}; // 上一轮状态快照，用于计算增量
let statusRev = -1; // 上次拉取的数据版本号，-1 表示首次拉取全量
let draggingNodeName = null; // 当前拖拽中的节点名
// DOM 元素引用
const dashboardGrid = document.getElementById("dashboard-grid");
/**
 * 获取节点状态卡当前采用的等待值字段。
 * @returns {"tasks_pending" | "total_tasks_pending"} 当前等待统计字段。
 */
function getStatusPendingField() {
    return webConfig?.useTotalPendingInStatus
        ? "total_tasks_pending"
        : "tasks_pending";
}
/**
 * 根据当前配置获取节点状态卡应展示的等待任务数。
 * @param {NodeStatus} status - 节点状态快照
 * @returns {number} 当前节点状态卡使用的等待值
 */
function getDisplayPending(status) {
    const pendingField = getStatusPendingField();
    return Number(status[pendingField] || 0);
}
/**
 * 根据当前配置获取节点状态卡应展示的剩余时间。
 * @param {NodeStatus} status - 节点状态快照
 * @returns {number} 当前节点状态卡使用的剩余时间
 */
function getDisplayRemainingTime(status) {
    return Number(webConfig?.useTotalPendingInStatus
        ? status.total_remaining_time
        : status.remaining_time);
}
/**
 * 获取节点状态卡当前应展示的等待标签 HTML。
 * @returns {string} 等待标签及提示点 HTML
 */
function getPendingLabelHtml() {
    return renderLabelWithTooltip(webConfig?.useTotalPendingInStatus
        ? "status.pendingGlobal"
        : "status.pending", webConfig?.useTotalPendingInStatus
        ? "status.pendingGlobalHelp"
        : "status.pendingHelp");
}
/**
 * 渲染带提示点的统计项标签。
 * @param {string} labelKey - 标签翻译键
 * @param {string} tooltipKey - 提示文案翻译键
 * @returns {string} 统计项标签 HTML
 */
function renderLabelWithTooltip(labelKey, tooltipKey) {
    const label = escapeHtml(t(labelKey));
    const tooltip = escapeHtml(t(tooltipKey));
    return `
    <span class="stat-label-row">
      <span>${label}</span>
      <span class="tooltip-anchor">
        <button
          type="button"
          class="tooltip-trigger"
          aria-label="${tooltip}"
        >i</button>
        <span class="tooltip-bubble" role="tooltip">${tooltip}</span>
      </span>
    </span>
  `;
}
/**
 * 将 elapsed 时间格式化为带颜色的 HTML 字符串
 * @param {number} seconds - 秒数
 * @param {number} successCount - 成功任务数
 * @param {number} failedCount - 失败任务数
 * @param {number} duplicateCount - 重复任务数
 * @returns {string} 带颜色分段的时间 HTML
 */
function formatElapsedDuration(seconds, successCount, failedCount, duplicateCount) {
    const duration = formatDuration(seconds);
    const digitCount = duration.replace(/:/g, "").length;
    if (!digitCount)
        return duration;
    const segments = getElapsedSegments(successCount, failedCount, duplicateCount);
    if (!segments.length)
        return duration;
    const digitClasses = buildElapsedDigitClasses(segments, digitCount);
    return renderElapsedDurationHtml(duration, digitClasses, segments[0].className);
}
/**
 * 根据成功、失败、重复任务数生成有效的 elapsed 颜色段
 * @param {number} successCount - 成功任务数
 * @param {number} failedCount - 失败任务数
 * @param {number} duplicateCount - 重复任务数
 * @returns {Array<{ className: string; count: number }>} 有效颜色段列表
 */
function getElapsedSegments(successCount, failedCount, duplicateCount) {
    return [
        { className: "elapsed-success", count: Math.max(0, successCount || 0) },
        { className: "elapsed-error", count: Math.max(0, failedCount || 0) },
        { className: "elapsed-duplicate", count: Math.max(0, duplicateCount || 0) },
    ].filter((segment) => segment.count > 0);
}
/**
 * 按任务状态比例为时间字符串（HH:MM:SS）的每一位分配颜色类
 * @param {Array<{ className: string; count: number }>} segments - 有效颜色段列表
 * @param {number} digitCount - 需要染色的总位数（不含冒号）
 * @returns {string[]} 按顺序排列的 CSS 类名列表
 */
function buildElapsedDigitClasses(segments, digitCount) {
    if (digitCount <= segments.length) {
        return segments.slice(0, digitCount).map((segment) => segment.className);
    }
    const totalCount = segments.reduce((sum, segment) => sum + segment.count, 0);
    const remainingPool = digitCount - segments.length;
    const exactAllocations = segments.map((segment) => (segment.count / totalCount) * remainingPool);
    const allocations = exactAllocations.map((value) => 1 + Math.floor(value));
    const remainingDigits = digitCount - allocations.reduce((sum, value) => sum + value, 0);
    const sortedIndexes = exactAllocations
        .map((value, index) => ({ index, remainder: value - Math.floor(value) }))
        .sort((a, b) => {
        if (b.remainder !== a.remainder)
            return b.remainder - a.remainder;
        return a.index - b.index;
    });
    for (let i = 0; i < remainingDigits; i++) {
        allocations[sortedIndexes[i % sortedIndexes.length].index] += 1;
    }
    const digitClasses = [];
    allocations.forEach((allocation, index) => {
        for (let i = 0; i < allocation; i++) {
            digitClasses.push(segments[index].className);
        }
    });
    while (digitClasses.length < digitCount) {
        digitClasses.push(segments[segments.length - 1].className);
    }
    return digitClasses;
}
/**
 * 将时间字符串渲染为带颜色 span 的 HTML
 * @param {string} duration - 原始时间字符串
 * @param {string[]} digitClasses - 每一位数字对应的颜色类
 * @param {string} defaultClassName - 当分隔符前没有数字时使用的默认颜色类
 * @returns {string} 渲染后的 HTML 字符串
 */
function renderElapsedDurationHtml(duration, digitClasses, defaultClassName) {
    let digitIndex = 0;
    return duration
        .split("")
        .map((char) => {
        if (char === ":") {
            const leftClassName = digitIndex > 0 ? digitClasses[digitIndex - 1] : defaultClassName;
            return `<span class="${leftClassName}">:</span>`;
        }
        const className = digitClasses[digitIndex] || digitClasses[digitClasses.length - 1];
        digitIndex += 1;
        return `<span class="${className}">${char}</span>`;
    })
        .join("");
}
/**
 * 异步加载最新的节点状态数据
 * 从后端 API 获取节点状态，更新全局变量并同步前端本地历史曲线
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
        appendStatusSnapshotToHistory(Number(body.timestamp || 0), nodeStatuses, lastNodeStatuses);
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
        // 计算增量变化
        const last = lastNodeStatuses[node] || {};
        const displayPending = getDisplayPending(data);
        const lastDisplayPending = getDisplayPending(last);
        const displayRemainingTime = getDisplayRemainingTime(data);
        const addSucceeded = data.tasks_succeeded - (last.tasks_succeeded || 0);
        const addPending = displayPending - lastDisplayPending;
        const addFailed = data.tasks_failed - (last.tasks_failed || 0);
        const addDuplicated = data.tasks_duplicated - (last.tasks_duplicated || 0);
        // 计算执行模式描述
        const executionModeDesc = data.execution_mode === "serial"
            ? data.execution_mode
            : `${data.execution_mode}-${data.max_workers}`;
        // 计算进度
        const total = data.tasks_processed + displayPending;
        const progress = total === 0 ? 0 : Math.floor((data.tasks_processed / total) * 100);
        // 计算四段进度条宽度百分比
        const pctSuccess = total === 0 ? 0 : (data.tasks_succeeded / total) * 100;
        const pctError = total === 0 ? 0 : (data.tasks_failed / total) * 100;
        const pctDuplicate = total === 0 ? 0 : (data.tasks_duplicated / total) * 100;
        const pctPending = total === 0 ? 0 : (displayPending / total) * 100;
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
            <div><div class="stat-label">${getPendingLabelHtml()}</div><div class="stat-value text-pending">${formatWithDelta(displayPending, addPending, "text-delta-pending", "text-delta-pending")}</div></div>
            <div><div class="stat-label">${t("status.error")}</div><div class="stat-value text-error error-clickable" data-node="${escapeHtml(node)}">${formatWithDelta(data.tasks_failed, addFailed, "text-delta-error", "text-delta-error")}</div></div>
            <div><div class="stat-label">${t("status.duplicated")}</div><div class="stat-value text-duplicate">${formatWithDelta(data.tasks_duplicated, addDuplicated, "text-delta-duplicate", "text-delta-duplicate")}</div></div>
            <div><div class="stat-label">${renderLabelWithTooltip("status.stageMode", "status.stageModeHelp")}</div><div class="stat-value">${escapeHtml(data.stage_mode)}</div></div>
            <div><div class="stat-label">${renderLabelWithTooltip("status.executionMode", "status.executionModeHelp")}</div><div class="stat-value">${escapeHtml(executionModeDesc)}</div></div>
          </div>
          <div class="text-sm text-carbon">${t("status.startTime")}${formatTimestamp(data.start_time)}</div>
          <div class="progress-container">
            <div class="progress-header">
              <span>${t("status.completionRate")}</span>
              <span class="time-estimate">
                <span class="elapsed">${formatElapsedDuration(data.elapsed_time, data.tasks_succeeded, data.tasks_failed, data.tasks_duplicated)}</span>
                &lt;
                <span class="remaining">${formatDuration(displayRemainingTime)}</span>,
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
