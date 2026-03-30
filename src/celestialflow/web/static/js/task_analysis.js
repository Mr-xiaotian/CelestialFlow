let analysisData = {};
let analysisRev = -1;
/**
 * 异步加载最新的分析数据
 * 从后端 API 获取分析信息并更新全局变量 analysisData
 */
async function loadAnalysis() {
    try {
        const res = await fetch(`/api/pull_analysis?known_rev=${analysisRev}`);
        const body = await res.json();
        if (body.data === null)
            return false;
        analysisData = body.data;
        analysisRev = body.rev;
        return true;
    }
    catch (e) {
        console.error("分析数据加载失败", e);
        return false;
    }
}
/**
 * 渲染分析信息面板
 * 根据 analysisData 在页面上显示结构类型、DAG 状态、调度模式和层级数量等信息
 */
function renderAnalysisInfo() {
    const container = document.getElementById("analysis-info");
    if (!container)
        return;
    if (!analysisData || Object.keys(analysisData).length === 0) {
        container.innerHTML = `<div class="placeholder">暂无分析信息</div>`;
        return;
    }
    const { isDAG, schedule_mode, class_name, layers_dict = {}, } = analysisData;
    const layerCount = Object.keys(layers_dict).length;
    container.innerHTML = `
    <div class="analysis-row">
      <span class="label">结构类型</span>
      <span class="value">${class_name}</span>
    </div>

    <div class="analysis-row">
      <span class="label">是否 DAG</span>
      <span class="value ${isDAG ? "ok" : "warn"}">
        ${isDAG ? "是（无环）" : "否（存在环）"}
      </span>
    </div>

    <div class="analysis-row">
      <span class="label">调度模式</span>
      <span class="value">${schedule_mode}</span>
    </div>

    <div class="analysis-row">
      <span class="label">层级数量</span>
      <span class="value">${layerCount}</span>
    </div>
  `;
}
