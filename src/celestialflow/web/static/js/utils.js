// task_web.js
/**
 * 将时间戳转换为本地时间字符串
 * @param {number} timestamp - Unix 时间戳（秒）
 * @returns {string} 本地时间字符串
 */
function renderLocalTime(timestamp) {
    return new Date(timestamp * 1000).toLocaleString();
}
/**
 * 将大数格式化为模糊科学计数法 HTML
 * 小数用逗号3位分割，如 1,000 或 10,000,000
 * 大数转为科学计数法：~1.23×10<sup>9</sup>
 * @param {number} n - 数值
 * @returns {string} 格式化后的字符串或 HTML
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
 * 根据索引获取预定义的颜色
 * @param {number} index - 索引值
 * @returns {string} 十六进制颜色代码
 */
function getColor(index) {
    const vars = [
        "--cornflower-500",
        "--jade-500",
        "--marigold-500",
        "--crimson-500",
        "--violet-500",
        "--rose-500",
        "--jade-400",
        "--sky-500",
        "--amber-500",
    ];
    const style = getComputedStyle(document.documentElement);
    return style.getPropertyValue(vars[index % vars.length]).trim();
}
/**
 * 从节点历史数据中提取进度数据，用于图表显示
 * @param {Object} nodeHistories - 节点历史数据对象
 * @returns {Object} 包含各节点历史数据的对象
 */
function extractProgressData(nodeHistories) {
    const result = {};
    for (const [node, data] of Object.entries(nodeHistories)) {
        result[node] = data.map((point) => ({
            x: point.timestamp,
            y: point.tasks_processed,
        }));
    }
    return result;
}
/**
 * 简单的移动端设备检测
 * @returns {boolean} 如果是移动设备则返回 true
 */
function isMobile() {
    return /Mobi|Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
}
// task_indexction.js
/**
 * 验证 JSON 字符串格式是否合法
 * @param {string} text - JSON 字符串
 * @returns {boolean} 格式合法返回 true，否则返回 false
 */
function validateJSON(text) {
    if (!text.trim()) {
        hideError("json-error");
        return true;
    }
    try {
        JSON.parse(text);
        hideError("json-error");
        return true;
    }
    catch (e) {
        showError("json-error", "JSON 格式不合法");
        return false;
    }
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
        .replace(/"/g, "&quot;");
}
/**
 * 切换页面暗黑/明亮主题
 * @returns {boolean} 切换后是否为暗黑模式
 */
function toggleDarkTheme() {
    return document.body.classList.toggle("dark-theme");
}
/**
 * 切换到错误标签页，并可选地设置节点筛选器
 * @param {string} [nodeFilter] - 节点筛选值，不传或传空字符串则显示全部
 */
function switchToErrorsTab(nodeFilter = "") {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
    document.querySelector(`.tab-btn[data-tab="errors"]`)?.classList.add("active");
    document.getElementById("errors")?.classList.add("active");
    const filterEl = document.getElementById("node-filter");
    if (filterEl) {
        filterEl.value = nodeFilter;
        filterEl.dispatchEvent(new Event("change"));
    }
}
// task_statuses.js
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
