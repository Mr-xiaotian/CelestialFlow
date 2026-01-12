let structureData = [];
let previousStructureDataJSON = "";

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
    case "circle": // Circle nodes
      return `((${label}))`;

    case "round": // Rounded box
      return `(${label})`;

    case "rhombus": // Diamond (decision)
      return `{{${label}}}`;

    case "subgraph": // Subroutine / Module block
      return `[[${label}]]`;

    case "parallelogram": // IO style block
      return `[/ ${label} /]`.replace(/\s+/g, "");

    case "db": // Database cylinder
      return `[( ${label} )]`;

    case "cloud":
      return `(${label}):::cloud`; // requires styling externally

    case "hex":
      return `{{{${label}}}}`; // triple braces style

    case "arrow": // non-standard, custom arrow-like node
      return `>${label}]`;

    default: // Default rectangular box
      return `[${label}]`;
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

  function walk(node) {
    const id = getNodeId(node);
    const label = `${node.stage_name}`;
    const tag = `${node.stage_name}[${node.func_name}]`;
    tagToId[tag] = id; // 保存 tag 到 ID 的映射

    let shape = "box";
    if (node.func_name === "_split") shape = "subgraph";
    else if (node.func_name === "_route") shape = "rhombus";
    else if (node.func_name === "_sink") shape = "parallelogram";
    else if (node.func_name === "_source") shape = "parallelogram";
    else if (node.func_name === "_ack") shape = "parallelogram";

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
      const addNum = statusInfo?.add_tasks_successed || 0;
      const edgeLabel = addNum > 0 ? `|+${addNum}|` : "";

      edges.add(`  ${id} -->${""} ${toId}`);
      walk(child);
    }
  }

  structureData.forEach((graph) => walk(graph));

  // let defs = [];

  // if (topologyData.schedule_mode=== "staged") {
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
