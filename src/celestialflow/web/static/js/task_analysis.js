/**
 * 拓扑分析模块
 * 负责拉取和展示图结构的拓扑分析结果（如是否为 DAG、调度模式等）
 */
// 全局状态
let analysisData = {}; // 拓扑分析数据
let analysisRev = -1; // 数据版本号，用于增量拉取
/**
 * 异步加载最新的分析数据
 * 从后端 API 获取分析信息并更新全局变量 analysisData
 * @returns {Promise<boolean>} 当分析数据版本发生变化并成功更新时返回 `true`，否则返回 `false`。
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
 * @returns {void}
 */
function renderAnalysisInfo() {
    const container = document.getElementById("analysis-info");
    if (!container)
        return;
    if (!analysisData || Object.keys(analysisData).length === 0) {
        container.innerHTML = `<div class="empty-placeholder">${t("analysis.noData")}</div>`;
        return;
    }
    const { isDAG, schedule_mode, class_name, layers_dict = {}, } = analysisData;
    const layerCount = Object.keys(layers_dict).length;
    container.innerHTML = `
    <div class="analysis-row">
      <span class="analysis-label">${t("analysis.structType")}</span>
      <span class="analysis-value">${class_name}</span>
    </div>

    <div class="analysis-row">
      <span class="analysis-label">${t("analysis.isDAG")}</span>
      <span class="analysis-value ${isDAG ? "ok" : "warn"}">
        ${isDAG ? t("analysis.dagYes") : t("analysis.dagNo")}
      </span>
    </div>

    <div class="analysis-row">
      <span class="analysis-label">${t("analysis.scheduleMode")}</span>
      <span class="analysis-value">${schedule_mode}</span>
    </div>

    <div class="analysis-row">
      <span class="analysis-label">${t("analysis.layerCount")}</span>
      <span class="analysis-value">${layerCount}</span>
    </div>
  `;
}
