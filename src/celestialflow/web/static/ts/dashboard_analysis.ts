/**
 * 拓扑分析模块
 * 负责拉取和展示图结构的拓扑分析结果（如是否为 DAG、调度模式等）
 */

type AnalysisData = {
  name: string; // 任务图名称
  startTime: number; // 任务图启动时间戳
  className: string; // 图结构分类名称
  isDAG: boolean; // 当前任务图是否为 DAG
  scheduleMode: string; // 图级调度模式名称
  layersDict: Record<string, unknown>; // 层级分析结果，键数量可用于统计层数
};

// 全局状态
let analysisData: AnalysisData | null = null; // 拓扑分析数据；未加载时为 null
let analysisRev = -1; // 数据版本号，用于增量拉取
let analysisRequestSeq = 0; // 请求序列号，防止旧分析响应覆盖新结果

/**
 * 异步加载最新的分析数据
 * 从后端 API 获取分析信息并更新全局变量 analysisData
 * @returns {Promise<boolean>} 当分析数据版本发生变化并成功更新时返回 `true`，否则返回 `false`。
 */
async function loadAnalysis(): Promise<boolean> {
  try {
    const requestSeq = ++analysisRequestSeq; // 为当前分析请求分配递增序号
    const res = await fetch(`/api/pull_analysis?known_rev=${analysisRev}`);
    const body = (await res.json()) as AnalysisPullResponse;
    if (requestSeq !== analysisRequestSeq) return false; // 丢弃已过时请求的返回结果
    const nextRev = Number(body.rev);
    const previousAnalysisData = analysisData;
    analysisData = body.data;
    const changed =
      analysisRev !== nextRev || previousAnalysisData !== analysisData;
    analysisRev = nextRev;
    return changed;
  } catch (e) {
    console.error("分析数据加载失败", e);
    return false;
  }
}

/**
 * 渲染分析信息面板
 * 根据 analysisData 在页面上显示结构类型、DAG 状态、调度模式和层级数量等信息
 * @returns {void}
 */
function renderAnalysisInfo(): void {
  const container = document.getElementById("analysis-info") as HTMLElement; // 分析卡片内容容器
  if (!container) return;

  if (!analysisData) {
    container.innerHTML = `<div class="empty-placeholder">${t("analysis.noData")}</div>`;
    return;
  }

  const { name, startTime, isDAG, scheduleMode, className, layersDict } =
    analysisData; // 解构常用分析字段

  const layerCount = Object.keys(layersDict).length; // 通过层级字典键数推导层级总数
  const startTimeText = startTime > 0 ? formatTimestamp(startTime) : "-";

  // 统一构建分析信息内容，避免分散更新不同 DOM 节点。
  container.innerHTML = `
    <div class="analysis-row">
      <span class="analysis-label">${t("analysis.graphName")}</span>
      <span class="analysis-value">${escapeHtml(name)}</span>
    </div>

    <div class="analysis-row">
      <span class="analysis-label">${t("analysis.startTime")}</span>
      <span class="analysis-value">${startTimeText}</span>
    </div>

    <div class="analysis-row">
      <span class="analysis-label">${renderLabelWithTooltip("analysis.structType", "analysis.structTypeHelp")}</span>
      <span class="analysis-value">${escapeHtml(className)}</span>
    </div>

    <div class="analysis-row">
      <span class="analysis-label">${t("analysis.isDAG")}</span>
      <span class="analysis-value ${isDAG ? "ok" : "warn"}">
        ${isDAG ? t("analysis.dagYes") : t("analysis.dagNo")}
      </span>
    </div>

    <div class="analysis-row">
      <span class="analysis-label">${renderLabelWithTooltip("analysis.scheduleMode", "analysis.scheduleModeHelp")}</span>
      <span class="analysis-value">${escapeHtml(scheduleMode)}</span>
    </div>

    <div class="analysis-row">
      <span class="analysis-label">${t("analysis.layerCount")}</span>
      <span class="analysis-value">${layerCount}</span>
    </div>
  `;
}
