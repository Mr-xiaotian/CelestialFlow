"use strict";
/**
 * 任务手动注入模块
 * 当前设计改为单节点编辑 + 批量提交：每个节点维护独立草稿，最终统一发送为
 * { node_name: [tasklist] } 结构。
 */
// ======== 页面级状态 ========
// 当前正在编辑的节点名称；未选择节点时为 null。
let currentNodeName = null;
// 每个节点各自维护一份 JSON 草稿文本。
let nodeDrafts = {};
// 状态提示的自动隐藏定时器，避免重复触发时相互覆盖。
let statusHideTimer = null;
/**
 * 为动态提示元素记录 i18n 元信息，便于语言切换后重绘。
 *
 * @param {HTMLElement} element - 目标元素
 * @param {string} messageKey - 文案翻译键
 * @param {string[]} [args=[]] - 占位参数
 * @returns {void}
 */
function setLocalizedMessageMeta(element, messageKey, args = []) {
    element.dataset.messageKey = messageKey;
    element.dataset.messageArgs = JSON.stringify(args);
}
/**
 * 清理元素上缓存的 i18n 元信息。
 *
 * @param {HTMLElement} element - 目标元素
 * @returns {void}
 */
function clearLocalizedMessageMeta(element) {
    delete element.dataset.messageKey;
    delete element.dataset.messageArgs;
}
/**
 * 读取元素上缓存的 i18n 占位参数。
 *
 * @param {HTMLElement} element - 目标元素
 * @returns {string[]} 占位参数列表
 */
function getLocalizedMessageArgs(element) {
    const rawArgs = element.dataset.messageArgs;
    if (!rawArgs)
        return [];
    try {
        const parsed = JSON.parse(rawArgs);
        return Array.isArray(parsed) ? parsed.map((item) => String(item)) : [];
    }
    catch {
        return [];
    }
}
/**
 * 根据成功/失败状态生成状态提示图标。
 *
 * @param {boolean} isSuccess - 是否为成功状态
 * @returns {string} SVG 字符串
 */
function getStatusIconSvg(isSuccess) {
    return isSuccess
        ? '<svg class="status-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>'
        : '<svg class="status-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>';
}
/**
 * 渲染底部状态提示的完整 HTML。
 *
 * @param {HTMLElement} statusDiv - 状态提示容器
 * @param {string} messageKey - 文案翻译键
 * @param {boolean} isSuccess - 是否使用成功态图标
 * @param {string[]} [args=[]] - 文案占位参数
 * @returns {void}
 */
function renderStatusMessage(statusDiv, messageKey, isSuccess, args = []) {
    statusDiv.innerHTML = getStatusIconSvg(isSuccess) + t(messageKey, ...args);
}
/** 获取节点搜索框。 */
function getSearchInput() {
    return document.getElementById("search-input");
}
/** 获取设置面板中的“仅显示可注入节点”勾选框。 */
function getInjectableOnlyToggle() {
    return document.getElementById("injectable-only-toggle");
}
/** 获取当前节点 JSON 编辑框。 */
function getJsonTextarea() {
    return document.getElementById("json-textarea");
}
/**
 * 收集当前节点编辑区里会随选中状态联动启用/禁用的按钮。
 *
 * @returns {HTMLButtonElement[]} 按钮列表
 */
function getEditorButtons() {
    return [
        document.getElementById("validate-json-btn"),
        document.getElementById("format-json-btn"),
        document.getElementById("clear-draft-btn"),
        document.getElementById("inject-termination-btn"),
    ];
}
// 页面初始化后立即绑定交互并绘制首屏注入页。
document.addEventListener("DOMContentLoaded", () => {
    setupEventListeners();
    renderInjectionPage();
});
/**
 * 绑定注入页所需的所有 DOM 事件。
 *
 * @returns {void}
 */
