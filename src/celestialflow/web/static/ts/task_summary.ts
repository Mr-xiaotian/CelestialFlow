let summaryData: Record<string, any> = {};
let previousSummaryDataJSON = "";

const totalSuccessed = document.getElementById("total-successed") as HTMLElement;
const totalPending = document.getElementById("total-pending") as HTMLElement;
const totalDuplicated = document.getElementById("total-duplicated") as HTMLElement;
const totalFailed = document.getElementById("total-failed") as HTMLElement;
const totalNodes = document.getElementById("total-nodes") as HTMLElement;
const totalRemain = document.getElementById("total-remain") as HTMLElement;

/**
 * 异步加载最新的汇总数据
 * 从后端 API 获取任务汇总信息并更新全局变量 summaryData
 */
async function loadSummary() {
  try {
    const res = await fetch("/api/get_summary");
    summaryData = await res.json();
  } catch (e) {
    console.error("合计数据加载失败", e);
  }
}

/**
 * 渲染汇总数据面板
 * 更新页面上的总成功数、等待数、失败数、重复数、节点数和剩余时间
 */
function renderSummary() {
  const {
    total_successed = 0,
    total_pending = 0,
    total_failed = 0,
    total_duplicated = 0,
    total_nodes = 0,
    total_remain = 0,
  } = summaryData || {};

  totalSuccessed.textContent = total_successed;
  totalPending.textContent = total_pending;
  totalFailed.textContent = total_failed;
  totalDuplicated.textContent = total_duplicated;
  totalNodes.textContent = total_nodes;
  totalRemain.textContent = formatDuration(total_remain);
  
  // 为错误数添加可点击样式和事件
  if (total_failed > 0) {
    totalFailed.classList.add("error-clickable");
    totalFailed.onclick = () => jumpToErrorsTabNoFilter();
  } else {
    totalFailed.classList.remove("error-clickable");
    totalFailed.onclick = null;
  }
}

/**
 * 跳转到错误日志标签页（不筛选节点）
 */
function jumpToErrorsTabNoFilter() {
  // 切换到错误日志标签页
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");
  
  tabButtons.forEach((b) => b.classList.remove("active"));
  tabContents.forEach((c) => c.classList.remove("active"));
  
  const errorsTabBtn = document.querySelector('.tab-btn[data-tab="errors"]');
  const errorsTabContent = document.getElementById("errors");
  
  if (errorsTabBtn && errorsTabContent) {
    errorsTabBtn.classList.add("active");
    errorsTabContent.classList.add("active");
  }
  
  // 清除节点筛选（显示全部）
  const nodeFilter = document.getElementById("node-filter") as HTMLSelectElement;
  if (nodeFilter) {
    nodeFilter.value = "";
    nodeFilter.dispatchEvent(new Event("change"));
  }
}
