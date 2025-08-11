let errors = [];
let previousErrorsJSON = "";
let currentPage = 1;
const pageSize = 10;

const searchInput = document.getElementById("error-search");
const nodeFilter = document.getElementById("node-filter");
const errorsTableBody = document.querySelector("#errors-table tbody");
const paginationContainer = document.getElementById("pagination-container");

async function loadErrors() {
  try {
    const res = await fetch("/api/get_errors");
    errors = await res.json();
  } catch (e) {
    console.error("错误日志加载失败", e);
  }
}

function renderErrors() {
  const filter = nodeFilter.value.trim();
  const keyword = (searchInput.value || "").trim().toLowerCase();

  const filtered = errors.filter(e => {
    const matchNode = !filter || e.node === filter;
    const matchKeyword = !keyword ||
      (e.error && e.error.toLowerCase().includes(keyword)) ||
      (e.task_id && e.task_id.toLowerCase().includes(keyword));
    return matchNode && matchKeyword;
  });

  const sortedByTime = [...filtered].sort((a, b) => b.timestamp - a.timestamp);
  const totalPages = Math.ceil(sortedByTime.length / pageSize);
  
  // 处理边界（例如当前页大于最大页）
  currentPage = Math.min(currentPage, totalPages || 1);

  const startIndex = (currentPage - 1) * pageSize;
  const pageItems = sortedByTime.slice(startIndex, startIndex + pageSize);

  errorsTableBody.innerHTML = "";

  if (!pageItems.length) {
    errorsTableBody.innerHTML = `<tr><td colspan="4" class="no-errors">没有错误记录</td></tr>`;
  } else {
    for (const e of pageItems) {
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

  renderPaginationControls(totalPages);
}

function buildPageList(current, total) {
  // 想显示哪些关键页：首尾、当前、前后1-2页
  const pages = new Set([1, total, current, current-1, current+1, current-2, current+2]);
  const list = [...pages].filter(p => p >= 1 && p <= total).sort((a,b)=>a-b);

  const out = [];
  for (let i = 0; i < list.length; i++) {
    out.push(list[i]);
    if (i < list.length - 1 && list[i+1] - list[i] > 1) out.push("…"); // 插入省略号
  }
  return out;
}

function renderPaginationControls(totalPages) {
  paginationContainer.innerHTML = "";
  if (totalPages <= 1) return;

  // 上一页
  const prevBtn = document.createElement("button");
  prevBtn.textContent = "上一页";
  prevBtn.className = "pager-btn";
  prevBtn.disabled = currentPage === 1;
  prevBtn.onclick = () => { currentPage = Math.max(1, currentPage - 1); renderErrors(); };

  // 数字页码区
  const pageBar = document.createElement("div");
  pageBar.className = "pager";

  const pages = buildPageList(currentPage, totalPages);
  pages.forEach(p => {
    const span = document.createElement("span");
    span.textContent = p;
    if (p === "…") {
      span.className = "dots";
    } else if (p === currentPage) {
      span.className = "page-current"; // 当前页样式
    } else {
      span.className = "page-link";    // 普通页可点击
      span.onclick = () => {
        currentPage = p;
        renderErrors();
      };
    }
    pageBar.appendChild(span);
  });

  // 下一页
  const nextBtn = document.createElement("button");
  nextBtn.textContent = "下一页";
  nextBtn.className = "pager-btn";
  nextBtn.disabled = currentPage === totalPages;
  nextBtn.onclick = () => { currentPage = Math.min(totalPages, currentPage + 1); renderErrors(); };

  paginationContainer.appendChild(prevBtn);
  paginationContainer.appendChild(pageBar);
  paginationContainer.appendChild(nextBtn);
}

function populateNodeFilter() {
  const nodes = Object.keys(nodeStatuses);
  const previousValue = nodeFilter.value;

  nodeFilter.innerHTML = `<option value="">全部节点</option>`;
  for (const node of nodes) {
    const option = document.createElement("option");
    option.value = node;
    option.textContent = node;
    nodeFilter.appendChild(option);
  }

  if (nodes.includes(previousValue)) {
    nodeFilter.value = previousValue;
  } else {
    nodeFilter.value = "";
  }
}

searchInput.addEventListener("input", () => {
  currentPage = 1;
  renderErrors();
});

nodeFilter.addEventListener("change", () => {
  currentPage = 1; // 切换节点时回到第一页
  renderErrors();
});
