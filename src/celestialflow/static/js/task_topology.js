let topologyData = [];
let previousTopologyDataJSON = "";

async function loadTopology() {
  try {
    const res = await fetch("/api/get_topology");
    topologyData = await res.json();
  } catch (e) {
    console.error("拓扑加载失败", e);
  }
}

function renderTopologyInfo() {
  const container = document.getElementById("topology-info");
  if (!container) return;

  if (!topologyData || Object.keys(topologyData).length === 0) {
    container.innerHTML = `<div class="placeholder">暂无拓扑信息</div>`;
    return;
  }

  const {
    isDAG,
    layout_mode,
    class_name,
    layers_dict = {},
  } = topologyData;

  const layerCount = Object.keys(layers_dict).length;

  container.innerHTML = `
    <div class="topology-row">
      <span class="label">结构类型</span>
      <span class="value">${class_name}</span>
    </div>

    <div class="topology-row">
      <span class="label">是否 DAG</span>
      <span class="value ${isDAG ? "ok" : "warn"}">
        ${isDAG ? "是（无环）" : "否（存在环）"}
      </span>
    </div>

    <div class="topology-row">
      <span class="label">调度模式</span>
      <span class="value">${layout_mode}</span>
    </div>

    <div class="topology-row">
      <span class="label">层级数量</span>
      <span class="value">${layerCount}</span>
    </div>
  `;
}
