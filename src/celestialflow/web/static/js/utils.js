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
function formatLargeNumber(n) {
    // 处理小于1000万的数：使用逗号分隔
    if (n < 10000000) {
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
function formatWithDelta(value, delta, deltaClass, negClass) {
    const fmtValue = formatLargeNumber(value);
    if (!delta || delta === 0)
        return fmtValue;
    const sign = delta > 0 ? "+" : "-";
    const cls = delta > 0 ? deltaClass : negClass;
    return `${fmtValue}<small class="${cls}" style="margin-left: 4px;">${sign}${formatLargeNumber(Math.abs(delta))}</small>`;
}
/**
 * 简单的移动端设备检测
 * @returns {boolean} 如果是移动设备则返回 true
 */
function isMobile() {
    return /Mobi|Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
}
/**
 * 转义 HTML 特殊字符，防止 XSS
 * @param {string} str - 原始字符串
 * @returns {string} 转义后的安全字符串
 */
function escapeHtml(str) {
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;")
        .replace(/\//g, "&#x2F;");
}
/**
 * 切换到错误标签页，并可选地设置节点筛选器
 * @param {string} [nodeFilter] - 节点筛选值，不传或传空字符串则显示全部
 * @returns {void}
 */
function switchToErrorsTab(nodeFilter = "") {
    const errorsTabButton = document.querySelector(`.tab-btn[data-tab="errors"]`);
    if (errorsTabButton) {
        activateTab(errorsTabButton);
    }
    const filterEl = document.getElementById("node-filter");
    if (filterEl) {
        filterEl.value = nodeFilter;
        filterEl.dispatchEvent(new Event("change"));
    }
}
/**
 * 格式化持续时间为 HH:MM:SS 或 MM:SS 格式
 * @param {number} seconds - 秒数
 * @returns {string} 格式化后的时间字符串
 */
function formatDuration(seconds) {
    seconds = seconds > 0 ? Math.max(1, Math.floor(seconds)) : 0;
    const hours = Math.floor(seconds / 3600);
    const remainder = seconds % 3600;
    const minutes = Math.floor(remainder / 60);
    const secs = remainder % 60;
    const pad = (n) => String(n).padStart(2, "0");
    if (hours > 0) {
        return `${pad(hours)}:${pad(minutes)}:${pad(secs)}`;
    }
    else {
        return `${pad(minutes)}:${pad(secs)}`;
    }
}
/**
 * 格式化时间戳为 YYYY-MM-DD HH:MM:SS 格式
 * @param {number} timestamp - Unix 时间戳（秒）
 * @returns {string} 格式化后的日期时间字符串
 */
function formatTimestamp(timestamp) {
    const d = new Date(timestamp * 1000);
    const pad = (n) => String(n).padStart(2, "0");
    const year = d.getFullYear();
    const month = pad(d.getMonth() + 1);
    const day = pad(d.getDate());
    const hour = pad(d.getHours());
    const minute = pad(d.getMinutes());
    const second = pad(d.getSeconds());
    return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
}
/**
 * 计算预计剩余时间（秒）
 * @param {number} processed - 已处理任务数
 * @param {number} pending - 待处理任务数
 * @param {number} elapsed - 已消耗时间（秒）
 * @returns {number} 预计剩余时间（秒）
 */
function calcRemainTime(processed, pending, elapsed) {
    if (processed && pending) {
        return pending / processed * elapsed;
    }
    return 0;
}
/**
 * 将对象格式化为字符串，自动转义换行、截断超长文本。
 * @param {unknown} obj - 任意对象
 * @param {number} max_length - 显示的最大字符数（超出将被截断）
 * @returns {string} 格式化字符串
 */
function format_repr(obj, max_length) {
    let obj_str = String(obj).replace(/\\/g, "\\\\").replace(/\n/g, "\\n");
    if (max_length <= 0 || obj_str.length <= max_length) {
        return obj_str;
    }
    // 截断逻辑（前 2/3 + ... + 后 1/3）
    const segment_len = Math.max(1, Math.floor(max_length / 3));
    const first_part = obj_str.slice(0, segment_len * 2);
    const last_part = obj_str.slice(-segment_len);
    return `${first_part}...${last_part}`;
}
