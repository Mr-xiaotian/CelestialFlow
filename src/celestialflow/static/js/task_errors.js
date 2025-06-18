let errors = [];

const nodeFilter = document.getElementById("node-filter");
const errorsTableBody = document.querySelector("#errors-table tbody");

async function loadErrors() {
  try {
    const res = await fetch("/api/get_errors");
    errors = await res.json();
  } catch (e) {
    console.error("错误日志加载失败", e);
  }
}

function renderErrors() {
  const filter = nodeFilter.value;
  const filtered = filter ? errors.filter((e) => e.node === filter) : errors;

  errorsTableBody.innerHTML = "";
  if (!filtered.length) {
    errorsTableBody.innerHTML = `<tr><td colspan="4" class="no-errors">没有错误记录</td></tr>`;
    return;
  }

  // 按时间戳降序排序（最新的错误排在最前面）
  const sortedByTime = [...filtered].sort((a, b) => b.timestamp - a.timestamp);

  for (const e of sortedByTime) {
    const row = document.createElement("tr");
    row.innerHTML = `
          <td class="error-message">${e.error}</td>
          <td>${e.node}</td>
          <td>${e.task_id}</td>
          <td>${formatTimestamp(e.timestamp)}</td>
        `;
    errorsTableBody.appendChild(row);
  }
}

function populateNodeFilter() {
  const nodes = Object.keys(nodeStatuses);
  const previousValue = nodeFilter.value; // 记住当前选中值

  // 重新填充选项
  nodeFilter.innerHTML = `<option value="">全部节点</option>`;
  for (const node of nodes) {
    const option = document.createElement("option");
    option.value = node;
    option.textContent = node;
    nodeFilter.appendChild(option);
  }

  // 尝试恢复之前的选中项
  if (nodes.includes(previousValue)) {
    nodeFilter.value = previousValue;
  } else {
    nodeFilter.value = ""; // 默认选“全部节点”
  }
}

nodeFilter.addEventListener("change", () => {
  renderErrors();
});
