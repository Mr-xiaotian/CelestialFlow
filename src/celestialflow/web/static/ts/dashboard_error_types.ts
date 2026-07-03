/**
 * 错误类型分布卡片
 * 负责节点筛选、聚合数据拉取以及 doughnut 图和图例渲染
 */

let errorTypeCounts: ErrorTypeCount[] = []; // 当前筛选条件下的错误类型聚合结果
let errorTypeCountsRev = -1; // 错误类型聚合数据版本号
let errorTypeCountsQueryKey = ""; // 最近一次请求使用的筛选条件缓存键
let errorTypeRequestSeq = 0; // 请求序号，避免慢响应覆盖新筛选结果
let errorTypeChart: ChartInstance | null = null; // 错误类型分布图实例

const ERROR_TYPE_COLORS = [
  "#2563eb",
  "#16a34a",
  "#dc2626",
  "#d97706",
  "#7c3aed",
  "#0891b2",
  "#db2777",
  "#4f46e5",
];

/**
 * 获取错误类型图表的节点筛选器。
 * @returns {HTMLSelectElement | null} 节点筛选下拉框。
 */
function getErrorTypeNodeFilter(): HTMLSelectElement | null {
  return document.getElementById(
    "error-type-node-filter",
  ) as HTMLSelectElement | null;
}

/**
 * 将错误类型名称归一为可展示文本。
 * @param {string} errorType - 原始错误类型名称。
 * @returns {string} 归一化后的展示名称。
 */
function getErrorTypeLabel(errorType: string): string {
  return errorType.trim() || t("errorTypes.unknown");
}

/**
 * 按索引获取稳定的扇区颜色。
 * @param {number} index - 数据项索引。
 * @returns {string} 对应颜色值。
 */
function getErrorTypeColor(index: number): string {
  return ERROR_TYPE_COLORS[index % ERROR_TYPE_COLORS.length];
}

/**
 * 获取无数据时空环图使用的占位颜色。
 * @returns {string} 占位扇区颜色。
 */
function getEmptyErrorTypeColor(): string {
  return document.body.classList.contains("dark-theme") ? "#4b5563" : "#e5e7eb";
}

/**
 * 初始化错误类型 doughnut 图实例。
 * @returns {void}
 */
function initErrorTypeChart(): void {
  const canvas = document.getElementById(
    "error-type-chart",
  ) as HTMLCanvasElement | null;
  if (!canvas) return;

  errorTypeChart?.destroy();
  errorTypeChart = new Chart(canvas.getContext("2d"), {
    type: "doughnut",
    data: {
      labels: [],
      datasets: [
        {
          label: t("card.errorTypes.title"),
          data: [],
          backgroundColor: [],
          borderWidth: 0,
        },
      ],
    },
    options: {
      animation: false,
      responsive: true,
      plugins: {
        legend: {
          display: false,
        },
      },
      cutout: "58%",
    },
  });
}

/**
 * 渲染错误类型图例和总数文本。
 * @returns {void}
 */
function renderErrorTypeLegend(): void {
  const legend = document.getElementById("error-type-legend");
  const totalEl = document.getElementById("error-type-total");
  if (!legend || !totalEl) return;

  const total = errorTypeCounts.reduce((sum, item) => sum + item.count, 0);
  totalEl.textContent = `${t("errorTypes.total")}: ${total}`;

  if (total <= 0) {
    legend.innerHTML = `
      <div class="error-type-legend-row">
        <span
          class="error-type-legend-color"
          style="background:${getEmptyErrorTypeColor()}"
        ></span>
        <span class="error-type-legend-label">${escapeHtml(t("errorTypes.noData"))}</span>
        <span class="error-type-legend-count">0</span>
      </div>
    `;
    return;
  }

  legend.innerHTML = errorTypeCounts
    .map((item, index) => {
      const label = escapeHtml(getErrorTypeLabel(item.error_type));
      const percent = ((item.count / total) * 100).toFixed(1);
      const color = getErrorTypeColor(index);
      return `
        <div class="error-type-legend-row">
          <span class="error-type-legend-color" style="background:${color}"></span>
          <span class="error-type-legend-label">${label}</span>
          <span class="error-type-legend-count">${item.count} (${percent}%)</span>
        </div>
      `;
    })
    .join("");
}