function setupEventListeners() {
    const nodeList = document.getElementById("node-list"); // 左侧节点浏览容器
    const validateButton = document.getElementById("validate-json-btn"); // 校验按钮
    const formatButton = document.getElementById("format-json-btn"); // 格式化按钮
    const clearButton = document.getElementById("clear-draft-btn"); // 清空草稿按钮
    const injectTerminationButton = document.getElementById("inject-termination-btn"); // 节点级终止符注入按钮
    const submitButton = document.getElementById("submit-btn"); // 批量提交按钮
    if (!nodeList ||
        !validateButton ||
        !formatButton ||
        !clearButton ||
        !injectTerminationButton ||
        !submitButton) {
        return;
    }
    // 搜索节点时实时过滤左侧节点浏览列表。
    getSearchInput().addEventListener("input", (e) => {
        renderNodeList(e.target.value);
    });
    // 编辑 JSON 时同步写回对应节点草稿，并更新右侧提示与底部预览。
    getJsonTextarea().addEventListener("input", (e) => {
        if (!currentNodeName)
            return;
        const nextValue = e.target.value;
        setDraftForNode(currentNodeName, nextValue);
        renderNodeList(getSearchInput().value);
        renderDraftList();
        validateCurrentDraft(true);
        updateSubmitButtonAvailability();
    });
    // 节点浏览列表采用事件委托，统一处理节点切换。
    nodeList.addEventListener("click", (e) => {
        const item = e.target.closest(".node-item[data-node]"); // 点击命中的节点项
        const nodeName = item?.dataset.node; // 节点项上缓存的节点名
        if (nodeName) {
            selectNode(nodeName);
        }
    });
    // 编辑器底部操作按钮。
    validateButton.addEventListener("click", () => {
        validateCurrentDraft(true);
    });
    formatButton.addEventListener("click", formatCurrentDraft);
    clearButton.addEventListener("click", clearCurrentDraft);
    injectTerminationButton.addEventListener("click", handleInjectTermination);
    submitButton.addEventListener("click", handleSubmit);
}
/**
 * 判断节点当前是否仍允许接收注入。
 * 已停止或已消失节点不能继续提交。
 *
 * @param {string} nodeName - 节点名称
 * @returns {boolean} 是否可注入
 */
function isInjectableNode(nodeName) {
    const status = nodeStatuses[nodeName];
    return Boolean(status) && status.status !== 2;
}
/**
 * 将草稿状态与最新节点状态快照对齐。
 * - 已消失或已不可注入节点的草稿会被清理
 * - 当前编辑节点如果已不可注入，则取消当前选择
 *
 * @returns {void}
 */
function syncInjectionStateWithStatuses() {
    for (const nodeName of Object.keys(nodeDrafts)) {
        if (!isInjectableNode(nodeName)) {
            delete nodeDrafts[nodeName];
        }
    }
    if (currentNodeName && !isInjectableNode(currentNodeName)) {
        currentNodeName = null;
    }
}
/**
 * 刷新注入页的三个主要区域：
 * - 左侧节点浏览
 * - 当前节点编辑器
 * - 底部待发送数据预览
 *
 * @returns {void}
 */
function renderInjectionPage() {
    syncInjectionStateWithStatuses();
    renderNodeList(getSearchInput().value);
    renderCurrentNodeEditor();
    renderDraftList();
    updateSubmitButtonAvailability();
}
/**
 * 渲染左侧节点浏览列表。
 *
 * @param {string} [searchTerm=""] - 搜索关键词
 * @returns {void}
 */
