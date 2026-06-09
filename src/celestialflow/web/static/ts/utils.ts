/**
 * 通用工具模块
 * 包含数值格式化、时间转换、设备检测及复杂的 UI 辅助逻辑
 */

/**
 * 将大数格式化为易读的字符串
 * - 小于 10,000,000 (一千万)：使用千分位逗号分隔，如 1,234,567
 * - 大于等于 10,000,000：转换为科学计数法格式的 HTML，如 ~1.23×10⁹
 * @param {number} n - 原始数值
 * @returns {string} 格式化后的 HTML 字符串
 */
function formatLargeNumber(n: number): string {
  // 处理小于1000万的数：使用逗号分隔
  if (n < 10_000_000) {
    return n.toLocaleString('en-US');
  }
  
  // 大数转为科学计数法
  const exp = Math.floor(Math.log10(n));
  const coeff = (n / Math.pow(10, exp)).toFixed(2);
  return `~${coeff}×10<sup>${exp}</sup>`;
}

/**
 * 格式化数值及其增量变化
 * @param {number} value - 当前数值
 * @param {number} delta - 增量数值
 * @param {string} deltaClass - 增量数值的 CSS 类名
 * @param {string} negClass - 负增量数值的 CSS 类名
 * @returns {string} 包含数值和带颜色增量的 HTML 字符串
 */
function formatWithDelta(
  value: number,
  delta: number,
  deltaClass: string,
  negClass: string,
): string {
  const fmtValue = formatLargeNumber(value); // 当前主值的格式化结果
  if (!delta || delta === 0) return fmtValue;
  const sign = delta > 0 ? "+" : "-"; // 增量显示符号
  const cls = delta > 0 ? deltaClass : negClass; // 根据正负值选择颜色类
  return `${fmtValue}<small class="${cls}" style="margin-left: 4px;">${sign}${formatLargeNumber(Math.abs(delta))}</small>`;
}

/**
 * 简单的移动端设备检测
 * @returns {boolean} 如果是移动设备则返回 true
 */
function isMobile(): boolean {
  return /Mobi|Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
}

/**
 * 转义 HTML 特殊字符，防止 XSS
 * @param {string} str - 原始字符串
 * @returns {string} 转义后的安全字符串
 */
function escapeHtml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;")
    .replace(/\//g, "&#x2F;");
}

/**
 * 渲染带提示点的通用标签。
 * @param {string} labelKey - 标签翻译键
 * @param {string} tooltipKey - 提示文案翻译键
 * @returns {string} 标签 HTML
 */
function renderLabelWithTooltip(labelKey: string, tooltipKey: string): string {
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
 * 切换到错误标签页，并可选地设置节点筛选器
 * @param {string} [nodeFilter] - 节点筛选值，不传或传空字符串则显示全部
 * @returns {void}
 */
function switchToErrorsTab(nodeFilter: string = ""): void {
  // 先切换到错误日志页，确保筛选器所在页面处于可见状态。
  const errorsTabButton = document.querySelector<HTMLElement>(
    `.tab-btn[data-tab="errors"]`,
  );
  if (errorsTabButton) {
    activateTab(errorsTabButton);
  }

  // 再同步节点筛选器，复用原有 change 事件触发刷新逻辑。
  const filterEl = document.getElementById("node-filter") as HTMLSelectElement | null;
  if (filterEl) {
    filterEl.value = nodeFilter;
    filterEl.dispatchEvent(new Event("change"));
  }
}

/**
 * 切换到任务注入标签页。
 * @returns {void}
 */
function switchToInjectionTab(): void {
  const injectionTabButton = document.querySelector<HTMLElement>(
    `.tab-btn[data-tab="task-injection"]`,
  );
  if (injectionTabButton) {
    activateTab(injectionTabButton);
  }
}

/**
 * 格式化持续时间为 HH:MM:SS 或 MM:SS 格式
 * @param {number} seconds - 秒数
 * @returns {string} 格式化后的时间字符串
 */
function formatDuration(seconds: number): string {
  seconds = seconds > 0 ? Math.max(1, Math.floor(seconds)) : 0; // 正数至少展示 1 秒

  const hours = Math.floor(seconds / 3600);
  const remainder = seconds % 3600;
  const minutes = Math.floor(remainder / 60);
  const secs = remainder % 60;

  /** 将单个时间段补齐为两位字符串。 */
  const pad = (n: number): string => String(n).padStart(2, "0");

  if (hours > 0) {
    return `${pad(hours)}:${pad(minutes)}:${pad(secs)}`;
  } else {
    return `${pad(minutes)}:${pad(secs)}`;
  }
}

/**
 * 格式化时间戳为 YYYY-MM-DD HH:MM:SS 格式
 * @param {number} timestamp - Unix 时间戳（秒）
 * @returns {string} 格式化后的日期时间字符串
 */
function formatTimestamp(timestamp: number): string {
  const d = new Date(timestamp * 1000); // Unix 秒级时间戳转本地时间

  /** 将年/月/日/时/分/秒字段补齐为两位。 */
  const pad = (n: number): string => String(n).padStart(2, "0");

  const year = d.getFullYear(); // 年份保留完整位数
  const month = pad(d.getMonth() + 1); // 月份从 0 开始，需补 1
  const day = pad(d.getDate()); // 日期
  const hour = pad(d.getHours()); // 小时
  const minute = pad(d.getMinutes()); // 分钟
  const second = pad(d.getSeconds()); // 秒

  return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
}

/**
 * 计算预计剩余时间（秒）
 * @param {number} processed - 已处理任务数
 * @param {number} pending - 待处理任务数
 * @param {number} elapsed - 已消耗时间（秒）
 * @returns {number} 预计剩余时间（秒）
 */
function calcRemainTime(processed: number, pending: number, elapsed: number): number {
  if (processed && pending) {
      return pending / processed * elapsed // 按当前吞吐速度线性估算剩余时长
  }
  return 0 // 没有足够样本时返回 0，避免误导性估算
}

/**
 * 将对象格式化为字符串，自动转义换行、截断超长文本。
 * @param {unknown} obj - 任意对象
 * @param {number} max_length - 显示的最大字符数（超出将被截断）
 * @returns {string} 格式化字符串
 */
function format_repr(obj: unknown, max_length: number): string {
    let obj_str = String(obj).replace(/\\/g, "\\\\").replace(/\n/g, "\\n"); // 保留换行与反斜杠的可见形式
    if (max_length <= 0 || obj_str.length <= max_length) {
        return obj_str;
    }

    // 截断逻辑（前 2/3 + ... + 后 1/3）
    const segment_len = Math.max(1, Math.floor(max_length / 3)); // 单侧保留的最小片段长度

    const first_part = obj_str.slice(0, segment_len * 2); // 前段保留更长，方便快速识别
    const last_part = obj_str.slice(-segment_len); // 末段保留尾部上下文

    return `${first_part}...${last_part}`;
}
