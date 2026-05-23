---
name: "docs-zh-sync"
description: "Audits code in src/, bench/, tests/, and demo/, then updates matching docs/zh-CN markdown by mirrored relative paths. Invoke when code changes require Chinese docs sync."
---

# Docs Zh Sync

用于把代码与 `docs/zh-CN` 文档持续对齐的技能。

当用户提出以下需求时，立即调用本技能：

- 同步、补全、刷新中文文档
- 依据代码更新 `docs/zh-CN`
- 检查 `src/`、`bench/`、`tests/`、`demo/` 后批量修正文档
- 发现文档过期、缺页、路径不一致，要求按代码现状修复

## 目标

检查以下目录中的源码与示例：

- `src/`
- `bench/`
- `tests/`
- `demo/`

覆盖以下文件类型：

- `*.py`
- `*.ts`
- `*.html`
- `*.css`

然后把对应内容更新到 `docs/zh-CN/` 下相同语义、相同相对路径的文档中，文档文件统一为 `*.md`。

## 路径映射规则

默认使用“代码路径 -> 中文文档路径”的镜像规则。

### 根目录映射

- `src/celestialflow/...` -> `docs/zh-CN/src/...`
- `bench/...` -> `docs/zh-CN/bench/...`
- `tests/...` -> `docs/zh-CN/tests/...`
- `demo/...` -> `docs/zh-CN/demo/...`

### 后缀映射

- `foo.py` -> `foo.md`
- `foo.ts` -> `foo.md`
- `foo.html` -> `foo.md`
- `foo.css` -> `foo.md`
- `__init__.py` -> `__init__.md`

### 示例

- `src/celestialflow/runtime/util_errors.py` -> `docs/zh-CN/src/runtime/util_errors.md`
- `src/celestialflow/web/static/ts/main.ts` -> `docs/zh-CN/src/web/static/ts/main.md`
- `src/celestialflow/web/templates/index.html` -> `docs/zh-CN/src/web/templates/index.md`
- `src/celestialflow/web/static/css/dashboard.css` -> `docs/zh-CN/src/web/static/css/dashboard.md`
- `tests/runtime/test_queue.py` -> `docs/zh-CN/tests/runtime/test_queue.md`
- `demo/demo_graph.py` -> `docs/zh-CN/demo/demo_graph.md`

如果项目里已经存在旧版但不镜像的中文文档路径，优先以“镜像路径”作为目标；必要时说明发现了旧路径遗留问题。

## 分区执行策略

优先按区域拆分任务，并尽量使用 `subagent` 并行处理。推荐最少拆成以下 5 个区域：

1. `src/` 核心 Python 模块
2. `src/` Web 前端资源（`ts/html/css`）
3. `bench/`
4. `tests/`
5. `demo/`

如果代码量较大，可继续细分 `src/`：

- `src/celestialflow/runtime|graph|stage|funnel`
- `src/celestialflow/observability|persistence|utils`
- `src/celestialflow/web/static/ts|css|templates`

每个 `subagent` 负责：

- 扫描所属区域的代码文件
- 找到对应的 `docs/zh-CN` 目标文档
- 对照现有文档判断“更新 / 新建 / 保留”
- 只根据代码事实写文档，不凭空补设定
- 返回该区域的变更清单、风险点、缺失项

如果当前环境不支持真正的 `subagent`，则按同样的区域边界顺序串行执行，但在思考和输出中保持分区。

## 推荐工作流

1. 先列出本次需要覆盖的代码文件，按区域分组。
2. 对每个区域读取源码与现有中文文档。
3. 判断文档是否存在以下问题：
   - 路径不镜像
   - 接口签名过期
   - 类、函数、异常、配置项遗漏
   - 示例与当前代码不一致
   - 仍在描述已删除能力
4. 更新或创建对应的 `docs/zh-CN/**/*.md`。
   - 对于更新或者新创建的文档，确保 `最后更新日期` 为当前日期（YYYY/MM/DD）。
   - 对于没有修改的文档，保持 `最后更新日期` 不变。
5. 完成后给出区域级汇总：
   - 更新了哪些文档
   - 新建了哪些文档
   - 哪些旧文档路径可能需要后续迁移
   - 哪些代码仍缺少足够上下文，暂不应编造说明

## 文档写作规则

- 默认使用中文。
- 以代码为唯一事实来源，必要时结合同目录已有文档风格。
- 重点写“职责、结构、关键函数、关键类、数据流、异常、配置、注意事项”。
- 对 `tests/` 文档，重点说明测试覆盖目标、关键场景、断言意图，不要把测试逐行复述。
- 对 `bench/` 文档，重点说明 benchmark 比较对象、衡量指标、实验目的、结论边界。
- 对 `demo/` 文档，重点说明演示目的、运行方式、预期行为、依赖。
- 对 `ts/html/css` 文档，重点说明页面职责、模块交互、DOM/样式作用域、与后端接口或其他前端模块的关系。

## 文档质量要求

- 可以适当引用代码片段以避免单一文字模式，但不要整段照抄。
- 不要虚构未实现的功能。
- 不要仅把函数名罗列出来而没有解释。
- 不要遗漏最近的重构结果，尤其是重命名、异常类型变化、字段变化、状态键变化。
- 如果发现文档内容与代码冲突，按代码修正文档，并在最终总结里指出冲突点。
- 不要轻易删除原有内容：原文档中已有的信息允许修改、补充、重组，但除非该信息已被代码证实为完全错误或彻底废弃，否则不要删除。宁可保留旧信息并标注"已变更"或"待确认"，也不要让有价值的历史说明丢失。

## 文档表达形式

文档不仅是信息的载体，更是开发者阅读体验的一部分。应善用丰富的表达形式，使阅读文档成为乐趣：

- **Mermaid 图表**：鼓励使用 Mermaid 绘制流程图、时序图、类图、状态图等，直观展示模块关系、数据流向、生命周期。
  - 流程图 (`flowchart`)：展示处理步骤、分支逻辑
  - 时序图 (`sequenceDiagram`)：展示模块间调用顺序、消息传递
  - 类图 (`classDiagram`)：展示核心类关系、继承结构
  - 状态图 (`stateDiagram`)：展示状态机、生命周期
- **表格**：适合对比、配置项罗列、参数说明等结构化信息，比纯文字更清晰。
- **ASCII 图**：适合展示目录树、简单的架构拓扑、终端输出示例。
- **列表与层级**：合理使用有序/无序列表、嵌套层级，让信息层次分明。
- **代码块**：关键示例使用带语言标注的代码块，方便语法高亮。
- **引用块**：用 `>` 引用块突出重要提示、注意事项、设计决策背景。

原则：形式服务于内容。不要为了花哨而堆砌图表，但也不要让文档变成一堵文字墙。好的文档应该让读者愿意读、容易读、读完有收获。

## 建议文档骨架

可按文件类型灵活调整，但通常保持以下结构：

```md
# 文件或模块标题

> 最后更新日期: YYYY/MM/DD

## 作用

## 核心对象 / 核心函数

## 关键流程

## 重要细节

## 使用示例 / 测试重点 / 运行方式

## 注意事项
```

## 排除项

除非用户明确要求，否则通常不处理以下内容：

- `docs/en/`
- `docs/ja/`
- 生成产物，如 `src/celestialflow/web/static/js/*.js`
- 第三方依赖锁文件、图片、二进制资源

## 交付要求

完成后输出：

- 本次扫描的区域
- 更新或新建的文档路径
- 发现的旧文档路径或结构不一致问题
- 仍待人工确认的歧义点

如果只完成了部分区域，要明确列出已完成范围和剩余范围。
