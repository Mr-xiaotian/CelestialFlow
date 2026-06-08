/**
 * 任务手动注入模块
 * 当前设计改为单节点编辑：每次只编辑并提交一个节点的注入数据。
 */

/** 校验提示的展示状态。 */
type ValidationState = "success" | "error" | "neutral";

// ======== 页面级状态 ========
// 当前正在编辑的节点名称；未选择节点时为 null。
let currentNodeName: string | null = null;
// 每个节点各自维护一份 JSON 草稿文本。
let nodeDrafts: Record<string, string> = {};
// 状态提示的自动隐藏定时器，避免重复触发时相互覆盖。
let statusHideTimer: number | null = null;

/**
 * 为动态提示元素记录 i18n 元信息，便于语言切换后重绘。
 *
 * @param {HTMLElement} element - 目标元素
 * @param {string} messageKey - 文案翻译键
 * @param {string[]} [args=[]] - 占位参数
 * @returns {void}
 */
function setLocalizedMessageMeta(
  element: HTMLElement,
  messageKey: string,
  args: string[] = [],
) {
  element.dataset.messageKey = messageKey;
  element.dataset.messageArgs = JSON.stringify(args);
}

/**
 * 清理元素上缓存的 i18n 元信息。
 *
 * @param {HTMLElement} element - 目标元素
 * @returns {void}
 */
function clearLocalizedMessageMeta(element: HTMLElement) {
  delete element.dataset.messageKey;
  delete element.dataset.messageArgs;
}

/**
 * 读取元素上缓存的 i18n 占位参数。
 *
 * @param {HTMLElement} element - 目标元素
 * @returns {string[]} 占位参数列表
 */
function getLocalizedMessageArgs(element: HTMLElement): string[] {
  const rawArgs = element.dataset.messageArgs;
  if (!rawArgs) return [];
  try {
    const parsed = JSON.parse(rawArgs);
    return Array.isArray(parsed) ? parsed.map((item) => String(item)) : [];
  } catch {
    return [];
  }
}

/**
 * 根据成功/失败状态生成状态提示图标。
 *
 * @param {boolean} isSuccess - 是否为成功状态
 * @returns {string} SVG 字符串
 */
function getStatusIconSvg(isSuccess: boolean): string {
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
function renderStatusMessage(
  statusDiv: HTMLElement,
  messageKey: string,
  isSuccess: boolean,
  args: string[] = [],
) {
  statusDiv.innerHTML = getStatusIconSvg(isSuccess) + t(messageKey, ...args);
}

/** 获取节点搜索框。 */
function getSearchInput(): HTMLInputElement {
  return document.getElementById("search-input") as HTMLInputElement;
}

/** 获取“仅显示可注入节点”勾选框。 */
function getInjectableOnlyToggle(): HTMLInputElement {
  return document.getElementById("injectable-only-toggle") as HTMLInputElement;
}

/** 获取当前节点 JSON 编辑框。 */
function getJsonTextarea(): HTMLTextAreaElement {
  return document.getElementById("json-textarea") as HTMLTextAreaElement;
}

/**
 * 收集当前节点编辑区里会随选中状态联动启用/禁用的按钮。
 *
 * @returns {HTMLButtonElement[]} 按钮列表
 */
function getEditorButtons(): HTMLButtonElement[] {
  return [
    document.getElementById("submit-btn") as HTMLButtonElement,
    document.getElementById("validate-json-btn") as HTMLButtonElement,
    document.getElementById("format-json-btn") as HTMLButtonElement,
    document.getElementById("clear-draft-btn") as HTMLButtonElement,
    document.getElementById("fill-termination-btn") as HTMLButtonElement,
  ];
}

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
  // 搜索节点时实时过滤左侧节点浏览列表。
  getSearchInput().addEventListener("input", (e) => {
    renderNodeList((e.target as HTMLInputElement).value);
  });

  // 切换“仅显示可注入节点”时同时刷新列表和待发送预览。
  getInjectableOnlyToggle().addEventListener("change", () => {
    renderNodeList(getSearchInput().value);
    renderDraftList();
  });

  // 编辑 JSON 时同步写回对应节点草稿，并更新右侧提示与底部预览。
  getJsonTextarea().addEventListener("input", (e) => {
    if (!currentNodeName) return;
    const nextValue = (e.target as HTMLTextAreaElement).value;
    setDraftForNode(currentNodeName, nextValue);
    renderNodeList(getSearchInput().value);
    renderDraftList();
    validateCurrentDraft(true);
  });

  // 节点浏览列表采用事件委托，统一处理节点切换。
  document.getElementById("node-list").addEventListener("click", (e) => {
    const item = (e.target as HTMLElement).closest<HTMLElement>(".node-item[data-node]");
    const nodeName = item?.dataset.node;
    if (nodeName) {
      selectNode(nodeName);
    }
  });

  // 编辑器底部操作按钮。
  document.getElementById("validate-json-btn").addEventListener("click", () => {
    validateCurrentDraft(true);
  });
  document.getElementById("format-json-btn").addEventListener("click", formatCurrentDraft);
  document.getElementById("clear-draft-btn").addEventListener("click", clearCurrentDraft);
  document.getElementById("fill-termination-btn").addEventListener("click", fillTerminationDraft);
  document.getElementById("submit-btn").addEventListener("click", handleSubmit);
}

