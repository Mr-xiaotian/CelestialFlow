"use strict";
/**
 * 错误日志分页与过滤模块
 * 处理错误记录的异步拉取、前端分页逻辑以及按节点/关键词搜索的过滤展示
 */
// 全局状态
let errors = []; // 错误记录列表
let currentPage = 1; // 当前分页页码
let pageSize = 10; // 每页显示条数
let errorSortOrder = "newest"; // 错误日志默认排序
let totalPages = 1; // 总页数
let errorsRev = -1; // 数据版本号，用于增量拉取
let lastQueryKey = ""; // 上次查询的缓存键，用于判断筛选条件是否变化
let errorsRequestSeq = 0; // 请求序列号，防止旧请求覆盖新结果
// DOM 元素引用（错误页）
const searchInput = document.getElementById("error-search");
const nodeFilter = document.getElementById("node-filter");
const errorSortSelect = document.getElementById("error-sort-order");
const errorsTableBody = document.querySelector("#errors-table tbody");
const paginationContainer = document.getElementById("pager-container");
/**
 * 构建错误查询缓存键
 * @param {number} page - 当前页码
 * @param {number} pageSizeValue - 每页大小
 * @param {string} node - 节点筛选条件
 * @param {string} keyword - 搜索关键词
 * @param {string} sortOrder - 排序顺序（"newest" 或 "oldest"）
 * @returns {string} 组合后的查询键
 */
function buildErrorsQueryKey(page, pageSizeValue, node, keyword, sortOrder) {
    return `${page}|${pageSizeValue}|${node}|${keyword}|${sortOrder}`;
}
/**
 * 从后端加载错误日志数据
 * @param {boolean} [forceReload=false] - 是否忽略当前查询缓存与 `known_rev`，强制重新拉取。
 * @returns {Promise<boolean>} 当后端返回了新的错误记录数据时返回 `true`，否则返回 `false`。
 */
async function loadErrors(forceReload = false) {
    try {
        const node = nodeFilter.value.trim(); // 当前节点筛选值
        const keyword = (searchInput.value || "").trim(); // 当前关键词筛选值
        const queryKey = buildErrorsQueryKey(currentPage, pageSize, node, keyword.toLowerCase(), errorSortOrder);
        const knownRev = forceReload || queryKey !== lastQueryKey ? -1 : errorsRev; // 条件变化时强制全量拉取
        const requestSeq = ++errorsRequestSeq; // 为当前请求分配递增序号
        // 将分页、排序和筛选条件编码进查询参数。
        const params = new URLSearchParams({
            known_rev: String(knownRev),
            page: String(currentPage),
            page_size: String(pageSize),
            node,
            keyword,
            sort_order: errorSortOrder,
        });
        const res = await fetch(`/api/pull_errors?${params.toString()}`);
        if (!res.ok)
            return false;
        const data = (await res.json());
        if (requestSeq !== errorsRequestSeq)
            return false; // 丢弃已过时请求的返回结果
        currentPage = Number(data.page || currentPage);
        totalPages = Number(data.total_pages || 1);
        errorSortOrder = data.sort_order === "oldest" ? "oldest" : "newest";
        lastQueryKey = queryKey;
        if (data.data === null || data.data === undefined) {
            return false;
        }
        errors = Array.isArray(data.data) ? data.data : []; // 仅接受数组类型结果
        const changed = errorsRev !== Number(data.rev); // 对比版本号判断是否有新内容
        errorsRev = Number(data.rev);
        return changed || forceReload;
    }
    catch (e) {
        console.error("错误日志加载失败", e);
        return false;
    }
}
/**
 * 渲染错误列表表格和分页控件
 * 将获取到的错误记录填充到表格中，并根据总页数生成分页按钮
 */
function renderErrors() {
    const pageItems = errors; // 后端已按分页返回当前页数据
    errorsTableBody.innerHTML = "";
    if (!pageItems.length) {
        errorsTableBody.innerHTML = `<tr><td colspan="7" class="empty-placeholder">${t("errors.noRecords")}</td></tr>`;
    }
    else {
        for (let i = 0; i < pageItems.length; i++) {
            const e = pageItems[i]; // 当前错误记录
            const index = (currentPage - 1) * pageSize + i + 1; // 全局展示序号
            const row = document.createElement("tr"); // 当前表格行
            const errorText = `${e.error_type}(${e.error_message})`; // 错误完整文本
            const errorRepr = format_repr(errorText, 40); // 表格中展示的截断错误文本
            const taskText = typeof e.task_json === "string"
                ? e.task_json
                : JSON.stringify(e.task_json);
            const taskRepr = format_repr(taskText, 40); // 表格中展示的截断任务文本
            const canRetry = e.task_json !== undefined && !taskText.startsWith("<");
            const retryLabel = canRetry ? t("errors.retryInject") : t("errors.retryUnavailable");
            const retryClass = canRetry ? "retry-link" : "retry-disabled";
            row.innerHTML = `
        <td data-label="#">${index}</td>
        <td class="error-id" data-label="${t("errors.colId")}">${e.event_id}</td>
        <td class="error-cell" data-label="${t("errors.colMessage")}" title="${escapeHtml(errorText)}">${escapeHtml(errorRepr)}</td>
        <td data-label="${t("errors.colNode")}">${escapeHtml(e.stage)}</td>
        <td data-label="${t("errors.colTask")}" title="${escapeHtml(taskText)}">${escapeHtml(taskRepr)}</td>
        <td data-label="${t("errors.colTime")}">${formatTimestamp(e.ts)}</td>
        <td data-label="${t("errors.colRetry")}"><div class="${retryClass}" role="${canRetry ? "button" : "note"}" tabindex="${canRetry ? "0" : "-1"}">${retryLabel}</div></td>
      `;
            const retryAction = row.querySelector(".retry-link");
            if (retryAction && canRetry) {
                retryAction.addEventListener("click", () => {
                    preloadInjectionDraftFromError(e.stage, e.task_json, webConfig.errors.jumpToInjectionAfterRetry);
                });
                retryAction.addEventListener("keydown", (event) => {
                    if (event.key !== "Enter" && event.key !== " ")
                        return;
                    event.preventDefault();
                    preloadInjectionDraftFromError(e.stage, e.task_json, webConfig.errors.jumpToInjectionAfterRetry);
                });
            }
            errorsTableBody.appendChild(row);
        }
    }
    renderPaginationControls(totalPages);
}
/**
 * 跳转到指定错误页码并重新加载数据
 * @param {number} nextPage - 目标页码
 * @returns {Promise<void>}
 */
