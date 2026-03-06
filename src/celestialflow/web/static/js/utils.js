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
 * 格式化数值及其增量变化
 * @param {number} value - 当前数值
 * @param {number} delta - 增量数值
 * @returns {string} 包含数值和带颜色增量的 HTML 字符串
 */
function formatWithDelta(value, delta) {
  if (!delta || delta === 0) return `${value}`;
  const sign = delta > 0 ? "+" : "-";
  return `${value}<small style="color: ${delta > 0 ? "green" : "red"}; margin-left: 4px;">${sign}${Math.abs(delta)}</small>`;
}

/**
 * 根据索引获取预定义的颜色
 * @param {number} index - 索引值
 * @returns {string} 十六进制颜色代码
 */
function getColor(index) {
  const colors = [
    "#3b82f6",
    "#10b981",
    "#f59e0b",
    "#ef4444",
    "#8b5cf6",
    "#ec4899",
    "#22c55e",
    "#0ea5e9",
    "#f97316",
  ];
  return colors[index % colors.length];
}

/**
 * 从节点状态中提取历史进度数据，用于图表显示
 * @param {Object} nodeStatuses - 节点状态对象
 * @returns {Object} 包含各节点历史数据的对象
 */
function extractProgressData(nodeStatuses) {
  const result = {};
  for (const [node, data] of Object.entries(nodeStatuses)) {
    if (data.history) {
      result[node] = data.history.map((point) => ({
        x: point.timestamp,
        y: point.tasks_processed,
      }));
    }
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
  } catch (e) {
    showError("json-error", "JSON 格式不合法");
    return false;
  }
}

/**
 * 切换页面暗黑/明亮主题
 * @returns {boolean} 切换后是否为暗黑模式
 */
function toggleDarkTheme() {
  return document.body.classList.toggle("dark-theme");
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
  } else {
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