/**
 * 判断节点当前是否仍允许接收注入。
 * 已停止或已消失节点不能继续提交。
 *
 * @param {string} nodeName - 节点名称
 * @returns {boolean} 是否可注入
 */
function isInjectableNode(nodeName: string): boolean {
  const status = nodeStatuses[nodeName];
  return Boolean(status) && status.status !== 2;
}

/**
 * 将草稿状态与最新节点状态快照对齐。
 * - 已消失节点的草稿会被清理
 * - 当前编辑节点如果已不可注入，则取消当前选择
 *
 * @returns {void}
 */
function syncInjectionStateWithStatuses() {
  for (const nodeName of Object.keys(nodeDrafts)) {
    if (!nodeStatuses[nodeName]) {
      delete nodeDrafts[nodeName];
    }
  }

  if (currentNodeName && !isInjectableNode(currentNodeName)) {
    currentNodeName = null;
  }
}

/**
 * 根据节点运行状态生成旧版 badge 描述。
 * 当前主要保留为状态文案工具，便于其他位置复用。
 *
 * @param {string} nodeName - 节点名称
 * @returns {{ badgeClass: string; badgeText: string }} 展示信息
 */
function getNodeBadgeInfo(nodeName: string): { badgeClass: string; badgeText: string } {
  const status = nodeStatuses[nodeName]?.status;
  if (status === 1) {
    return { badgeClass: "badge-running", badgeText: t("injection.running") };
  }
  if (status === 2) {
    return { badgeClass: "badge-completed", badgeText: t("injection.stopped") };
  }
  return { badgeClass: "badge-inactive", badgeText: t("injection.notRunning") };
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
  renderNodeList(getSearchInput()?.value || "");
  renderCurrentNodeEditor();
  renderDraftList();
}

/**
 * 渲染左侧节点浏览列表。
 *
 * @param {string} [searchTerm=""] - 搜索关键词
 * @returns {void}
 */
