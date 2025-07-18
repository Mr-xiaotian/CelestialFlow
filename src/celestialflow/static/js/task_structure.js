let structureData = [];
let previousStructureDataJSON = "";

const mermaidTitle = document.getElementById("mermaid-title");

async function loadStructure() {
  try {
    const res = await fetch("/api/get_structure");
    structureData = await res.json(); // 现在是数组格式
  } catch (e) {
    console.error("结构加载失败", e);
  }
}

function getNodeId(node) {
  return node.stage_name.replace(/\W+/g, "_");
}

function getShapeWrappedLabel(label, shape = "box") {
  switch (shape) {
    case "circle":
      return `((${label}))`;
    case "round":
      return `(${label})`;
    case "rhombus":
      return `{${label}}`;
    case "subgraph":
      return `[[${label}]]`;
    case "arrow":
      return `>${label}<`;
    default:
      return `[${label}]`; // 默认 box
  }
}

function renderMermaidFromTaskStructure() {
  const edges = new Set();
  const nodeLabels = new Map();
  const classDefs = [];
  const tagToId = {}; // "Grid_1_1[load_func]" -> "Grid_1_1"

  // ✅ 判断是否是暗黑主题
  const isDark = document.body.classList.contains("dark-theme");

  // ✅ 样式区块：根据主题切换
  const styleBlock = isDark
    ? `
classDef whiteNode fill:#1f2937,stroke:#e5e7eb,stroke-width:1px;
classDef greyNode fill:#374151,stroke:#9ca3af,stroke-width:1px;
classDef greenNode fill:#14532d,stroke:#22c55e,stroke-width:2px;
classDef blueNode fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px;
linkStyle default stroke:#9ca3af,stroke-width:1.5px;
`
    : `
classDef whiteNode fill:#ffffff,stroke:#333,stroke-width:1px;
classDef greyNode fill:#f3f4f6,stroke:#999,stroke-width:1px;
classDef greenNode fill:#dcfce7,stroke:#16a34a,stroke-width:2px;
classDef blueNode fill:#e0f2fe,stroke:#0ea5e9,stroke-width:2px;
linkStyle default stroke:#999,stroke-width:1.5px;
`;

const structureClassName = topologyData.class_name || "Mermaid";
mermaidTitle.textContent = `任务结构图（${structureClassName}）`;

  function walk(node) {
    const id = getNodeId(node);
    const label = `${node.stage_name}`;
    const tag = `${node.stage_name}[${node.func_name}]`;
    tagToId[tag] = id; // 保存 tag 到 ID 的映射

    let shape = "box";
    if (node.func_name === "_split_task") shape = "round";
    else if (node.func_name === "_trans_redis") shape = "subgraph";

    nodeLabels.set(id, getShapeWrappedLabel(label, shape));

    // 🧠 找对应状态 class
    const statusInfo = nodeStatuses?.[tag];
    let statusClass = "whiteNode";
    if (statusInfo) {
      if (statusInfo.status === 1) statusClass = "greenNode";
      else if (statusInfo.status === 2) statusClass = "greyNode";
    }
    classDefs.push(`  class ${id} ${statusClass};`);

    for (const child of node.next_stages || []) {
      const toId = getNodeId(child);
      const fromTag = `${node.stage_name}[${node.func_name}]`;
      const addNum = nodeStatuses?.[fromTag]?.add_tasks_successed || 0;
      const edgeLabel = addNum > 0 ? `|+${addNum}|` : "";

      edges.add(`  ${id} -->${""} ${toId}`);
      walk(child);
    }
  }

  structureData.forEach((graph) => walk(graph));

  // let defs = [];

  // if (topologyData.layout_mode === "serial") {
  //   const layers = topologyData.layers_dict || {};
  //   const sortedLayerKeys = Object.keys(layers).sort((a, b) => Number(a) - Number(b));
  //   for (const layer of sortedLayerKeys) {
  //     defs.push(`  subgraph layer_${layer}`);
  //     for (const tag of layers[layer]) {
  //       const id = tagToId[tag];
  //       const label = nodeLabels.get(id);
  //       if (id && label) {
  //         defs.push(`    ${id}${label}`);
  //       }
  //     }
  //     defs.push("  end");
  //   }
  // } else {
  //   defs = [...nodeLabels.entries()].map(([id, label]) => `  ${id}${label}`);
  // }

  const defs = [...nodeLabels.entries()].map(
    ([id, shapeLabel]) => `  ${id}${shapeLabel}`
  );

  const mermaidCode = `graph TD\n${defs.join("\n")}\n${[...edges].join(
    "\n"
  )}\n${classDefs.join("\n")}\n${styleBlock}`;

  const old = document.getElementById("mermaid-container");
  const newDiv = document.createElement("div");
  newDiv.id = "mermaid-container";
  newDiv.className = "mermaid";
  newDiv.style.whiteSpace = "pre-line";
  newDiv.textContent = mermaidCode;

  old.replaceWith(newDiv);
  window.mermaid.run();
}

// 初始化折叠节点记录; 已弃用
let collapsedNodeIds = new Set(
  JSON.parse(localStorage.getItem("collapsedNodes") || "[]")
);

// 渲染任务结构图; 已弃用
function renderGraph(graphs) {
  const graphContainer = document.getElementById("task-graph");
  graphContainer.innerHTML = "";

  function buildGraphHTML(node, path = "") {
    const nodeId = path ? `${path}/${node.stage_name}` : node.stage_name;
    let html = "<li>";

    // 节点展示内容
    html += `<div class="graph-node collapsible" data-id="${nodeId}" onclick="toggleNode(this)">`;

    if (node.next_stages && node.next_stages.length > 0) {
      html += `<span class="collapse-icon">${
        collapsedNodeIds.has(nodeId) ? "+" : "-"
      }</span>`;
    }

    html += `<span class="stage-name">${node.stage_name}</span>`;
    html += `<span class="stage-mode">(stage_mode: ${node.stage_mode})</span>`;
    html += `<span class="stage-func">func: ${node.func_name}</span>`;

    if (node.visited) {
      html += `<span class="visited-mark">visited</span>`;
    }

    html += "</div>";

    // 子节点递归渲染
    if (node.next_stages && node.next_stages.length > 0) {
      const isCollapsed = collapsedNodeIds.has(nodeId);
      html += `<ul ${isCollapsed ? 'class="hidden"' : ""}>`;
      node.next_stages.forEach((childNode) => {
        html += buildGraphHTML(childNode, nodeId);
      });
      html += "</ul>";
    }

    html += "</li>";
    return html;
  }

  // 多棵图处理
  const graphHTML = graphs
    .map((graph, index) => {
      return `${buildGraphHTML(graph, `root${index}`)}`;
    })
    .join("");

  graphContainer.innerHTML = graphHTML;
}

// 折叠状态控制; 已弃用
function toggleNode(element) {
  const childList = element.nextElementSibling;
  const nodeId = element.dataset.id;
  if (!nodeId || !childList || childList.tagName !== "UL") return;

  const isNowHidden = childList.classList.toggle("hidden");
  const icon = element.querySelector(".collapse-icon");
  if (icon) {
    icon.textContent = isNowHidden ? "+" : "-";
  }

  if (isNowHidden) {
    collapsedNodeIds.add(nodeId);
  } else {
    collapsedNodeIds.delete(nodeId);
  }
  localStorage.setItem("collapsedNodes", JSON.stringify([...collapsedNodeIds]));
}