function renderNodeList(searchTerm = "") {
    const nodeListEl = document.getElementById("node-list");
    if (!nodeListEl)
        return;
    syncInjectionStateWithStatuses();
    const normalizedSearch = searchTerm.toLowerCase().trim();
    const injectableOnly = getInjectableOnlyToggle().checked;
    const visibleNodes = Object.keys(nodeStatuses).filter((nodeName) => {
        if (injectableOnly && !isInjectableNode(nodeName))
            return false;
        if (!normalizedSearch)
            return true;
        return nodeName.toLowerCase().includes(normalizedSearch);
    });
    if (!visibleNodes.length) {
        nodeListEl.innerHTML = `<div class="empty-placeholder">${t("injection.noNodes")}</div>`;
        return;
    }
    nodeListEl.innerHTML = visibleNodes
        .map((nodeName) => {
        const activeClass = currentNodeName === nodeName ? "active-node" : "";
        const disabledClass = isInjectableNode(nodeName) ? "" : "disabled-node";
        const hasDraft = Boolean((nodeDrafts[nodeName] || "").trim());
        const dataAttr = isInjectableNode(nodeName)
            ? `data-node="${escapeHtml(nodeName)}"`
            : "";
        const rightTag = hasDraft
            ? `<span class="node-side-tag">${t("injection.draftEdited")}</span>`
            : "";
        return `
        <div class="node-item ${activeClass} ${disabledClass}" ${dataAttr}>
          <div class="node-info">
            <div class="node-name">${escapeHtml(nodeName)}</div>
          </div>
          ${rightTag}
        </div>`;
    })
        .join("");
}
/**
 * 渲染“当前节点编辑”区的标题、tag 和输入框状态。
 *
 * @returns {void}
 */
function renderCurrentNodeEditor() {
    const currentNodeEl = document.getElementById("current-node-name"); // 当前节点标题文本
    const currentTagEl = document.getElementById("current-node-tag"); // 当前节点标题右侧 tag
    const textarea = getJsonTextarea(); // JSON 编辑框
    if (!currentNodeEl || !currentTagEl)
        return;
    const hasNode = Boolean(currentNodeName); // 当前是否已有选中的可编辑节点
    if (!hasNode) {
        // 未选择节点时，编辑器进入只读提示状态。
        currentNodeEl.textContent = t("injection.noNodeSelected");
        currentTagEl.textContent = "";
        currentTagEl.style.display = "none";
        textarea.value = "";
        textarea.placeholder = t("injection.selectNodeHint");
        textarea.disabled = true;
        setValidationMessage("injection.validationSelectNode", "neutral");
    }
    else {
        const currentNode = currentNodeName; // 收窄后的当前节点名
        if (!currentNode)
            return;
        // 已选择节点时，恢复该节点草稿并实时显示“已编辑”状态。
        currentNodeEl.textContent = currentNode;
        const hasDraft = Boolean((nodeDrafts[currentNode] || "").trim());
        currentTagEl.textContent = hasDraft ? t("injection.draftEdited") : "";
        currentTagEl.style.display = hasDraft ? "inline-flex" : "none";
        textarea.value = nodeDrafts[currentNode] || "";
        textarea.placeholder = t("injection.jsonPlaceholder");
        textarea.disabled = false;
        validateCurrentDraft(false);
    }
    for (const button of getEditorButtons()) {
        button.disabled = !hasNode;
    }
}
/**
 * 切换当前编辑节点。
 *
 * @param {string} nodeName - 节点名称
 * @returns {void}
 */
function selectNode(nodeName) {
    if (!isInjectableNode(nodeName)) {
        syncInjectionStateWithStatuses();
        renderInjectionPage();
        return;
    }
    currentNodeName = nodeName;
    renderInjectionPage();
}
/**
 * 写入某个节点的草稿文本。
 * 空白文本会直接清除该节点草稿。
 *
 * @param {string} nodeName - 节点名称
 * @param {string} value - 草稿文本
 * @returns {void}
 */
function setDraftForNode(nodeName, value) {
    if (value.trim()) {
        nodeDrafts[nodeName] = value;
    }
    else {
        delete nodeDrafts[nodeName];
    }
}
/**
 * 从错误日志预填一条任务到注入页。
 *
 * @param {string} nodeName - 目标节点
 * @param {unknown} taskData - 原始任务数据
 * @param {boolean} [switchTab=true] - 是否在预填后切换到任务注入页
 * @returns {void}
 */
