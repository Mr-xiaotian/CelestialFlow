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