async function goToErrorsPage(nextPage) {
    const normalizedPage = Math.max(1, Math.min(totalPages || 1, nextPage)); // 将目标页码限制在合法范围内
    if (normalizedPage === currentPage)
        return;
    currentPage = normalizedPage;
    await loadErrors(true);
    renderErrors();
}
/**
 * 生成分页页码列表，包含首尾、当前及前后页，自动插入省略号
 * @param {number} current - 当前页码
 * @param {number} total - 总页数
 * @returns {Array<number|string>} 页码数组（数字或省略号）
 */
function buildPageList(current, total) {
    // 想显示哪些关键页：首尾、当前、前后1-2页
    const pages = new Set([1, total, current, current - 1, current + 1, current - 2, current + 2]);
    const list = [...pages].filter(p => p >= 1 && p <= total).sort((a, b) => a - b); // 去掉越界页码后升序排列
    const out = [];
    for (let i = 0; i < list.length; i++) {
        out.push(list[i]);
        if (i < list.length - 1 && list[i + 1] - list[i] > 1)
            out.push("…"); // 插入省略号
    }
    return out;
}
/**
 * 渲染分页控件（上一页、页码、下一页）
 * @param {number} totalPages - 总页数
 * @returns {void}
 */
function renderPaginationControls(totalPages) {
    paginationContainer.innerHTML = "";
    if (totalPages <= 1)
        return;
    // 上一页
    const prevBtn = document.createElement("button");
    prevBtn.textContent = t("errors.prevPage");
    prevBtn.className = "pager-btn";
    prevBtn.disabled = currentPage === 1;
    prevBtn.onclick = async () => { await goToErrorsPage(currentPage - 1); };
    // 数字页码区
    const pageBar = document.createElement("div"); // 中间页码容器
    pageBar.className = "pager";
    const pages = buildPageList(currentPage, totalPages); // 带省略号的页码模型
    pages.forEach(p => {
        const span = document.createElement("span"); // 单个页码或省略号元素
        span.textContent = p.toString();
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
    nextBtn.textContent = t("errors.nextPage");
    nextBtn.className = "pager-btn";
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.onclick = async () => { await goToErrorsPage(currentPage + 1); };
    paginationContainer.appendChild(prevBtn);
    paginationContainer.appendChild(pageBar);
    paginationContainer.appendChild(nextBtn);
}
/**
 * 根据节点状态填充错误筛选下拉框
 * @param {Record<string, NodeStatus>} statuses - 节点状态映射
 * @returns {void}
 */
function populateNodeFilter(statuses) {
    const nodes = Object.keys(statuses); // 当前可供筛选的节点名列表
    const previousValue = nodeFilter.value; // 尽量保留用户当前筛选条件
    nodeFilter.innerHTML = `<option value="">${t("errors.allNodes")}</option>`;
    for (const node of nodes) {
        const option = document.createElement("option"); // 单个节点下拉项
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
// 输入搜索关键词时立即重新筛选错误列表并回到第一页。
searchInput.addEventListener("input", async () => {
    currentPage = 1;
    await loadErrors(true);
    renderErrors();
});
// 切换节点筛选时刷新当前错误列表。
nodeFilter.addEventListener("change", async () => {
    currentPage = 1; // 切换节点时回到第一页
    await loadErrors(true);
    renderErrors();
});
// 切换默认排序方式时刷新错误页并保存当前设置。
errorSortSelect.addEventListener("change", async () => {
    errorSortOrder = errorSortSelect.value === "oldest" ? "oldest" : "newest";
    if (webConfig) {
        webConfig.errors.sortOrder = errorSortOrder;
    }
    currentPage = 1;
    await loadErrors(true);
    renderErrors();
    if (webConfig) {
        showSettingsSaveStatus((await saveWebConfig()) ? "settings.saveSuccess" : "settings.saveFailed");
    }
});
