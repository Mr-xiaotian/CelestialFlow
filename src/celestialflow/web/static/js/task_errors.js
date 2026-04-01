let errors = [];
let currentPage = 1;
const pageSize = 10;
let totalPages = 1;
let errorsRev = -1;
let lastQueryKey = "";
let errorsRequestSeq = 0;
const searchInput = document.getElementById("error-search");
const nodeFilter = document.getElementById("node-filter");
const errorsTableBody = document.querySelector("#errors-table tbody");
const paginationContainer = document.getElementById("pager-container");
function buildErrorsQueryKey(page, pageSizeValue, node, keyword) {
    return `${page}|${pageSizeValue}|${node}|${keyword}`;
}
async function loadErrors(forceReload = false) {
    try {
        const node = nodeFilter.value.trim();
        const keyword = (searchInput.value || "").trim();
        const queryKey = buildErrorsQueryKey(currentPage, pageSize, node, keyword.toLowerCase());
        const knownRev = forceReload || queryKey !== lastQueryKey ? -1 : errorsRev;
        const requestSeq = ++errorsRequestSeq;
        const params = new URLSearchParams({
            known_rev: String(knownRev),
            page: String(currentPage),
            page_size: String(pageSize),
            node,
            keyword,
        });
        const res = await fetch(`/api/pull_errors?${params.toString()}`);
        if (!res.ok)
            return false;
        const data = await res.json();
        if (requestSeq !== errorsRequestSeq)
            return false;
        currentPage = Number(data.page || currentPage);
        totalPages = Number(data.total_pages || 1);
        lastQueryKey = queryKey;
        if (data.data === null || data.data === undefined) {
            return false;
        }
        errors = Array.isArray(data.data) ? data.data : [];
        const changed = errorsRev !== Number(data.rev);
        errorsRev = Number(data.rev);
        return changed || forceReload;
    }
    catch (e) {
        console.error("错误日志加载失败", e);
        return false;
    }
}
function renderErrors() {
    const pageItems = errors;
    errorsTableBody.innerHTML = "";
    if (!pageItems.length) {
        errorsTableBody.innerHTML = `<tr><td colspan="6" class="no-errors">没有错误记录</td></tr>`;
    }
    else {
        for (let i = 0; i < pageItems.length; i++) {
            const e = pageItems[i];
            const index = (currentPage - 1) * pageSize + i + 1;
            const row = document.createElement("tr");
            row.innerHTML = `
        <td data-label="#">${index}</td>
        <td class="error-id" data-label="错误id">${e.error_id}</td>
        <td class="error-message" data-label="错误信息" title="${escapeHtml(e.error_repr)}">${escapeHtml(e.error_repr)}</td>
        <td data-label="节点">${escapeHtml(e.stage)}</td>
        <td data-label="任务">${escapeHtml(e.task_repr)}</td>
        <td data-label="时间">${renderLocalTime(e.ts)}</td>
      `;
            errorsTableBody.appendChild(row);
        }
    }
    renderPaginationControls(totalPages);
}
async function goToErrorsPage(nextPage) {
    const normalizedPage = Math.max(1, Math.min(totalPages || 1, nextPage));
    if (normalizedPage === currentPage)
        return;
    currentPage = normalizedPage;
    await loadErrors(true);
    renderErrors();
}
function buildPageList(current, total) {
    // 想显示哪些关键页：首尾、当前、前后1-2页
    const pages = new Set([1, total, current, current - 1, current + 1, current - 2, current + 2]);
    const list = [...pages].filter(p => p >= 1 && p <= total).sort((a, b) => a - b);
    const out = [];
    for (let i = 0; i < list.length; i++) {
        out.push(list[i]);
        if (i < list.length - 1 && list[i + 1] - list[i] > 1)
            out.push("…"); // 插入省略号
    }
    return out;
}
function renderPaginationControls(totalPages) {
    paginationContainer.innerHTML = "";
    if (totalPages <= 1)
        return;
    // 上一页
    const prevBtn = document.createElement("button");
    prevBtn.textContent = "上一页";
    prevBtn.className = "pager-btn";
    prevBtn.disabled = currentPage === 1;
    prevBtn.onclick = async () => { await goToErrorsPage(currentPage - 1); };
    // 数字页码区
    const pageBar = document.createElement("div");
    pageBar.className = "pager";
    const pages = buildPageList(currentPage, totalPages);
    pages.forEach(p => {
        const span = document.createElement("span");
        span.textContent = p;
        if (p === "…") {
            span.className = "dots";
        }
        else if (p === currentPage) {
            span.className = "pager-current";
        }
        else {
            span.className = "pager-link";
            span.onclick = async () => {
                await goToErrorsPage(Number(p));
            };
        }
        pageBar.appendChild(span);
    });
    // 下一页
    const nextBtn = document.createElement("button");
    nextBtn.textContent = "下一页";
    nextBtn.className = "pager-btn";
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.onclick = async () => { await goToErrorsPage(currentPage + 1); };
    paginationContainer.appendChild(prevBtn);
    paginationContainer.appendChild(pageBar);
    paginationContainer.appendChild(nextBtn);
}
function populateNodeFilter(statuses) {
    const nodes = Object.keys(statuses);
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
    }
    else {
        nodeFilter.value = "";
    }
}
searchInput.addEventListener("input", async () => {
    currentPage = 1;
    await loadErrors(true);
    renderErrors();
});
nodeFilter.addEventListener("change", async () => {
    currentPage = 1; // 切换节点时回到第一页
    await loadErrors(true);
    renderErrors();
});