function preloadInjectionDraftFromError(nodeName, taskData, switchTab = true) {
    currentNodeName = nodeName;
    const currentDraft = (nodeDrafts[nodeName] || "").trim();
    let nextTaskList = [taskData];
    if (currentDraft) {
        const parsed = parseDraftTaskList(currentDraft);
        if (parsed.ok) {
            nextTaskList = [...parsed.taskList, taskData];
        }
    }
    const nextDraft = JSON.stringify(nextTaskList, null, 2);
    setDraftForNode(nodeName, nextDraft);
    if (switchTab) {
        switchToInjectionTab();
    }
    renderInjectionPage();
    const textarea = getJsonTextarea();
    textarea.focus();
    textarea.setSelectionRange(textarea.value.length, textarea.value.length);
}
/**
 * 将节点草稿解析为任务列表。
 * 任务注入的新结构要求每个节点值都必须是 JSON 数组。
 *
 * @param {string} draftText - 节点草稿文本
 * @returns {{ ok: true; taskList: unknown[] } | { ok: false; reason: "invalid_json" | "not_array" }}
 */
function parseDraftTaskList(draftText) {
    try {
        const parsed = JSON.parse(draftText);
        if (!Array.isArray(parsed)) {
            return { ok: false, reason: "not_array" };
        }
        return { ok: true, taskList: parsed };
    }
    catch {
        return { ok: false, reason: "invalid_json" };
    }
}
/**
 * 构建最终提交给服务端的注入映射。
 *
 * @returns {{
 *   payload: Record<string, unknown[]>;
 *   invalidNode: string | null;
 *   invalidReason: "invalid_json" | "not_array" | null;
 * }}
 */
function buildPendingInjectionPayload() {
    const payload = {}; // 最终提交给后端的映射
    let invalidNode = null; // 首个校验失败的节点
    let invalidReason = null; // 失败原因
    for (const [nodeName, draftText] of Object.entries(nodeDrafts)) {
        if (!isInjectableNode(nodeName) || !draftText.trim())
            continue;
        const parsed = parseDraftTaskList(draftText);
        if (parsed.ok) {
            payload[nodeName] = parsed.taskList;
            continue;
        }
        if (!invalidNode) {
            invalidNode = nodeName;
            invalidReason = "reason" in parsed ? parsed.reason : "invalid_json";
        }
    }
    return { payload, invalidNode, invalidReason };
}
/**
 * 按是否存在可提交草稿刷新底部提交按钮状态。
 *
 * @returns {void}
 */
function updateSubmitButtonAvailability() {
    const submitBtn = document.getElementById("submit-btn");
    if (!submitBtn || submitBtn.dataset.loading === "true")
        return;
    submitBtn.disabled =
        Object.keys(buildPendingInjectionPayload().payload).length === 0;
}
/**
 * 渲染底部“待发送数据预览”。
 * 这里尽量贴近最终发送的数据结构，便于用户肉眼检查。
 *
 * @returns {void}
 */
function renderDraftList() {
    const draftPreview = document.getElementById("draft-preview");
    if (!draftPreview)
        return;
    const previewPayload = {}; // 供右侧 JSON 预览展示的数据
    for (const [nodeName, draftText] of Object.entries(nodeDrafts)) {
        if (!isInjectableNode(nodeName) || !draftText.trim())
            continue;
        const parsed = parseDraftTaskList(draftText);
        if (parsed.ok) {
            previewPayload[nodeName] = parsed.taskList;
        }
        else {
            const reason = "reason" in parsed ? parsed.reason : "invalid_json";
            previewPayload[nodeName] =
                reason === "invalid_json"
                    ? {
                        invalid_json: true,
                        task_list_raw: draftText,
                    }
                    : {
                        invalid_task_list: true,
                        task_list_raw: draftText,
                    };
        }
    }
    if (!Object.keys(previewPayload).length) {
        draftPreview.innerHTML = `<div class="empty-placeholder">${escapeHtml(t("injection.noDrafts"))}</div>`;
        return;
    }
    draftPreview.textContent = JSON.stringify(previewPayload, null, 2);
}
/**
 * 设置编辑区下方的校验状态文字。
 * 该区域同时承担错误、成功和中性提示的统一展示职责。
 *
 * @param {string} messageKey - 翻译键
 * @param {ValidationState} state - 展示状态
 * @param {string[]} [args=[]] - 占位参数
 * @returns {void}
 */
