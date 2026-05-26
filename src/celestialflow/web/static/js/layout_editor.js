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
const DEFAULT_LAYOUT = {
    left: ["mermaid", "analysis"],
    middle: ["status"],
    right: ["progress", "summary"],
};
let originalLayout = {};
/** 打开布局编辑器，读取当前配置并渲染 */
function openLayoutEditor() {
    const overlay = document.getElementById("layout-editor-overlay");
    overlay.classList.remove("hidden");
    originalLayout = {
        left: [...(webConfig.dashboard?.left ?? DEFAULT_LAYOUT.left)],
        middle: [...(webConfig.dashboard?.middle ?? DEFAULT_LAYOUT.middle)],
        right: [...(webConfig.dashboard?.right ?? DEFAULT_LAYOUT.right)],
    };
    renderLayoutColumns(originalLayout);
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
/** 根据布局数据渲染三栏的卡片列表 */
function renderLayoutColumns(layout) {
    for (const col of ["left", "middle", "right"]) {
        const zone = document.getElementById(`layout-dropzone-${col}`);
        zone.innerHTML = "";
        for (const cardId of layout[col] || []) {
            const name = CARD_META[cardId] ?? cardId;
            const el = document.createElement("div");
            el.className = "layout-card";
            el.dataset.cardId = cardId;
            el.innerHTML = `
        <span class="layout-card-name">${name}</span>
        <span class="layout-card-handle" aria-hidden="true">⠿</span>`;
            zone.appendChild(el);
        }
    }
}
/** 初始化 SortableJS 拖拽（三栏互拖） */
function initSortable() {
    const zones = [
        document.getElementById("layout-dropzone-left"),
        document.getElementById("layout-dropzone-middle"),
        document.getElementById("layout-dropzone-right"),
    ];
    for (const zone of zones) {
        Sortable.create(zone, {
            group: "dashboard-layout",
            animation: 150,
            ghostClass: "dragging",
            dragClass: "dragging",
            onEnd: () => syncLayout(),
        });
    }
}
/** 拖拽结束后将 dropzone 中的卡片顺序写回 webConfig */
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
/** 重置为默认布局 */
function resetLayout() {
    webConfig.dashboard = {
        left: [...DEFAULT_LAYOUT.left],
        middle: [...DEFAULT_LAYOUT.middle],
        right: [...DEFAULT_LAYOUT.right],
    };
    renderLayoutColumns(webConfig.dashboard);
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
