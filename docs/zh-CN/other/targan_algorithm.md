# **Tarjan 算法** 

用于在 $O(V+E)$ 时间内找出有向图的**所有强连通分量（SCC）**。这是图论中最精妙的算法之一，核心只有三个东西：**DFS 时间戳**、**lowlink 值**、**维护栈**。

---

## 1. 什么是强连通分量（SCC）？

**强连通**：节点 $u$ 和 $v$ 互相可达（$u \to v$ 且 $v \to u$）。

**强连通分量**：一个极大的子图，其中任意两点都强连通。换句话说，SCC 内部的节点能互相串门，但跟外部是"单向墙"——你可以从 SCC 出去，或者从外面进来，但出去了就回不来了（除非在另一个 SCC 之间）。

**关键定理**：把每个 SCC 缩成一个点，得到的**凝聚图（Condensation Graph）一定是有向无环图（DAG）**。

---

## 2. Tarjan 算法的核心思想

Tarjan 在 DFS 的过程中做三件事：

| 机制 | 作用 |
|------|------|
| **`indices[v]`（dfn）** | 节点 $v$ 被 DFS 首次访问的**时间戳**（递增整数） |
| **`lowlink[v]`** | 从 $v$ 出发，通过**树边 + 回边 + 指向栈中节点的横叉边**，能到达的最小时间戳 |
| **栈 `stack`** | 维护当前 DFS 路径上**尚未确定归属 SCC** 的节点 |

### 核心判定条件

```
if lowlink[v] == indices[v]:
    v 是一个 SCC 的"根"
    从栈顶不断弹出，直到 v 为止，这些节点构成一个 SCC
```

**为什么？** `lowlink[v]` 表示 $v$ 能"够到"的最老祖先。如果它只能够到自己（`lowlink[v] == indices[v]`），说明以 $v$ 为根的子树中，没有任何节点能跳出 $v$ 的子树回到更早的祖先。因此 $v$ 子树中所有还在栈里的节点，和 $v$ 一起形成一个封闭的 SCC。

---

## 3. 逐行拆解代码

```python
def tarjan_scc(graph: OrderGraph) -> list[list[str]]:
    out = graph._out
    index = 0                    # 全局时间戳计数器
    stack: list[str] = []        # 维护当前"活跃"节点
    on_stack: set[str] = set()   # 快速判断某节点是否在栈中
    indices: dict[str, int] = {} # 记录每个节点的发现时间戳
    lowlink: dict[str, int] = {} # 记录每个节点能回溯到的最小时间戳
    sccs: list[list[str]] = []   # 结果：所有 SCC 列表
```

### 内层函数 `strongconnect(v)`

```python
    def strongconnect(v: str) -> None:
        nonlocal index
        
        # ① 初始化：给 v 打上时间戳，lowlink 先等于自己
        indices[v] = lowlink[v] = index
        index += 1
        stack.append(v)
        on_stack.add(v)
```

**第一步**：节点 $v$ 被发现。`indices[v]` 和 `lowlink[v]` 初始都等于当前时间戳。$v$ 入栈，表示它"暂时还没找到组织"。

```python
        # ② 遍历所有出边 v → w
        for w in out.get(v, []):
            
            if w not in indices:
                # 情况 A：w 未被访问过 → 树边，继续 DFS
                strongconnect(w)
                # 回溯后，w 的 lowlink 已经算好，用它来更新 v
                lowlink[v] = min(lowlink[v], lowlink[w])
            
            elif w in on_stack:
                # 情况 B：w 在栈中 → 回边或指向同 SCC 的横叉边
                # w 的时间戳就是它能代表的最老祖先
                lowlink[v] = min(lowlink[v], indices[w])
            
            # 情况 C（隐式 else）：w 已访问但不在栈中
            # 说明 w 属于一个已经确定的 SCC，对 v 无影响，直接忽略
```

**三种边类型的处理**：

| 情况 | 条件 | 含义 | 操作 |
|------|------|------|------|
| **A** | `w not in indices` | 树边（Tree Edge），$w$ 是 $v$ 的子节点 | 递归 DFS，回溯后用 `lowlink[w]` 更新 `lowlink[v]` |
| **B** | `w in on_stack` | 回边（Back Edge），$w$ 是 $v$ 的祖先或在同一 SCC 中 | 用 `indices[w]` 更新 `lowlink[v]`，表示 $v$ 能回到 $w$ |
| **C** | `w in indices` 且 `w not in on_stack` | 横叉边/前向边，指向**已完成的 SCC** | 忽略，因为那个 SCC 已经封闭，$v$ 无法通过它形成新的强连通 |

```python
        # ③ 判定：v 是不是某个 SCC 的根？
        if lowlink[v] == indices[v]:
            scc = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                scc.append(w)
                if w == v:
                    break
            sccs.append(scc)
```

**第三步**：DFS 完 $v$ 的所有出边后，如果 `lowlink[v] == indices[v]`，说明 $v$ 子树中没有任何节点能跳出到 $v$ 之前。此时栈中从栈顶到 $v$ 的所有节点，恰好构成一个完整的 SCC，把它们全部弹出。

### 外层循环

```python
    for v in graph._nodes:
        if v not in indices:
            strongconnect(v)
    
    return sccs
```

图可能不连通，所以需要遍历所有节点，对未访问的启动 DFS。

---

## 4. 完整例子走一遍

假设图结构：

```
a → b → c
↑       ↓
└───────┘      (a,b,c 形成环: SCC0)

c → d → e
        ↑
        └──── f  (e,f 形成环: SCC1)
```

邻接表：
- `a: [b]`
- `b: [c]`
- `c: [a, d]`
- `d: [e]`
- `e: [f]`
- `f: [e]`

