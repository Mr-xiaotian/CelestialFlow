/**
 * 任务手动注入模块
 * 提供 UI 界面允许用户选择节点并手动注入 JSON 格式的任务数据或通过文件上传
 */

/** 被选中的注入目标节点描述信息 */
type SelectedNode = { 
  name: string;      // 节点名称
};

// 全局状态
let selectedNodes: SelectedNode[] = []; // 用户选中的注入目标节点
let currentInputMethod = "json"; // 当前输入方式（json / file）
let uploadedFile: { name: string; content: string } | null = null; // 已上传的文件内容

// 页面加载完成后初始化节点列表并绑定注入表单交互。
document.addEventListener("DOMContentLoaded", function () {
  renderNodeList();
  setupEventListeners();
});

/**
 * 设置页面元素的事件监听器
 * 包括搜索输入、JSON 输入验证、文件上传和提交按钮
 */
function setupEventListeners() {
  // 搜索节点列表时实时按关键词过滤可选节点。
  document
    .getElementById("search-input")
    .addEventListener("input", function (e) {
      const target = e.target as HTMLInputElement;
      renderNodeList(target.value);
    });

  // 输入 JSON 文本时立即做格式校验，尽早给出错误反馈。
  document
    .getElementById("json-textarea")
    .addEventListener("input", function (e) {
      const target = e.target as HTMLTextAreaElement;
      validateJSON(target.value);
    });

  // 选择上传文件后读取并校验 JSON 文件内容。
  document
    .getElementById("file-input")
    .addEventListener("change", handleFileUpload);

  // 点击提交按钮后执行注入请求流程。
  document
    .getElementById("submit-btn")
    .addEventListener("click", handleSubmit);

  // 通过事件委托统一处理“全选 / 清空”两个节点选择操作。
  document.querySelector(".button-group").addEventListener("click", (e) => {
    const button = (e.target as HTMLElement).closest<HTMLButtonElement>("button[data-selection-action]");
    if (!button) return;

    if (button.dataset.selectionAction === "select-all") {
      selectAllNodes();
    } else if (button.dataset.selectionAction === "clear") {
      clearSelection();
    }
  });

  // 通过 data-input-method 标记切换 JSON 输入和文件上传两种模式。
  document.querySelector(".input-toggle").addEventListener("click", (e) => {
    const button = (e.target as HTMLElement).closest<HTMLButtonElement>("button[data-input-method]");
    const method = button?.dataset.inputMethod;
    if (method) {
      switchInputMethod(method);
    }
  });

  // 一键填入终止信号示例，便于快速构造测试输入。
  document.getElementById("fill-termination-btn").addEventListener("click", fillTermination);

  // 点击节点列表项时切换该节点的选中状态。
  document.getElementById("node-list").addEventListener("click", (e) => {
    const item = (e.target as HTMLElement).closest<HTMLElement>(".node-item[data-node]");
    if (item) selectNode(item.dataset.node);
  });

  // 通过事件委托处理已选节点列表中的移除按钮。
  document.getElementById("selected-list").addEventListener("click", (e) => {
    const button = (e.target as HTMLElement).closest<HTMLButtonElement>("button[data-remove-node]");
    const nodeName = button?.dataset.removeNode;
    if (nodeName) {
      removeNode(nodeName);
    }
  });
}

/**
 * 渲染任务注入页面的节点列表
 * @param {string} searchTerm - 搜索关键词，用于过滤节点
 * @returns {void}
 */
function renderNodeList(searchTerm = "") {
  const nodeListEl = document.getElementById("node-list");
  if (!nodeListEl) return;

  const normalizedSearch = searchTerm.toLowerCase().trim();

  const nodeListHTML = Object.keys(nodeStatuses)
    .filter((nodeName) => {
      if (!normalizedSearch) return true;
      return nodeName.toLowerCase().includes(normalizedSearch);
    })
    .map((nodeName) => {
      // 根据 status 值确定样式和文本
      const status = nodeStatuses[nodeName].status;
      let badgeClass = "badge-inactive";
      let badgeText = t("injection.notRunning");
      if (status === 1) {
        badgeClass = "badge-running";
        badgeText = t("injection.running");
      } else if (status === 2) {
        badgeClass = "badge-completed";
        badgeText = t("injection.stopped");
      }

      // 禁止点击已停止的节点
      const dataAttr = status !== 2 ? `data-node="${escapeHtml(nodeName)}"` : "";
      const disabledClass = status === 2 ? "disabled-node" : "";

      return `
        <div class="node-item ${disabledClass}" ${dataAttr}>
          <div class="node-info">
            <div class="node-name">${escapeHtml(nodeName)}</div>
          </div>
          <span class="badge ${badgeClass}">${badgeText}</span>
        </div>`;
    })
    .join("");

  nodeListEl.innerHTML = nodeListHTML;
}

