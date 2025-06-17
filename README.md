# CelestialFlow

## Structure

- chain
- tree
- forest
- loop
- complete

## Log

- [2021] 建立一个支持多线程与单线程处理函数的类
- [2023] 在GPT4帮助下添加多进程与携程运行模式 
- [5/9/2024] 将原有的处理类抽象为节点, 添加TaskChain类, 可以线性连接多个节点, 并设定节点在Chain中的运行模式, 支持serial和process两种, 后者Chain所有节点同时运行
- [12/12/2024-12/16/2024] 在原有链式结构基础上允许节点有复数下级节点, 实现Tree结构; 将原有TaskChain改名为TaskTree
- [3/16/2025] 支持web端任务完成情况可视化
- [6/9/2025] 支持节点拥有复数上级节点, 脱离纯Tree结构, 为之后循环图做准备
- [6/11/2025] 自**CelestialVault**项目instances.inst_task迁入
- [6/12/2025] 支持循环图, 下级节点可指向上级节点
- [6/13/2025] 支持loop结构, 即节点可指向自己
- [6/14/2025] 支持forest结构, 即可有多个根节点
- [6/16/2025] 多轮评测后, 当前框架已支持完整有向图结构, 故将TaskTree改名为TaskGraph