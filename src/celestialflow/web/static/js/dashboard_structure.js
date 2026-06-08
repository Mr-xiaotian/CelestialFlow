"use strict";
/**
 * 任务图结构展示模块
 * 使用 Mermaid.js 将复杂的任务有向图转换为可视化的流程图，并根据节点状态实时着色
 */
// 全局状态
let structureData = {
    nodes: {},
    edges: {},
    source_nodes: [],
}; // 任务结构图数据（有向图）
let structureRev = -1; // 数据版本号，用于增量拉取
let structureRequestSeq = 0; // 请求序列号，防止旧结构响应覆盖新结果
/**
 * 异步加载最新的任务结构数据
 * 从后端 API 获取任务结构图数据并更新全局变量 structureData
 * @returns {Promise<boolean>} 当结构版本发生变化并成功更新时返回 `true`，否则返回 `false`。
 */
async function loadStructure() {
    try {
        const requestSeq = ++structureRequestSeq; // 为当前结构请求分配递增序号
        const res = await fetch(`/api/pull_structure?known_rev=${structureRev}`);
        const body = (await res.json());
        if (requestSeq !== structureRequestSeq)
            return false; // 丢弃已过时请求的返回结果
        if (body.data === null)
            return false;
        structureData = body.data;
        structureRev = body.rev;
        return true;
    }
    catch (e) {
        console.error("结构加载失败", e);
        return false;
    }
}
/**
 * 获取节点的唯一标识符 ID
 * @param {string} nodeName - 节点名称。
 * @returns {string} 替换非单词字符后的节点 ID
 */
function getNodeId(nodeName) {
    return nodeName.replace(/\W+/g, "_");
}
/**
 * 根据节点元信息推导 Mermaid 形状类型
 * @param {StructureNodeMeta} nodeMeta - 节点元信息
 * @returns {string} Mermaid 形状名称
 */
function getNodeShape(nodeMeta) {
    switch (nodeMeta.func_name) {
        case "_split":
            return "subgraph";
        case "_route":
            return "rhombus";
        case "_transport":
        case "_source":
        case "_ack":
            return "parallelogram";
        default:
            return "box";
    }
}
/**
 * 根据节点形状类型生成 Mermaid 语法的标签
 * @param {string} label - 节点显示的文本
 * @param {string} [shape="box"] - 形状类型，可选值包括 `box`、`circle`、`round`、`rhombus`、`subgraph`、`parallelogram`、`db`、`cloud`、`hex`、`arrow`。
 * @returns {string} 包含形状定义的 Mermaid 节点标签
 */
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
/**
 * 根据任务结构数据渲染 Mermaid 图表
 * 构建 Mermaid 流程图代码，根据节点状态应用样式，并更新 DOM
 * @param {Record<string, NodeStatus>} [statuses={}] - 当前节点状态映射，用于节点着色和边增量计算。
 * @returns {void}
 */
function renderMermaidStructure(statuses = {}) {
    const { nodes = {}, edges = {}, source_nodes = [] } = structureData || {}; // 当前结构图主数据
    const nodeNames = Object.keys(nodes); // 全量节点名，供空状态判断和遍历使用
    if (!nodeNames.length) {
        const old = document.getElementById("mermaid-container");
        if (!old)
            return;
        const newDiv = document.createElement("div");
        newDiv.id = "mermaid-container";
        newDiv.className = "empty-placeholder";
        newDiv.textContent = t("structure.noData");
        old.replaceWith(newDiv);
        return;
    }
    const mermaidEdges = new Set(); // 边定义去重集合
    const nodeLabels = new Map(); // Mermaid 节点标签缓存
    const classDefs = new Set(); // Mermaid class 样式绑定集合
    // 判断是否是暗黑主题
    const isDark = document.body.classList.contains("dark-theme");
    // 样式区块：根据主题切换
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
    const orderedNodeNames = [
        ...source_nodes.filter((name) => name in nodes),
        ...nodeNames.filter((name) => !source_nodes.includes(name)),
    ]; // 优先把源节点放前面，增强拓扑图可读性
    // 先生成节点定义和节点样式，再生成边，便于后续统一拼接 Mermaid 代码。
    for (const nodeName of orderedNodeNames) {
        const nodeMeta = nodes[nodeName];
        const id = getNodeId(nodeName);
        nodeLabels.set(id, getShapeWrappedLabel(nodeName, getNodeShape(nodeMeta)));
        const statusInfo = statuses[nodeName]; // 当前节点的运行态，用于上色
        let statusClass = "whiteNode"; // 默认样式为普通白色节点
        if (statusInfo) {
            if (statusInfo.status === 1)
                statusClass = "greenNode";
            else if (statusInfo.status === 2)
                statusClass = "greyNode";
        }
        classDefs.add(`  class ${id} ${statusClass};`);
    }
    // 再生成边定义，并按配置决定是否在边上显示本轮成功增量。
    for (const [fromName, toNames] of Object.entries(edges)) {
        if (!(fromName in nodes))
            continue;
        const fromId = getNodeId(fromName);
        const statusInfo = statuses[fromName];
        for (const toName of toNames || []) {
            if (!(toName in nodes))
                continue;
            const toId = getNodeId(toName);
            let edgeLabel = ""; // Mermaid 边标签，默认空字符串
            if (webConfig.dashboard.showStructureEdgeDelta) {
                const lastInfo = lastNodeStatuses[fromName] || {}; // 上一轮状态，用于计算增量
                const addNum = (statusInfo?.tasks_succeeded || 0) - (lastInfo?.tasks_succeeded || 0); // 本轮新增成功任务数
                edgeLabel = addNum > 0 ? `|+${addNum}|` : "";
            }
            mermaidEdges.add(`  ${fromId} -->${edgeLabel} ${toId}`);
        }
    }
    const defs = [...nodeLabels.entries()].map(([id, shapeLabel]) => `  ${id}${shapeLabel}`); // Mermaid 节点定义区块
    const mermaidCode = `graph TD\n${defs.join("\n")}\n${[...mermaidEdges].join("\n")}\n${[...classDefs].join("\n")}\n${styleBlock}`; // 最终 Mermaid 源码
    const old = document.getElementById("mermaid-container");
    if (!old)
        return;
    const newDiv = document.createElement("div"); // 新容器替换旧容器，避免 mermaid 对旧 DOM 状态残留
    newDiv.id = "mermaid-container";
    newDiv.className = "mermaid";
    newDiv.style.whiteSpace = "pre-line";
    newDiv.textContent = mermaidCode;
    old.replaceWith(newDiv);
    // Mermaid 会扫描新容器中的源码并完成 SVG 渲染。
    window.mermaid.run();
}