function setValidationMessage(messageKey, state, args = []) {
    const validationDiv = document.getElementById("json-validation");
    setLocalizedMessageMeta(validationDiv, messageKey, args);
    validationDiv.textContent = t(messageKey, ...args);
    validationDiv.className = `validation-message validation-${state}`;
}
/**
 * 清空编辑区下方的提示文字。
 *
 * @returns {void}
 */
function clearValidationMessage() {
    const validationDiv = document.getElementById("json-validation");
    clearLocalizedMessageMeta(validationDiv);
    validationDiv.textContent = "";
    validationDiv.className = "validation-message";
}
/**
 * 校验当前节点草稿的 JSON 格式。
 *
 * @param {boolean} [showSyntaxError=true] - 是否显示内联语法错误
 * @returns {boolean} 当前草稿是否为合法 JSON 数组
 */
function validateCurrentDraft(showSyntaxError = true) {
    if (!currentNodeName) {
        setValidationMessage("injection.validationSelectNode", "neutral");
        return false;
    }
    const draftText = (nodeDrafts[currentNodeName] || "").trim();
    if (!draftText) {
        setValidationMessage("injection.validationEmpty", "neutral");
        return false;
    }
    const parsed = parseDraftTaskList(draftText);
    if (parsed.ok) {
        setValidationMessage("injection.validationOk", "success");
        return true;
    }
    const reason = "reason" in parsed ? parsed.reason : "invalid_json";
    setValidationMessage(reason === "invalid_json"
        ? "injection.invalidJson"
        : "injection.invalidTaskList", "error");
    return false;
}
/**
 * 对当前节点草稿执行 JSON 格式化。
 *
 * @returns {void}
 */
function formatCurrentDraft() {
    if (!currentNodeName) {
        showStatus("injection.selectNodeRequired", false);
        return;
    }
    const draftText = (nodeDrafts[currentNodeName] || "").trim();
    if (!draftText) {
        setValidationMessage("injection.validationEmpty", "neutral");
        return;
    }
    try {
        const formatted = JSON.stringify(JSON.parse(draftText), null, 2);
        setDraftForNode(currentNodeName, formatted);
        getJsonTextarea().value = formatted;
        renderNodeList(getSearchInput().value);
        renderDraftList();
        validateCurrentDraft(false);
        updateSubmitButtonAvailability();
    }
    catch {
        validateCurrentDraft(true);
    }
}
/**
 * 清空当前节点草稿与编辑区内容。
 *
 * @returns {void}
 */
function clearCurrentDraft() {
    if (!currentNodeName) {
        showStatus("injection.selectNodeRequired", false);
        return;
    }
    delete nodeDrafts[currentNodeName];
    getJsonTextarea().value = "";
    renderNodeList(getSearchInput().value);
    renderDraftList();
    setValidationMessage("injection.validationEmpty", "neutral");
    updateSubmitButtonAvailability();
}
/**
 * 为当前选中节点立即注入终止符。
 *
 * @returns {Promise<void>}
 */
async function handleInjectTermination() {
    if (!currentNodeName) {
        showStatus("injection.selectNodeRequired", false);
        return;
    }
    const targetNode = currentNodeName;
    setTerminationButtonLoading(true);
    try {
        const response = await fetch("/api/push_injection_terminations", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify([targetNode]),
        });
        if (!response.ok)
            throw new Error(`HTTP ${response.status}`);
        showStatus("injection.terminationInjected", true, targetNode);
    }
    catch (e) {
        console.error(e);
        showStatus("injection.terminationInjectFailed", false, targetNode);
    }
    finally {
        setTerminationButtonLoading(false);
    }
}
/**
 * 显示底部提交结果提示，并自动在 3 秒后隐藏。
 *
 * @param {string} messageKey - 翻译键
 * @param {boolean} [isSuccess=false] - 是否为成功态
 * @param {...string[]} args - 占位参数
 * @returns {void}
 */