function renderNodeList(searchTerm = "") {
  const nodeListEl = document.getElementById("node-list");
  if (!nodeListEl) return;

  syncInjectionStateWithStatuses();

  const normalizedSearch = searchTerm.toLowerCase().trim();
  const injectableOnly = getInjectableOnlyToggle().checked;
  const visibleNodes = Object.keys(nodeStatuses).filter((nodeName) => {
    if (injectableOnly && !isInjectableNode(nodeName)) return false;
    if (!normalizedSearch) return true;
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
      const hasDraft = Boolean(nodeDrafts[nodeName]?.trim());
      const dataAttr = isInjectableNode(nodeName) ? `data-node="${escapeHtml(nodeName)}"` : "";
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
  const currentNodeEl = document.getElementById("current-node-name");
  const currentTagEl = document.getElementById("current-node-tag");
  const textarea = getJsonTextarea();
  const hasNode = Boolean(currentNodeName);

  if (!hasNode) {
    currentNodeEl.textContent = t("injection.noNodeSelected");
    currentTagEl.textContent = "";
    currentTagEl.style.display = "none";
    textarea.value = "";
    textarea.placeholder = t("injection.selectNodeHint");
    textarea.disabled = true;
    hideError("json-error");
    setValidationMessage("injection.validationSelectNode", "neutral");
  } else {
    currentNodeEl.textContent = currentNodeName;
    const hasDraft = Boolean(nodeDrafts[currentNodeName]?.trim());
    currentTagEl.textContent = hasDraft ? t("injection.draftEdited") : "";
    currentTagEl.style.display = hasDraft ? "inline-flex" : "none";
    textarea.value = nodeDrafts[currentNodeName] || "";
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
function selectNode(nodeName: string) {
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
function setDraftForNode(nodeName: string, value: string) {
  if (value.trim()) {
    nodeDrafts[nodeName] = value;
  } else {
    delete nodeDrafts[nodeName];
  }
}

/**
 * 渲染底部“待发送数据预览”。
 * 这里尽量贴近最终发送的数据结构，便于用户肉眼检查。
 *
 * @returns {void}
 */
function renderDraftList() {
  const draftPreview = document.getElementById("draft-preview");
  if (!draftPreview) return;

  const pendingEntries = Object.entries(nodeDrafts)
    .filter(([, draftText]) => draftText.trim())
    .map(([nodeName, draftText]) => {
      try {
        return {
          node: nodeName,
          task_datas: JSON.parse(draftText),
        };
      } catch {
        return {
          node: nodeName,
          invalid_json: true,
          task_datas_raw: draftText,
        };
      }
    });

  if (!pendingEntries.length) {
    draftPreview.textContent = t("injection.noDrafts");
    return;
  }

  draftPreview.textContent = JSON.stringify(pendingEntries, null, 2);
}

/**
 * 显示 JSON 语法错误等内联错误信息。
 *
 * @param {string} elementId - 错误信息容器 ID
 * @param {string} messageKey - 翻译键
 * @param {...string[]} args - 占位参数
 * @returns {void}
 */
function showError(elementId: string, messageKey: string, ...args: string[]) {
  const errorDiv = document.getElementById(elementId) as HTMLElement;
  setLocalizedMessageMeta(errorDiv, messageKey, args);
  errorDiv.textContent = t(messageKey, ...args);
  errorDiv.style.display = "block";
}

/**
 * 隐藏指定的内联错误信息。
 *
 * @param {string} elementId - 错误信息容器 ID
 * @returns {void}
 */
function hideError(elementId: string) {
  const errorDiv = document.getElementById(elementId) as HTMLElement;
  errorDiv.style.display = "none";
  clearLocalizedMessageMeta(errorDiv);
}

/**
 * 设置编辑区下方的校验状态文字。
 *
 * @param {string} messageKey - 翻译键
 * @param {ValidationState} state - 展示状态
 * @param {string[]} [args=[]] - 占位参数
 * @returns {void}
 */
function setValidationMessage(
  messageKey: string,
  state: ValidationState,
  args: string[] = [],
) {
  const validationDiv = document.getElementById("json-validation") as HTMLElement;
  setLocalizedMessageMeta(validationDiv, messageKey, args);
  validationDiv.textContent = t(messageKey, ...args);
  validationDiv.className = `validation-message validation-${state}`;
}

/**
 * 校验当前节点草稿的 JSON 格式。
 *
 * @param {boolean} [showSyntaxError=true] - 是否显示内联语法错误
 * @returns {boolean} 当前草稿是否为合法 JSON
 */
function validateCurrentDraft(showSyntaxError = true): boolean {
  if (!currentNodeName) {
    hideError("json-error");
    setValidationMessage("injection.validationSelectNode", "neutral");
    return false;
  }

  const draftText = (nodeDrafts[currentNodeName] || "").trim();
  if (!draftText) {
    hideError("json-error");
    setValidationMessage("injection.validationEmpty", "neutral");
    return false;
  }

  try {
    JSON.parse(draftText);
    hideError("json-error");
    setValidationMessage("injection.validationOk", "success");
    return true;
  } catch {
    if (showSyntaxError) {
      showError("json-error", "json.invalid");
    } else {
      hideError("json-error");
    }
    setValidationMessage("injection.invalidJson", "error");
    return false;
  }
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
  } catch {
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
  hideError("json-error");
  setValidationMessage("injection.validationEmpty", "neutral");
}

/**
 * 为当前节点填入终止信号模板。
 *
 * @returns {void}
 */
function fillTerminationDraft() {
  if (!currentNodeName) {
    showStatus("injection.selectNodeRequired", false);
    return;
  }

  const terminationDraft = JSON.stringify(["TERMINATION_SIGNAL"], null, 2);
  setDraftForNode(currentNodeName, terminationDraft);
  getJsonTextarea().value = terminationDraft;
  renderNodeList(getSearchInput().value);
  renderDraftList();
  validateCurrentDraft(false);
}

/**
 * 显示底部提交结果提示，并自动在 3 秒后隐藏。
 *
 * @param {string} messageKey - 翻译键
 * @param {boolean} [isSuccess=false] - 是否为成功态
 * @param {...string[]} args - 占位参数
 * @returns {void}
 */
function showStatus(messageKey: string, isSuccess = false, ...args: string[]) {
  const statusDiv = document.getElementById("status-message") as HTMLElement;
  setLocalizedMessageMeta(statusDiv, messageKey, args);
  renderStatusMessage(statusDiv, messageKey, isSuccess, args);
  statusDiv.className = `status-message ${
    isSuccess ? "status-success" : "status-error"
  }`;
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
 * 提交前会再次验证每个节点的 JSON 格式，并在成功后清空全部草稿。
 *
 * @returns {Promise<void>}
 */
async function handleSubmit() {
  syncInjectionStateWithStatuses();

  const draftEntries = Object.entries(nodeDrafts).filter(
    ([nodeName, draftText]) => isInjectableNode(nodeName) && draftText.trim(),
  );

  if (!draftEntries.length) {
    showStatus("injection.noDraftsToSubmit", false);
    return;
  }

  for (const [nodeName, draftText] of draftEntries) {
    try {
      JSON.parse(draftText);
    } catch {
      currentNodeName = nodeName;
      renderInjectionPage();
      showStatus("injection.invalidNodeJson", false, nodeName);
      return;
    }
  }

  setButtonLoading(true);

  try {
    for (const [nodeName, draftText] of draftEntries) {
      const response = await fetch("/api/push_injection_tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          node: nodeName,
          task_datas: JSON.parse(draftText),
          timestamp: new Date().toISOString(),
        }),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
    }

    nodeDrafts = {};
    renderInjectionPage();
    showStatus("injection.successBatch", true, String(draftEntries.length));
  } catch (e) {
    console.error(e);
    showStatus("injection.failed", false);
  } finally {
    setButtonLoading(false);
  }
}

/**
 * 设置提交按钮的加载状态。
 *
 * @param {boolean} loading - 是否进入提交中状态
 * @returns {void}
 */
function setButtonLoading(loading: boolean) {
  const submitBtn = document.getElementById("submit-btn") as HTMLButtonElement;

  submitBtn.dataset.loading = loading ? "true" : "false";

  if (loading) {
    submitBtn.innerHTML = `<div class="spinner"></div>${t("injection.submitting")}`;
    submitBtn.disabled = true;
  } else {
    submitBtn.innerHTML = t("injection.submitAllDrafts");
    submitBtn.disabled = !currentNodeName;
  }
}

/**
 * 在语言切换后，重绘注入页中所有动态文本。
 * 包括：错误提示、校验提示、底部状态提示和草稿预览相关文案。
 *
 * @returns {void}
 */
function refreshInjectionLocalizedText() {
  const jsonError = document.getElementById("json-error") as HTMLElement;
  const jsonErrorMessageKey = jsonError.dataset.messageKey;
  if (jsonErrorMessageKey) {
    jsonError.textContent = t(
      jsonErrorMessageKey,
      ...getLocalizedMessageArgs(jsonError),
    );
  }

  const validationDiv = document.getElementById("json-validation") as HTMLElement;
  const validationMessageKey = validationDiv.dataset.messageKey;
  if (validationMessageKey) {
    validationDiv.textContent = t(
      validationMessageKey,
      ...getLocalizedMessageArgs(validationDiv),
    );
  }

  const statusDiv = document.getElementById("status-message") as HTMLElement;
  const statusMessageKey = statusDiv.dataset.messageKey;
  if (statusMessageKey) {
    renderStatusMessage(
      statusDiv,
      statusMessageKey,
      statusDiv.classList.contains("status-success"),
      getLocalizedMessageArgs(statusDiv),
    );
  }

  renderInjectionPage();

  const submitBtn = document.getElementById("submit-btn") as HTMLButtonElement;
  if (submitBtn.dataset.loading === "true") {
    submitBtn.innerHTML = `<div class="spinner"></div>${t("injection.submitting")}`;
  }
}
