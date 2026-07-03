/**
 * 卡片布局编辑器
 * 悬浮窗口中用拖拽方式管理仪表盘左中右三栏的卡片排列
 */

const DEFAULT_LAYOUT: DashboardLayout = {
  left: ["mermaid", "analysis"],
  middle: ["status"],
  right: ["progress", "error-types", "summary"],
}; // 默认三栏布局，用于首次启动和重置

let originalLayout: DashboardLayout = {
  left: [],
  middle: [],
  right: [],
}; // 打开编辑器时的布局快照，用于取消时恢复

const LAYOUT_ZONE_IDS = [
  "layout-dropzone-left",
  "layout-dropzone-middle",
  "layout-dropzone-right",
  "layout-dropzone-unused",
] as const; // 布局编辑器内支持互拖的全部区域 ID

let sortableInstances: Partial<Record<(typeof LAYOUT_ZONE_IDS)[number], SortableInstance>> = {};
// 缓存当前拖拽区实例，避免反复打开编辑器时重复创建监听器。

/** 创建一张可拖拽卡片 */
function renderCard(cardId: string): HTMLElement {
  const name = t(CARD_META[cardId] ?? cardId); // 卡片显示名称，优先使用国际化标题
  const el = document.createElement("div"); // 可拖拽卡片 DOM
  el.className = "layout-card";
  el.dataset.cardId = cardId;
  el.innerHTML = `
    <span class="layout-card-name">${name}</span>
    <span class="layout-card-handle" aria-hidden="true">⠿</span>`;
  return el;
}

/** 打开布局编辑器，读取当前配置并渲染 */
function openLayoutEditor(): void {
  const overlay = document.getElementById("layout-editor-overlay")!; // 布局编辑器遮罩层
  overlay.classList.remove("hidden");

  const layout = webConfig.dashboard.layout; // 当前生效布局
  originalLayout = {
    left: [...(layout.left ?? [])],
    middle: [...(layout.middle ?? [])],
    right: [...(layout.right ?? [])],
  };

  const usedIds = new Set([
    ...(layout.left ?? []),
    ...(layout.middle ?? []),
    ...(layout.right ?? []),
  ]); // 当前已经被占用的卡片 ID

  // 渲染三栏
  for (const col of ["left", "middle", "right"] as DashboardColumnKey[]) {
    const zone = document.getElementById(`layout-dropzone-${col}`)!; // 当前栏位的拖放区域
    zone.innerHTML = "";
    for (const cardId of layout[col] ?? []) {
      zone.appendChild(renderCard(cardId));
    }
  }

  // 渲染未使用池
  const unusedZone = document.getElementById("layout-dropzone-unused")!; // 未使用卡片池
  unusedZone.innerHTML = "";
  for (const cardId of ALL_CARD_IDS) {
    if (!usedIds.has(cardId)) {
      unusedZone.appendChild(renderCard(cardId));
    }
  }

  initSortable();
}

/** 关闭编辑器 */
function closeLayoutEditor(restore: boolean = true): void {
  const overlay = document.getElementById("layout-editor-overlay")!; // 布局编辑器遮罩层
  overlay.classList.add("hidden");
  destroySortableInstances();
  if (restore) {
    // 关闭且需要恢复时，回滚到打开编辑器时的布局快照。
    webConfig.dashboard.layout = {
      left: [...originalLayout.left],
      middle: [...originalLayout.middle],
      right: [...originalLayout.right],
    };
    applyConfig();
  }
}

/** 初始化 SortableJS 拖拽（三栏 + 未使用池互拖） */
function initSortable(): void {
  destroySortableInstances();

  for (const id of LAYOUT_ZONE_IDS) {
    const zone = document.getElementById(id);
    if (!zone) continue;
    // 每个区域都加入同一 group，这样卡片可以跨栏位拖拽。
    sortableInstances[id] = Sortable.create(zone, {
      group: "dashboard-layout",
      animation: 150,
      ghostClass: "dragging",
      dragClass: "dragging",
    });
  }
}

