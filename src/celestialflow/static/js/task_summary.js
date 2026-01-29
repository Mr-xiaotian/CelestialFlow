let summaryData = [];
let previousSummaryDataJSON = "";

const totalSuccessed = document.getElementById("total-successed");
const totalPending = document.getElementById("total-pending");
const totalDuplicated = document.getElementById("total-duplicated");
const totalFailed = document.getElementById("total-failed");
const totalNodes = document.getElementById("total-nodes");
const totalRemain = document.getElementById("total-remain");

async function loadSummary() {
  try {
    const res = await fetch("/api/get_summary");
    summaryData = await res.json();
  } catch (e) {
    console.error("合计数据加载失败", e);
  }
}

function renderSummary() {
  totalSuccessed.textContent = summaryData.total_successed;
  totalPending.textContent = summaryData.total_pending;
  totalFailed.textContent = summaryData.total_failed;
  totalDuplicated.textContent = summaryData.total_duplicated;
  totalNodes.textContent = summaryData.total_nodes;
  totalRemain.textContent = summaryData.total_remain;
}