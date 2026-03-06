let summaryData = [];
let previousSummaryDataJSON = "";

const totalSuccessed = document.getElementById("total-successed");
const totalPending = document.getElementById("total-pending");
const totalDuplicated = document.getElementById("total-duplicated");
const totalFailed = document.getElementById("total-failed");
const totalNodes = document.getElementById("total-nodes");
const totalRemain = document.getElementById("total-remain");

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
}