/**
 * 根据当前聚合结果刷新图表和图例。
 * @returns {void}
 */
function renderErrorTypeChart(): void {
  if (!errorTypeChart) {
    initErrorTypeChart();
  }
  if (!errorTypeChart) return;

  const total = errorTypeCounts.reduce((sum, item) => sum + item.count, 0);
  const labels = errorTypeCounts.map((item) => getErrorTypeLabel(item.error_type));
  const counts = errorTypeCounts.map((item) => item.count);
  const colors = errorTypeCounts.map((_, index) => getErrorTypeColor(index));

  errorTypeChart.data.labels = total > 0 ? labels : [t("errorTypes.noData")];
  errorTypeChart.data.datasets = [
    {
      label: t("card.errorTypes.title"),
      data: total > 0 ? counts : [1],
      backgroundColor: total > 0 ? colors : [getEmptyErrorTypeColor()],
      borderWidth: 0,
    },
  ];
  errorTypeChart.update();
  renderErrorTypeLegend();
}

/**
 * 拉取当前节点筛选下的错误类型聚合结果。
 * @param {boolean} [forceReload=false] - 是否强制绕过 known_rev 缓存。
 * @returns {Promise<boolean>} 当聚合结果发生变化时返回 true。
 */
async function loadErrorTypeCounts(forceReload: boolean = false): Promise<boolean> {
  const filterEl = getErrorTypeNodeFilter();
  const node = filterEl?.value ?? "";
  const queryKey = node;
  const knownRev =
    forceReload || queryKey !== errorTypeCountsQueryKey ? -1 : errorTypeCountsRev;
  const seq = ++errorTypeRequestSeq;
  const params = new URLSearchParams({
    known_rev: String(knownRev),
    node,
  });

  try {
    const res = await fetch(`/api/pull_error_type_counts?${params.toString()}`);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    const body = (await res.json()) as ErrorTypeCountsPullResponse;
    if (seq !== errorTypeRequestSeq) {
      return false;
    }

    errorTypeCountsQueryKey = queryKey;
    if (body.data === null) {
      errorTypeCountsRev = body.rev;
      return false;
    }

    errorTypeCountsRev = body.rev;
    errorTypeCounts = body.data;
    return true;
  } catch (err) {
    console.warn("错误类型聚合拉取失败:", err);
    return false;
  }
}

/**
 * 用当前节点状态刷新错误类型卡片的节点筛选器。
 * @param {Record<string, NodeStatus>} statuses - 当前节点状态快照。
 * @returns {void}
 */
function populateErrorTypeNodeFilter(statuses: Record<string, NodeStatus>): void {
  const filterEl = getErrorTypeNodeFilter();
  if (!filterEl) return;

  const previousValue = filterEl.value;
  const nodeNames = Object.keys(statuses).sort();
  const optionValues = new Set(nodeNames);
  if (previousValue) {
    optionValues.add(previousValue);
  }
  filterEl.innerHTML = "";

  const allOption = document.createElement("option");
  allOption.value = "";
  allOption.textContent = t("errors.allNodes");
  filterEl.appendChild(allOption);

  for (const nodeName of Array.from(optionValues).sort()) {
    const option = document.createElement("option");
    option.value = nodeName;
    option.textContent = nodeName;
    filterEl.appendChild(option);
  }

  filterEl.value = previousValue;
}

// 页面初始化后绑定筛选器事件。
document.addEventListener("DOMContentLoaded", () => {
  const filterEl = getErrorTypeNodeFilter();
  filterEl?.addEventListener("change", async () => {
    await loadErrorTypeCounts(true);
    renderErrorTypeChart();
  });
});
