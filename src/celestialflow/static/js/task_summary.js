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