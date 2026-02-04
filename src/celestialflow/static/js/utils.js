// task_web.js
function renderLocalTime(timestamp) {
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
        y: point.tasks_processed,
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

function toggleDarkTheme() {
  return document.body.classList.toggle("dark-theme");
}

// task_statuses.js
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