/**
 * 销毁当前布局编辑器挂载的全部 Sortable 实例。
 * 在重绘拖拽区之前先清理旧实例，避免重复监听和实例泄漏。
 *
 * @returns {void}
 */
function destroySortableInstances(): void {
  for (const id of LAYOUT_ZONE_IDS) {
    sortableInstances[id]?.destroy();
  }
  sortableInstances = {};
}

/** 拖拽结束后将三栏卡片顺序写回 webConfig */
function syncLayout(): void {
  /**
   * 读取某一栏位中的全部卡片顺序。
   * @param {DashboardColumnKey} col - 栏位 key
   * @returns {string[]} 栏位中的卡片 ID 顺序
   */
  const cards = (col: DashboardColumnKey): string[] => {
    const zone = document.getElementById(`layout-dropzone-${col}`)!; // 对应栏位的拖放区域
    return Array.from(zone.querySelectorAll<HTMLElement>(".layout-card")).map(
      (c) => c.dataset.cardId!,
    );
  };
  webConfig.dashboard.layout = {
    left: cards("left"),
    middle: cards("middle"),
    right: cards("right"),
  };
}

/** 保存布局到 config.json 并刷新仪表盘 */
async function saveLayout(): Promise<void> {
  syncLayout();
  const saved = await saveWebConfig();
  if (saved) {
    applyConfig();
    closeLayoutEditor(false);
  } else {
    showSettingsSaveStatus("settings.saveFailed");
  }
}

/** 重置为默认布局（清空所有栏并重新渲染） */
function resetLayout(): void {
  // 先把运行时布局恢复成默认值。
  webConfig.dashboard.layout = {
    left: [...DEFAULT_LAYOUT.left],
    middle: [...DEFAULT_LAYOUT.middle],
    right: [...DEFAULT_LAYOUT.right],
  };

  const usedIds = new Set([
    ...DEFAULT_LAYOUT.left,
    ...DEFAULT_LAYOUT.middle,
    ...DEFAULT_LAYOUT.right,
  ]); // 默认布局中已经使用到的卡片 ID

  for (const col of ["left", "middle", "right"] as DashboardColumnKey[]) {
    const zone = document.getElementById(`layout-dropzone-${col}`)!; // 当前栏位拖放区域
    zone.innerHTML = "";
    for (const cardId of webConfig.dashboard.layout[col]) {
      zone.appendChild(renderCard(cardId));
    }
  }

  const unusedZone = document.getElementById("layout-dropzone-unused")!; // 未使用卡片池
  unusedZone.innerHTML = "";
  for (const cardId of ALL_CARD_IDS) {
    if (!usedIds.has(cardId)) {
      unusedZone.appendChild(renderCard(cardId));
    }
  }

  initSortable();
}

// ── 事件绑定 ──────────────────────────────────────────

// 页面初始化后绑定布局编辑器相关交互。
document.addEventListener("DOMContentLoaded", () => {
  // 点击设置项里的入口按钮时打开布局编辑弹层。
  document
    .getElementById("open-layout-editor")!
    .addEventListener("click", openLayoutEditor);

  // 点击右上角关闭按钮时关闭弹层并恢复未保存布局。
  document
    .getElementById("layout-editor-close")!
    .addEventListener("click", () => closeLayoutEditor());

  // 点击遮罩空白区域时关闭弹层，保留常见弹窗交互习惯。
  document
    .getElementById("layout-editor-overlay")!
    .addEventListener("click", (e) => {
      if ((e.target as HTMLElement).id === "layout-editor-overlay") {
        closeLayoutEditor();
      }
    });

  // 点击保存按钮时写回当前拖拽结果并持久化配置。
  document
    .getElementById("layout-save-btn")!
    .addEventListener("click", saveLayout);

  // 点击重置按钮时恢复默认卡片布局。
  document
    .getElementById("layout-reset-btn")!
    .addEventListener("click", resetLayout);
});