/**
 * 选择或取消选择节点
 * @param {string} nodeName - 节点名称
 */
function selectNode(nodeName: string) {
  const existing = selectedNodes.find((n) => n.name === nodeName);

  if (existing) {
    // 点击已选节点 = 取消选中
    selectedNodes = selectedNodes.filter((n) => n.name !== nodeName);
  } else {
    // 新选节点
    selectedNodes.push({ name: nodeName });
  }

  updateSelectedNodes();
}

/**
 * 从已选列表中移除节点
 * @param {string} nodeName - 节点名称
 */
function removeNode(nodeName: string) {
  selectedNodes = selectedNodes.filter((n) => n.name !== nodeName);
  updateSelectedNodes();
}

/**
 * 更新已选节点列表的 UI 显示
 * 显示已选数量和节点列表，如果为空则隐藏相关区域
 * @returns {void}
 */
function updateSelectedNodes() {
  const selectedSection = document.getElementById("selected-section");
  const selectedList = document.getElementById("selected-list");
  const selectedCount = document.getElementById("selected-count");

  if (selectedNodes.length === 0) {
    selectedSection.style.display = "none";
    return;
  }

  selectedSection.style.display = "block";
  selectedCount.textContent = String(selectedNodes.length);

  const selectedHTML = selectedNodes
    .map(
      (node) => `
        <div class="selected-item">
          <span class="selected-name">${escapeHtml(node.name)}</span>
          <button class="btn-remove" type="button" data-remove-node="${escapeHtml(node.name)}">
            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>`
    )
    .join("");

  selectedList.innerHTML = selectedHTML;
}

/**
 * 全选所有可用节点（排除已停止的节点）
 */
function selectAllNodes() {
  const filteredNodes = Object.entries(nodeStatuses)
    .filter(([, status]) => status.status !== 2)
    .map(([name]) => ({ name }));

  filteredNodes.forEach((node) => {
    if (!selectedNodes.find((n) => n.name === node.name)) {
      selectedNodes.push(node);
    }
  });

  updateSelectedNodes();
}

/**
 * 清空所有已选节点
 */
function clearSelection() {
  selectedNodes = [];
  updateSelectedNodes();
}

/**
 * 切换任务数据输入方式（JSON文本或文件上传）
 * @param {string} method - 输入方式，当前支持 `json` 或 `file`。
 * @returns {void}
 */
function switchInputMethod(method: string) {
  currentInputMethod = method;

  document
    .getElementById("json-toggle")
    .classList.toggle("active", method === "json");
  document
    .getElementById("file-toggle")
    .classList.toggle("active", method === "file");

  document
    .getElementById("json-input-section")
    .classList.toggle("hidden", method !== "json");
  document
    .getElementById("file-input-section")
    .classList.toggle("hidden", method !== "file");
}

/**
 * 填充预定义的终止信号 JSON
 * @returns {void}
 */
function fillTermination() {
  (document.getElementById("json-textarea") as HTMLTextAreaElement).value = JSON.stringify(
    ["TERMINATION_SIGNAL"],
    null,
    2
  );
  hideError("json-error");
}

/**
 * 处理文件上传事件
 * 读取 JSON 文件内容并验证格式
 * @param {Event} e - 文件选择事件
 * @returns {void}
 */
function handleFileUpload(e: Event) {
  const fileInput = e.target as HTMLInputElement;
  const file = fileInput.files?.[0];
  if (!file) return;

  if (!file.name.endsWith(".json")) {
    showError("file-error", t("injection.uploadJsonOnly"));
    return;
  }

  const reader = new FileReader();
  reader.onload = function (event: ProgressEvent<FileReader>) {
    try {
      const content = event.target?.result;
      if (typeof content !== "string") return;
      JSON.parse(content);

      uploadedFile = { name: file.name, content };
      document.getElementById("file-name").textContent = t("injection.uploaded", file.name);
      document.getElementById("file-info").style.display = "flex";
      hideError("file-error");
    } catch (e) {
      showError("file-error", t("injection.uploadInvalid"));
      uploadedFile = null;
      document.getElementById("file-info").style.display = "none";
    }
  };
  reader.readAsText(file);
}