function showStatus(messageKey, isSuccess = false, ...args) {
    const statusDiv = document.getElementById("status-message");
    setLocalizedMessageMeta(statusDiv, messageKey, args);
    renderStatusMessage(statusDiv, messageKey, isSuccess, args);
    statusDiv.className = `status-message ${isSuccess ? "status-success" : "status-error"}`;
    statusDiv.style.visibility = "visible";
    if (statusHideTimer !== null) {
        window.clearTimeout(statusHideTimer);
    }
    statusHideTimer = window.setTimeout(() => {
        statusDiv.style.visibility = "hidden";
    }, 3000);
}
/**
 * 提交所有待发送节点草稿。
 * 提交前会再次验证每个节点都是 JSON 数组，并统一发送为 { node_name: [tasklist] }。
 *
 * @returns {Promise<void>}
 */
async function handleSubmit() {
    syncInjectionStateWithStatuses();
    const { payload, invalidNode, invalidReason } = buildPendingInjectionPayload();
    const targetNodes = Object.keys(payload);
    if (invalidNode) {
        currentNodeName = invalidNode;
        renderInjectionPage();
        showStatus(invalidReason === "invalid_json"
            ? "injection.invalidNodeJson"
            : "injection.invalidNodeTaskList", false, invalidNode);
        return;
    }
    if (!targetNodes.length) {
        showStatus("injection.noDraftsToSubmit", false);
        return;
    }
    setButtonLoading(true);
    try {
        const response = await fetch("/api/push_injection_tasks", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        if (!response.ok)
            throw new Error(`HTTP ${response.status}`);
        nodeDrafts = {};
        renderInjectionPage();
        showStatus("injection.successBatch", true, String(targetNodes.length));
    }
    catch (e) {
        console.error(e);
        showStatus("injection.failed", false);
    }
    finally {
        setButtonLoading(false);
    }
}
/**
 * 设置提交按钮的加载状态。
 *
 * @param {boolean} loading - 是否进入提交中状态
 * @returns {void}
 */
function setButtonLoading(loading) {
    const submitBtn = document.getElementById("submit-btn"); // 提交按钮 DOM
    submitBtn.dataset.loading = loading ? "true" : "false";
    if (loading) {
        // 加载中时替换按钮内容并锁定重复提交。
        submitBtn.innerHTML = `<div class="spinner"></div>${t("injection.submitting")}`;
        submitBtn.disabled = true;
    }
    else {
        // 结束加载后恢复按钮文案，并重新按当前草稿状态判断是否可提交。
        submitBtn.innerHTML = t("injection.submitAllDrafts");
        updateSubmitButtonAvailability();
    }
}
/**
 * 设置终止符注入按钮的加载状态。
 *
 * @param {boolean} loading - 是否进入提交中状态
 * @returns {void}
 */
function setTerminationButtonLoading(loading) {
    const terminationBtn = document.getElementById("inject-termination-btn");
    terminationBtn.dataset.loading = loading ? "true" : "false";
    if (loading) {
        terminationBtn.textContent = t("injection.terminationInjecting");
        terminationBtn.disabled = true;
    }
    else {
        terminationBtn.textContent = t("injection.injectTermination");
        terminationBtn.disabled = !Boolean(currentNodeName);
    }
}
/**
 * 在语言切换后，重绘注入页中所有动态文本。
 * 包括：错误提示、校验提示、底部状态提示和草稿预览相关文案。
 *
 * @returns {void}
 */
function refreshInjectionLocalizedText() {
    const validationDiv = document.getElementById("json-validation"); // 编辑器下方校验提示
    const validationMessageKey = validationDiv.dataset.messageKey; // 当前校验提示翻译键
    if (validationMessageKey) {
        validationDiv.textContent = t(validationMessageKey, ...getLocalizedMessageArgs(validationDiv));
    }
    const statusDiv = document.getElementById("status-message"); // 预览卡底部状态提示
    const statusMessageKey = statusDiv.dataset.messageKey; // 当前状态提示翻译键
    if (statusMessageKey) {
        renderStatusMessage(statusDiv, statusMessageKey, statusDiv.classList.contains("status-success"), getLocalizedMessageArgs(statusDiv));
    }
    renderInjectionPage();
    const submitBtn = document.getElementById("submit-btn"); // 提交按钮
    if (submitBtn.dataset.loading === "true") {
        submitBtn.innerHTML = `<div class="spinner"></div>${t("injection.submitting")}`;
    }
}
