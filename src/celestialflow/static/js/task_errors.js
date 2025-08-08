let errors = [];
let previousErrorsJSON = "";
let currentPage = 1;
const pageSize = 10;

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
  const filter = nodeFilter.value;
  const filtered = filter ? errors.filter((e) => e.node === filter) : errors;

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

function renderPaginationControls(totalPages) {
  paginationContainer.innerHTML = "";

  if (totalPages <= 1) return;

  const prevBtn = document.createElement("button");
  prevBtn.textContent = "上一页";
  prevBtn.disabled = currentPage === 1;
  prevBtn.onclick = () => {
    currentPage--;
    renderErrors();
  };

  const nextBtn = document.createElement("button");
  nextBtn.textContent = "下一页";
  nextBtn.disabled = currentPage === totalPages;
  nextBtn.onclick = () => {
    currentPage++;
    renderErrors();
  };

  const info = document.createElement("span");
  info.className = "pagination-info";
  info.textContent = `第 ${currentPage} 页 / 共 ${totalPages} 页`;

  // 🔹 页码输入框
  const pageInput = document.createElement("input");
  pageInput.type = "number";
  pageInput.min = 1;
  pageInput.max = totalPages;
  pageInput.value = currentPage;
  pageInput.className = "page-input";
  pageInput.style.width = "50px";
  pageInput.onkeydown = (e) => {
    if (e.key === "Enter") {
      jumpToPage();
    }
  };

  // 🔹 跳转按钮
  const jumpBtn = document.createElement("button");
  jumpBtn.textContent = "跳转";
  jumpBtn.onclick = jumpToPage;

  function jumpToPage() {
    let targetPage = parseInt(pageInput.value, 10);
    if (!isNaN(targetPage)) {
      targetPage = Math.max(1, Math.min(totalPages, targetPage)); // 限制范围
      if (targetPage !== currentPage) {
        currentPage = targetPage;
        renderErrors();
      }
    }
  }

  paginationContainer.appendChild(prevBtn);
  paginationContainer.appendChild(info);
  paginationContainer.appendChild(pageInput);
  paginationContainer.appendChild(jumpBtn);
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

nodeFilter.addEventListener("change", () => {
  currentPage = 1; // 切换节点时回到第一页
  renderErrors();
});
