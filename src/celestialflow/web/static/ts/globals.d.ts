declare const Chart: any;
declare const Sortable: any;

interface Window {
  mermaid: any;
}

type Lang = "zh-CN" | "en" | "ja";
declare var currentLang: Lang;
declare function setLang(lang: Lang): void;
declare function t(key: string, ...args: string[]): string;
declare function applyI18nDOM(): void;
