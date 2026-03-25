let summaryData = {};
let summaryRev = -1;
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
        const res = await fetch(`/api/pull_summary?known_rev=${summaryRev}`);
        const body = await res.json();
        if (body.data === null)
            return false;
        summaryData = body.data;
        summaryRev = body.rev;
        return true;
    }
    catch (e) {
        console.error("合计数据加载失败", e);
        return false;
    }
}
/**
 * 渲染汇总数据面板
 * 更新页面上的总成功数、等待数、失败数、重复数、节点数和剩余时间
 */
function renderSummary() {
    const { total_successed = 0, total_pending = 0, total_failed = 0, total_duplicated = 0, total_nodes = 0, total_remain = 0, } = summaryData || {};
    totalSuccessed.innerHTML = formatLargeNumber(total_successed);
    totalPending.innerHTML = formatLargeNumber(total_pending);
    totalFailed.innerHTML = formatLargeNumber(total_failed);
    totalDuplicated.innerHTML = formatLargeNumber(total_duplicated);
    totalNodes.innerHTML = formatLargeNumber(total_nodes);
    totalRemain.textContent = formatDuration(total_remain);
    // 为错误数添加可点击样式和事件
    if (total_failed > 0) {
        totalFailed.classList.add("error-clickable");
        totalFailed.onclick = () => switchToErrorsTab();
    }
    else {
        totalFailed.classList.remove("error-clickable");
        totalFailed.onclick = null;
    }
}
