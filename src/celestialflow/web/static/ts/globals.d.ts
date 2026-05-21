/**
 * 全局类型声明文件
 * 包含外部库（Chart.js, Sortable.js, Mermaid）的类型定义
 * 以及由其他脚本导出的全局变量和函数
 */

declare const Chart: any;
declare const Sortable: any;

interface Window {
  mermaid: any;
}

/** 支持的界面语言类型 */
type Lang = "zh-CN" | "en" | "ja";

/** 当前选中的语言标识 */
declare var currentLang: Lang;

/** 设置当前语言并更新 HTML 根节点 */
declare function setLang(lang: Lang): void;

/** 根据翻译键获取当前语言的文本 */
declare function t(key: string, ...args: string[]): string;

/** 将国际化属性应用到 DOM 元素 */
declare function applyI18nDOM(): void;
