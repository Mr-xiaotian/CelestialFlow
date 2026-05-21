/**
 * 全局汇总统计模块
 * 负责计算和展示整个图任务的总体进度、成功/失败总量及预计剩余时间
 */

// 全局状态
let summaryData: Record<string, any> = {}; // 汇总统计数据
let summaryRev = -1; // 数据版本号，用于增量拉取

// DOM 元素引用（汇总面板）
const totalSucceeded = document.getElementById("total-succeeded") as HTMLElement;
const totalPending = document.getElementById("total-pending") as HTMLElement;
const totalDuplicated = document.getElementById("total-duplicated") as HTMLElement;
const totalFailed = document.getElementById("total-failed") as HTMLElement;
const totalNodes = document.getElementById("total-nodes") as HTMLElement;
const totalRemain = document.getElementById("total-remain") as HTMLElement;

/**
 * 异步加载最新的汇总数据
 * 从后端 API 获取任务汇总信息并更新全局变量 summaryData
 */
async function loadSummary(): Promise<boolean> {
  try {
    const res = await fetch(`/api/pull_summary?known_rev=${summaryRev}`);
    const body = await res.json();
    if (body.data === null) return false;
    summaryData = body.data;
    summaryRev = body.rev;
    return true;
  } catch (e) {
    console.error("合计数据加载失败", e);
    return false;
  }
}

/**
 * 渲染汇总数据面板
 * 更新页面上的总成功数、等待数、失败数、重复数、节点数和剩余时间
 */
function renderSummary() {
  const {
    total_succeeded = 0,
    total_pending = 0,
    total_failed = 0,
    total_duplicated = 0,
    total_nodes = 0,
    total_remain = 0,
  } = summaryData || {};

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
  } else {
    totalFailed.classList.remove("error-clickable");
    totalFailed.onclick = null;
  }
}

