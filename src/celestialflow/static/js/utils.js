// task_web.js
function formatTimestamp(timestamp) {
  return new Date(timestamp * 1000).toLocaleString();
}

function formatWithDelta(value, delta) {
  if (!delta || delta === 0) return `${value}`;
  const sign = delta > 0 ? "+" : "-";
  return `${value}<small style="color: ${delta > 0 ? "green" : "red"}; margin-left: 4px;">${sign}${Math.abs(delta)}</small>`;
}

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

function extractProgressData(nodeStatuses) {
  const result = {};
  for (const [node, data] of Object.entries(nodeStatuses)) {
    if (data.history) {
      result[node] = data.history.map((point) => ({
        x: point.timestamp,
        y: point.tasks_completed,
      }));
    }
  }
  return result;
}

// 简单移动端判断
function isMobile() {
  return /Mobi|Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
}

// task_indexction.js
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