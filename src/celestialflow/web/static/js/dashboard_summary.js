"use strict";
/**
 * 全局汇总统计模块
 * 负责计算和展示整个图任务的总体进度、成功/失败总量及预计剩余时间
 */
// 全局状态
let summaryRev = -1; // 数据版本号，用于增量拉取
// DOM 元素引用（汇总面板）
const totalSucceeded = document.getElementById("total-succeeded");
const totalPending = document.getElementById("total-pending");
const totalDuplicated = document.getElementById("total-duplicated");
const totalFailed = document.getElementById("total-failed");
const totalNodes = document.getElementById("total-nodes");
const totalRemain = document.getElementById("total-remain");
/**
 * 渲染汇总数据面板
 * 基于已有节点状态聚合展示总成功数、等待数、失败数、重复数、活动节点数；
 * 图级剩余时间由前端基于各节点的 `total_remaining_time` 取最大值得到。
 * @returns {void}
 */
function renderSummary() {
    const statusList = Object.values(nodeStatuses || {}); // 当前全部节点状态快照
    const total_succeeded = statusList.reduce((sum, status) => sum + (status.tasks_succeeded || 0), 0); // 总成功任务数
    const total_pending = statusList.reduce((sum, status) => sum + (status.tasks_pending || 0), 0); // 总等待任务数
    const total_failed = statusList.reduce((sum, status) => sum + (status.tasks_failed || 0), 0); // 总失败任务数
    const total_duplicated = statusList.reduce((sum, status) => sum + (status.tasks_duplicated || 0), 0); // 总重复任务数
    const total_nodes = statusList.reduce((sum, status) => sum + (status.status === 1 ? 1 : 0), 0); // 当前运行中的节点数
    const total_remain = Math.max(...statusList.map(status => status.total_remaining_time || 0), 0); // 图级剩余时间取所有链路估算中的最大值
    totalSucceeded.innerHTML = formatLargeNumber(total_succeeded);
    totalPending.innerHTML = formatLargeNumber(total_pending);
    totalFailed.innerHTML = formatLargeNumber(total_failed);
    totalDuplicated.innerHTML = formatLargeNumber(total_duplicated);
    totalNodes.innerHTML = formatLargeNumber(total_nodes);
    totalRemain.textContent = formatDuration(total_remain);
    // 为错误数添加可点击样式和事件：点击后自动切换到错误日志页并显示全部节点错误
    if (total_failed > 0) {
        totalFailed.classList.add("error-clickable");
        totalFailed.onclick = () => switchToErrorsTab();
    }
    else {
        totalFailed.classList.remove("error-clickable");
        totalFailed.onclick = null;
    }
}
