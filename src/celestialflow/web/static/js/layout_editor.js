/**
 * 卡片布局编辑器
 * 悬浮窗口中用拖拽方式管理仪表盘左中右三栏的卡片排列
 */
const CARD_META = {
    mermaid: "结构图",
    analysis: "图分析",
    status: "节点状态",
    progress: "指标走向",
    summary: "总体摘要",
};
const ALL_CARD_IDS = Object.keys(CARD_META);
const DEFAULT_LAYOUT = {
    left: ["mermaid", "analysis"],
    middle: ["status"],
    right: ["progress", "summary"],
};
let originalLayout = {};
/** 创建一张可拖拽卡片 */
function renderCard(cardId) {
    const name = CARD_META[cardId] ?? cardId;
    const el = document.createElement("div");
    el.className = "layout-card";
    el.dataset.cardId = cardId;
    el.innerHTML = `
    <span class="layout-card-name">${name}</span>
    <span class="layout-card-handle" aria-hidden="true">⠿</span>`;
    return el;
}
/** 打开布局编辑器，读取当前配置并渲染 */
function openLayoutEditor() {
    const overlay = document.getElementById("layout-editor-overlay");
    overlay.classList.remove("hidden");
    const layout = webConfig.dashboard ?? DEFAULT_LAYOUT;
    originalLayout = {
        left: [...(layout.left ?? [])],
        middle: [...(layout.middle ?? [])],
        right: [...(layout.right ?? [])],
    };
    const usedIds = new Set([
        ...(layout.left ?? []),
        ...(layout.middle ?? []),
        ...(layout.right ?? []),
    ]);
    // 渲染三栏
    for (const col of ["left", "middle", "right"]) {
        const zone = document.getElementById(`layout-dropzone-${col}`);
        zone.innerHTML = "";
        for (const cardId of layout[col] ?? []) {
            zone.appendChild(renderCard(cardId));
        }
    }
    // 渲染未使用池
    const unusedZone = document.getElementById("layout-dropzone-unused");
    unusedZone.innerHTML = "";
    for (const cardId of ALL_CARD_IDS) {
        if (!usedIds.has(cardId)) {
            unusedZone.appendChild(renderCard(cardId));
        }
    }
    initSortable();
}
/** 关闭编辑器 */
function closeLayoutEditor(restore = true) {
    const overlay = document.getElementById("layout-editor-overlay");
    overlay.classList.add("hidden");
    if (restore) {
        webConfig.dashboard = {
            left: [...originalLayout.left],
            middle: [...originalLayout.middle],
            right: [...originalLayout.right],
        };
        applyConfig();
    }
}
/** 初始化 SortableJS 拖拽（三栏 + 未使用池互拖） */
function initSortable() {
    const zoneIds = [
        "layout-dropzone-left",
        "layout-dropzone-middle",
        "layout-dropzone-right",
        "layout-dropzone-unused",
    ];
    for (const id of zoneIds) {
        Sortable.create(document.getElementById(id), {
            group: "dashboard-layout",
            animation: 150,
            ghostClass: "dragging",
            dragClass: "dragging",
        });
    }
}
/** 拖拽结束后将三栏卡片顺序写回 webConfig */
function syncLayout() {
    const cards = (col) => {
        const zone = document.getElementById(`layout-dropzone-${col}`);
        return Array.from(zone.querySelectorAll(".layout-card")).map((c) => c.dataset.cardId);
    };
    webConfig.dashboard = {
        left: cards("left"),
        middle: cards("middle"),
        right: cards("right"),
    };
}
/** 保存布局到 config.json 并刷新仪表盘 */
async function saveLayout() {
    syncLayout();
    const saved = await saveWebConfig();
    if (saved) {
        applyConfig();
        closeLayoutEditor(false);
    }
    else {
        showSettingsSaveStatus("settings.saveFailed");
    }
}
/** 重置为默认布局（清空所有栏并重新渲染） */
function resetLayout() {
    webConfig.dashboard = {
        left: [...DEFAULT_LAYOUT.left],
        middle: [...DEFAULT_LAYOUT.middle],
        right: [...DEFAULT_LAYOUT.right],
    };
    const usedIds = new Set([
        ...DEFAULT_LAYOUT.left,
        ...DEFAULT_LAYOUT.middle,
        ...DEFAULT_LAYOUT.right,
    ]);
    for (const col of ["left", "middle", "right"]) {
        const zone = document.getElementById(`layout-dropzone-${col}`);
        zone.innerHTML = "";
        for (const cardId of webConfig.dashboard[col]) {
            zone.appendChild(renderCard(cardId));
        }
    }
    const unusedZone = document.getElementById("layout-dropzone-unused");
    unusedZone.innerHTML = "";
    for (const cardId of ALL_CARD_IDS) {
        if (!usedIds.has(cardId)) {
            unusedZone.appendChild(renderCard(cardId));
        }
    }
    initSortable();
}
// ── 事件绑定 ──────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    document
        .getElementById("open-layout-editor")
        .addEventListener("click", openLayoutEditor);
    document
        .getElementById("layout-editor-close")
        .addEventListener("click", () => closeLayoutEditor());
    document
        .getElementById("layout-editor-overlay")
        .addEventListener("click", (e) => {
        if (e.target.id === "layout-editor-overlay") {
            closeLayoutEditor();
        }
    });
    document
        .getElementById("layout-save-btn")
        .addEventListener("click", saveLayout);
    document
        .getElementById("layout-reset-btn")
        .addEventListener("click", resetLayout);
});