### 执行过程

**访问 a：**
- `indices[a]=0, lowlink[a]=0`, 栈 `[a]`

**a→b：**
- `b` 未访问，递归。
- `indices[b]=1, lowlink[b]=1`, 栈 `[a, b]`

**b→c：**
- `c` 未访问，递归。
- `indices[c]=2, lowlink[c]=2`, 栈 `[a, b, c]`

**c→a：**
- `a` 已访问且 `a in on_stack`（情况 B）
- `lowlink[c] = min(2, 0) = 0`

**c→d：**
- `d` 未访问，递归。
- `indices[d]=3, lowlink[d]=3`, 栈 `[a, b, c, d]`

**d→e：**
- `e` 未访问，递归。
- `indices[e]=4, lowlink[e]=4`, 栈 `[a, b, c, d, e]`

**e→f：**
- `f` 未访问，递归。
- `indices[f]=5, lowlink[f]=5`, 栈 `[a, b, c, d, e, f]`

**f→e：**
- `e` 已访问且 `e in on_stack`（情况 B）
- `lowlink[f] = min(5, 4) = 4`

**f 的 DFS 结束：**
- `lowlink[f]=4 != indices[f]=5`，不弹出。返回。
- 更新 `e`：`lowlink[e] = min(4, 4) = 4`

**e 的 DFS 结束：**
- `lowlink[e]=4 != indices[e]=4`？**等等，等于！**
- 是的，`lowlink[e] == indices[e] == 4`
- **弹出 SCC：** 从栈顶弹出 `f`，然后 `e`。得到 `['f', 'e']`（顺序是弹出顺序，倒过来就是 `[e, f]`）
- 栈变为 `[a, b, c, d]`
- `sccs = [['f', 'e']]`（注意这个 SCC 是汇点 SCC，先被找到）

**回到 d：**
- 更新 `lowlink[d] = min(3, 4) = 3`

**d 的 DFS 结束：**
- `lowlink[d]=3 == indices[d]=3`
- **弹出 SCC：** 弹出 `d`。得到 `['d']`
- 栈变为 `[a, b, c]`
- `sccs = [['f', 'e'], ['d']]`

**回到 c：**
- 更新 `lowlink[c] = min(0, 3) = 0`

**c 的 DFS 结束：**
- `lowlink[c]=0 != indices[c]=2`，不弹出。

**回到 b：**
- 更新 `lowlink[b] = min(1, 0) = 0`

**b 的 DFS 结束：**
- `lowlink[b]=0 != indices[b]=1`，不弹出。

**回到 a：**
- 更新 `lowlink[a] = min(0, 0) = 0`

**a 的 DFS 结束：**
- `lowlink[a]=0 == indices[a]=0`
- **弹出 SCC：** 依次弹出 `c, b, a`。得到 `['c', 'b', 'a']`
- 栈空。
- `sccs = [['f', 'e'], ['d'], ['c', 'b', 'a']]`

### 最终结果

```python
[['f', 'e'], ['d'], ['c', 'b', 'a']]
```

**注意顺序**：这是**逆拓扑序**——**汇点 SCC 先被输出**，**源点 SCC 后被输出**。

对应凝聚图：
```
SCC(a,b,c) → SCC(d) → SCC(e,f)
```

Tarjan 输出顺序：`[SCC(e,f), SCC(d), SCC(a,b,c)]`，恰好是拓扑排序的**倒序**。

---

## 5. 为什么返回顺序是"逆拓扑序"？

Tarjan 算法中，一个 SCC 只有在它的**所有出边都 DFS 完毕**后才会被弹出。也就是说：

- 如果 SCC A 有边指向 SCC B，那么 DFS 会先深入 B，B 先被弹出，A 后被弹出。
- 因此先弹出的 SCC 在凝聚图中是"下游"（汇点方向），后弹出的是"上游"（源点方向）。

这正是凝聚图拓扑排序的**逆序**。这个性质非常有用——我们后续找 `source_sccs` 时，只需要在最后几个 SCC 里找入度为 0 的即可。

---

## 6. 复杂度分析

- **时间**：$O(V + E)$。每个节点访问一次，每条边检查一次，栈操作均摊 $O(1)$。
- **空间**：$O(V)$。栈、时间戳数组、递归栈深度最多为 $V$。

---

## 7. 常见误区

| 误区 | 澄清 |
|------|------|
| "为什么情况 C（已访问但不在栈中）要忽略？" | 因为 $w$ 已经属于一个确定的 SCC，且那个 SCC 在凝聚图中位于 $v$ 的下游。$v$ 无法通过 $w$ 回到更早的祖先，所以不影响 `lowlink`。 |
| "弹出的 SCC 内部顺序有意义吗？" | 没有。`['c', 'b', 'a']` 只是弹出顺序，不代表拓扑关系。SCC 内部是互相可达的。 |
| "lowlink 为什么用 `indices[w]` 而不是 `lowlink[w]` 更新？" | 在情况 B（回边）中，$w$ 还在栈中，说明 $w$ 和 $v$ 属于同一个 DFS 树中的未封闭区域。`indices[w]` 就是 $w$ 作为祖先的"高度"，直接用它更新即可。 |

---

## 总结

Tarjan 算法的精髓可以概括为一句话：

> **用 DFS 时间戳给节点编号，用 lowlink 追踪能回溯到的最老祖先，当某个节点发现自己只能回溯到自己时，它就是一坨强连通分量的"根"，把栈里这坨全部倒出来，就是一个 SCC。**

配合 Kahn 算法的 `is_dag`，两者形成了完美的互补：Tarjan 负责**分解环**，Kahn 负责**验证无环**。