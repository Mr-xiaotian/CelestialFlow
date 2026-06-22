# funnel 测试包

> 📅 最后更新日期: 2026/06/05

## 作用
`tests/funnel/` 覆盖基础漏斗组件的线程生命周期与队列传输语义，主要验证 `BaseInlet` 和 `BaseSpout` 的最小行为约束。

## 包含的测试文件
- `test_inlet.py`: 验证 inlet 通过 `_funnel()` 把记录写入目标队列。
- `test_spout.py`: 验证 spout 启停钩子、终止信号处理和抽象方法约束。

## 运行方式

```bash
pytest tests/funnel -v
pytest tests/funnel -k "inlet or spout" -v
```