/**
 * 显示错误信息
 * @param {string} elementId - 错误信息容器 ID
 * @param {string} message - 错误文本
 * @returns {void}
 */
function showError(elementId: string, message: string) {
  const errorDiv = document.getElementById(elementId) as HTMLElement;
  errorDiv.textContent = message;
  errorDiv.style.display = "block";
}

/**
 * 隐藏错误信息
 * @param {string} elementId - 错误信息容器 ID
 * @returns {void}
 */
function hideError(elementId: string) {
  (document.getElementById(elementId) as HTMLElement).style.display = "none";
}

/**
 * 验证 JSON 字符串格式是否合法
 * @param {string} text - JSON 字符串
 * @returns {boolean} 格式合法返回 true，否则返回 false
 */
function validateJSON(text: string): boolean {
  if (!text.trim()) {
    hideError("json-error");
    return true;
  }

  try {
    JSON.parse(text);
    hideError("json-error");
    return true;
  } catch {
    showError("json-error", t("json.invalid"));
    return false;
  }
}

/**
 * 显示操作状态提示（成功或失败）
 * @param {string} message - 要显示的提示 HTML 文本。
 * @param {boolean} [isSuccess=false] - 是否按成功态样式展示。
 * @returns {void}
 */
function showStatus(message: string, isSuccess = false) {
  const statusDiv = document.getElementById("status-message");
  const iconSVG = isSuccess
    ? '<svg class="status-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>'
    : '<svg class="status-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>';

  statusDiv.innerHTML = iconSVG + message;
  statusDiv.className = `status-message ${
    isSuccess ? "status-success" : "status-error"
  }`;
  statusDiv.style.visibility = "visible";

  setTimeout(() => {
    statusDiv.style.visibility = "hidden";
  }, 3000);
}

/**
 * 处理任务注入提交
 * 1. 验证节点选择和输入数据
 * 2. 遍历所有选定节点发送 POST 请求
 * 3. 根据结果显示成功或失败状态，并重置表单
 * @returns {Promise<void>}
 */
async function handleSubmit() {
  if (selectedNodes.length === 0) {
    showStatus(t("injection.selectNodeRequired"), false);
    return;
  }

  let taskData;
  if (currentInputMethod === "json") {
    const jsonText = (document.getElementById("json-textarea") as HTMLTextAreaElement).value.trim();
    if (!jsonText) {
      showStatus(t("injection.enterData"), false);
      return;
    }
    if (!validateJSON(jsonText)) {
      showStatus(t("injection.invalidJson"), false);
      return;
    }
    taskData = JSON.parse(jsonText);
  } else {
    if (!uploadedFile) {
      showStatus(t("injection.uploadRequired"), false);
      return;
    }
    taskData = JSON.parse(uploadedFile.content);
  }

  setButtonLoading(true);

  try {
    for (const node of selectedNodes) {
      const response = await fetch("/api/push_injection_tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          node: node.name,
          task_datas: taskData,
          timestamp: new Date().toISOString(),
        }),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
    }

    showStatus(t("injection.success"), true);
    clearForm();
  } catch (e) {
    console.error(e);
    showStatus(t("injection.failed"), false);
  } finally {
    setButtonLoading(false);
  }
}

/**
 * 设置提交按钮的加载状态
 * @param {boolean} loading - 是否正在加载
 * @returns {void}
 */
function setButtonLoading(loading: boolean) {
  const btn = document.getElementById("submit-btn") as HTMLButtonElement;
  if (loading) {
    btn.innerHTML = `<div class="spinner"></div>${t("injection.submitting")}`;
    btn.disabled = true;
  } else {
    btn.innerHTML = t("injection.submit");
    btn.disabled = false;
  }
}

/**
 * 重置任务注入表单
 * 清空选择、输入框和错误信息
 * @returns {void}
 */
function clearForm() {
  selectedNodes = [];
  updateSelectedNodes();
  (document.getElementById("json-textarea") as HTMLTextAreaElement).value = "";
  hideError("json-error");
  (document.getElementById("file-input") as HTMLInputElement).value = "";
  uploadedFile = null;
  document.getElementById("file-info").style.display = "none";
  hideError("file-error");
  (document.getElementById("search-input") as HTMLInputElement).value = "";
  renderNodeList();
}
