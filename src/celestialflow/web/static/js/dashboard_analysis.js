"use strict";
/**
 * 拓扑分析模块
 * 负责拉取和展示图结构的拓扑分析结果（如是否为 DAG、调度模式等）
 */
// 全局状态
let analysisData = {}; // 拓扑分析数据
let analysisRev = -1; // 数据版本号，用于增量拉取
let analysisRequestSeq = 0; // 请求序列号，防止旧分析响应覆盖新结果
/**
 * 渲染带提示点的分析项标签。
 * @param {string} labelKey - 标签翻译键
 * @param {string} tooltipKey - 提示文案翻译键
 * @returns {string} 标签 HTML
 */
function renderAnalysisLabelWithTooltip(labelKey, tooltipKey) {
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
 * 异步加载最新的分析数据
 * 从后端 API 获取分析信息并更新全局变量 analysisData
 * @returns {Promise<boolean>} 当分析数据版本发生变化并成功更新时返回 `true`，否则返回 `false`。
 */
async function loadAnalysis() {
    try {
        const requestSeq = ++analysisRequestSeq; // 为当前分析请求分配递增序号
        const res = await fetch(`/api/pull_analysis?known_rev=${analysisRev}`);
        const body = (await res.json());
        if (requestSeq !== analysisRequestSeq)
            return false; // 丢弃已过时请求的返回结果
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
    const container = document.getElementById("analysis-info"); // 分析卡片内容容器
    if (!container)
        return;
    if (!analysisData || Object.keys(analysisData).length === 0) {
        container.innerHTML = `<div class="empty-placeholder">${t("analysis.noData")}</div>`;
        return;
    }
    const { isDAG, scheduleMode, className, layersDict = {} } = analysisData; // 解构常用分析字段
    const layerCount = Object.keys(layersDict).length; // 通过层级字典键数推导层级总数
    // 统一构建四行展示内容，避免分散更新不同 DOM 节点。
    container.innerHTML = `
    <div class="analysis-row">
      <span class="analysis-label">${renderAnalysisLabelWithTooltip("analysis.structType", "analysis.structTypeHelp")}</span>
      <span class="analysis-value">${className}</span>
    </div>

    <div class="analysis-row">
      <span class="analysis-label">${t("analysis.isDAG")}</span>
      <span class="analysis-value ${isDAG ? "ok" : "warn"}">
        ${isDAG ? t("analysis.dagYes") : t("analysis.dagNo")}
      </span>
    </div>

    <div class="analysis-row">
      <span class="analysis-label">${renderAnalysisLabelWithTooltip("analysis.scheduleMode", "analysis.scheduleModeHelp")}</span>
      <span class="analysis-value">${scheduleMode}</span>
    </div>

    <div class="analysis-row">
      <span class="analysis-label">${t("analysis.layerCount")}</span>
      <span class="analysis-value">${layerCount}</span>
    </div>
  `;
}
