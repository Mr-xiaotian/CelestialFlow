let selectedNodes = [];
let currentInputMethod = "json";
let uploadedFile = null;

document.addEventListener("DOMContentLoaded", async function () {
  renderNodeList();
  setupEventListeners();
});

function setupEventListeners() {
  document
    .getElementById("search-input")
    .addEventListener("input", function (e) {
      renderNodeList(e.target.value);
    });

  document
    .getElementById("json-textarea")
    .addEventListener("input", function (e) {
      validateJSON(e.target.value);
    });

  document
    .getElementById("file-input")
    .addEventListener("change", handleFileUpload);

  document
    .getElementById("submit-btn")
    .addEventListener("click", handleSubmit);
}

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
      let badgeText = "未运行";
      if (status === 1) {
        badgeClass = "badge-running";
        badgeText = "运行中";
      } else if (status === 2) {
        badgeClass = "badge-completed";
        badgeText = "已停止";
      }

      // 禁止点击已停止的节点
      const clickable = status === 2 ? "" : `onclick="selectNode('${nodeName}')"`
      const disabledClass = status === 2 ? "disabled-node" : "";

      return `
        <div class="node-item ${disabledClass}" ${clickable}>
          <div class="node-info">
            <div class="node-name">${nodeName}</div>
          </div>
          <span class="badge ${badgeClass}">${badgeText}</span>
        </div>`;
    })
    .join("");

  document.getElementById("node-list").innerHTML = nodeListHTML;
}

function selectNode(nodeName) {
  const existing = selectedNodes.find((n) => n.name === nodeName);

  if (existing) {
    // 点击已选节点 = 取消选中
    selectedNodes = selectedNodes.filter((n) => n.name !== nodeName);
  } else {
    // 新选节点
    selectedNodes.push({
      name: nodeName,
      type: nodeStatuses[nodeName].execution_mode || "unknown",
    });
  }

  updateSelectedNodes();
}

function removeNode(nodeName) {
  selectedNodes = selectedNodes.filter((n) => n.name !== nodeName);
  updateSelectedNodes();
}

function updateSelectedNodes() {
  const selectedSection = document.getElementById("selected-section");
  const selectedList = document.getElementById("selected-list");
  const selectedCount = document.getElementById("selected-count");

  if (selectedNodes.length === 0) {
    selectedSection.style.display = "none";
    return;
  }

  selectedSection.style.display = "block";
  selectedCount.textContent = selectedNodes.length;

  const selectedHTML = selectedNodes
    .map(
      (node) => `
        <div class="selected-item">
          <span class="selected-name">${node.name}</span>
          <button class="remove-btn" onclick="removeNode('${node.name}')">
            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>`
    )
    .join("");

  selectedList.innerHTML = selectedHTML;
}

function selectAllNodes() {
  // const searchTerm = document.getElementById("search-input").value;

  const nodesArray = Object.keys(nodeStatuses).map(name => ({
    name,
    type: nodeStatuses[name].execution_mode,
    status: nodeStatuses[name].status
  }));

  const filteredNodes = nodesArray.filter(node =>
    node.status !== 2
  );

  filteredNodes.forEach((node) => {
    if (!selectedNodes.find((n) => n.name === node.name)) {
      selectedNodes.push(node);
    }
  });

  updateSelectedNodes();
}

function clearSelection() {
  selectedNodes = [];
  updateSelectedNodes();
}

function switchInputMethod(method) {
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

function fillTermination() {
  document.getElementById("json-textarea").value = JSON.stringify(
    ["TERMINATION_SIGNAL"],
    null,
    2
  );
  hideError("json-error");
}

function handleFileUpload(e) {
  const file = e.target.files[0];
  if (!file) return;

  if (!file.name.endsWith(".json")) {
    showError("file-error", "请上传 .json 格式的文件");
    return;
  }

  const reader = new FileReader();
  reader.onload = function (event) {
    try {
      const content = event.target.result;
      JSON.parse(content);

      uploadedFile = { name: file.name, content };
      document.getElementById("file-name").textContent = `已上传: ${file.name}`;
      document.getElementById("file-info").style.display = "flex";
      hideError("file-error");
    } catch (e) {
      showError("file-error", "上传文件无效，请检查JSON格式");
      uploadedFile = null;
      document.getElementById("file-info").style.display = "none";
    }
  };
  reader.readAsText(file);
}

function showError(elementId, message) {
  const errorDiv = document.getElementById(elementId);
  errorDiv.textContent = message;
  errorDiv.style.display = "block";
}

function hideError(elementId) {
  document.getElementById(elementId).style.display = "none";
}

function showStatus(message, isSuccess = false) {
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

async function handleSubmit() {
  if (selectedNodes.length === 0) {
    showStatus("请选择至少一个节点", false);
    return;
  }

  let taskData;
  if (currentInputMethod === "json") {
    const jsonText = document.getElementById("json-textarea").value.trim();
    if (!jsonText) {
      showStatus("请输入任务数据", false);
      return;
    }
    if (!validateJSON(jsonText)) {
      showStatus("JSON格式不合法", false);
      return;
    }
    taskData = JSON.parse(jsonText);
  } else {
    if (!uploadedFile) {
      showStatus("请上传任务文件", false);
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

    showStatus("任务已成功注入到所有选定节点", true);
    clearForm();
  } catch (e) {
    console.error(e);
    showStatus("任务注入失败，请重试", false);
  } finally {
    setButtonLoading(false);
  }
}

function setButtonLoading(loading) {
  const btn = document.getElementById("submit-btn");
  if (loading) {
    btn.innerHTML = '<div class="spinner"></div>提交中...';
    btn.disabled = true;
  } else {
    btn.innerHTML = "提交任务注入";
    btn.disabled = false;
  }
}

function clearForm() {
  selectedNodes = [];
  updateSelectedNodes();
  document.getElementById("json-textarea").value = "";
  hideError("json-error");
  document.getElementById("file-input").value = "";
  uploadedFile = null;
  document.getElementById("file-info").style.display = "none";
  hideError("file-error");
  document.getElementById("search-input").value = "";
  renderNodeList();
}
