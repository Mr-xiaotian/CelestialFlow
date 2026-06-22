# **Tarjan's Algorithm**

Finds all **strongly connected components (SCCs)** of a directed graph in $O(V+E)$ time. It is one of the most elegant algorithms in graph theory; its core consists of only three things: **DFS discovery timestamp**, **lowlink value**, and **maintaining a stack**.

---

## 1. What is a Strongly Connected Component (SCC)?

**Strongly connected**: Nodes $u$ and $v$ are mutually reachable ($u \to v$ and $v \to u$).

**Strongly connected component**: A maximal subgraph in which any two vertices are strongly connected. In other words, nodes inside an SCC can visit each other freely, but to the outside they form a "one-way wall"—you can leave the SCC, or enter it from outside, but once you leave you cannot return (unless through another SCC).

**Key theorem**: If every SCC is collapsed into a single node, the resulting **condensation graph is always a directed acyclic graph (DAG)**.

---

## 2. Core idea of Tarjan's algorithm

During DFS, Tarjan does three things:

| Mechanism | Role |
|------|------|
| **`indices[v]` (dfn)** | The **discovery timestamp** (an increasing integer) when node $v$ is first visited by DFS |
| **`lowlink[v]`** | The smallest timestamp reachable from $v$ via **tree edges + back edges + cross edges pointing to nodes still on the stack** |
| **Stack `stack`** | Maintains nodes on the current DFS path whose SCC membership has **not yet been determined** |

### Core decision condition

```
if lowlink[v] == indices[v]:
    v is the "root" of an SCC
    Keep popping from the top of the stack until v is popped; these nodes form one SCC
```

**Why?** `lowlink[v]` represents the oldest ancestor that $v$ can "reach". If it can only reach itself (`lowlink[v] == indices[v]`), then no node in the subtree rooted at $v$ can jump out of $v$'s subtree back to an earlier ancestor. Therefore, all nodes still on the stack in $v$'s subtree, together with $v$, form a closed SCC.

---

## 3. Code walkthrough

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

### Inner function `strongconnect(v)`

```python
    def strongconnect(v: str) -> None:
        nonlocal index
        
        # ① 初始化：给 v 打上时间戳，lowlink 先等于自己
        indices[v] = lowlink[v] = index
        index += 1
        stack.append(v)
        on_stack.add(v)
```

**Step 1**: Node $v$ is discovered. `indices[v]` and `lowlink[v]` are initially set to the current timestamp. $v$ is pushed onto the stack, indicating it has "not yet found its organization".

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

**Handling of the three edge types**:

| Case | Condition | Meaning | Action |
|------|------|------|------|
| **A** | `w not in indices` | Tree edge: $w$ is a child of $v$ | Recursively DFS, then update `lowlink[v]` with `lowlink[w]` after backtracking |
| **B** | `w in on_stack` | Back edge: $w$ is an ancestor of $v$ or in the same SCC | Update `lowlink[v]` with `indices[w]`, indicating $v$ can return to $w$ |
| **C** | `w in indices` and `w not in on_stack` | Cross edge / forward edge pointing to a **completed SCC** | Ignore, because that SCC is already closed and $v$ cannot form a new strong connection through it |

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

**Step 3**: After DFS finishes all outgoing edges of $v$, if `lowlink[v] == indices[v]`, it means no node in $v$'s subtree can jump out to a node before $v$. At this point, all nodes from the top of the stack down to $v$ exactly form one complete SCC; pop them all.

### Outer loop

```python
    for v in graph._nodes:
        if v not in indices:
            strongconnect(v)
    
    return sccs
```

The graph may be disconnected, so all nodes must be traversed and DFS started from any unvisited node.

---

## 4. Full example walkthrough

Assume the graph structure:

```
a → b → c
↑       ↓
└───────┘      (a,b,c form a cycle: SCC0)

c → d → e
        ↑
        └──── f  (e,f form a cycle: SCC1)
```

Adjacency list:
- `a: [b]`
- `b: [c]`
- `c: [a, d]`
- `d: [e]`
- `e: [f]`
- `f: [e]`

### Execution process

**Visit a:**
- `indices[a]=0, lowlink[a]=0`, stack `[a]`

**a→b:**
- `b` unvisited, recurse.
- `indices[b]=1, lowlink[b]=1`, stack `[a, b]`

**b→c:**
- `c` unvisited, recurse.
- `indices[c]=2, lowlink[c]=2`, stack `[a, b, c]`

**c→a:**
- `a` visited and `a in on_stack` (case B)
- `lowlink[c] = min(2, 0) = 0`

**c→d:**
- `d` unvisited, recurse.
- `indices[d]=3, lowlink[d]=3`, stack `[a, b, c, d]`

**d→e:**
- `e` unvisited, recurse.
- `indices[e]=4, lowlink[e]=4`, stack `[a, b, c, d, e]`

**e→f:**
- `f` unvisited, recurse.
- `indices[f]=5, lowlink[f]=5`, stack `[a, b, c, d, e, f]`

**f→e:**
- `e` visited and `e in on_stack` (case B)
- `lowlink[f] = min(5, 4) = 4`

**DFS of f ends:**
- `lowlink[f]=4 != indices[f]=5`, do not pop. Return.
- Update `e`: `lowlink[e] = min(4, 4) = 4`

**DFS of e ends:**
- `lowlink[e]=4 != indices[e]=4`? **Wait, it is equal!**
- Yes, `lowlink[e] == indices[e] == 4`
- **Pop SCC:** pop `f`, then `e` from the top of the stack. Result `['f', 'e']` (pop order; reversed it is `[e, f]`)
- Stack becomes `[a, b, c, d]`
- `sccs = [['f', 'e']]` (note this SCC is a sink SCC, found first)

**Back to d:**
- Update `lowlink[d] = min(3, 4) = 3`

**DFS of d ends:**
- `lowlink[d]=3 == indices[d]=3`
- **Pop SCC:** pop `d`. Result `['d']`
- Stack becomes `[a, b, c]`
- `sccs = [['f', 'e'], ['d']]`

**Back to c:**
- Update `lowlink[c] = min(0, 3) = 0`

**DFS of c ends:**
- `lowlink[c]=0 != indices[c]=2`, do not pop.

**Back to b:**
- Update `lowlink[b] = min(1, 0) = 0`

**DFS of b ends:**
- `lowlink[b]=0 != indices[b]=1`, do not pop.

**Back to a:**
- Update `lowlink[a] = min(0, 0) = 0`

**DFS of a ends:**
- `lowlink[a]=0 == indices[a]=0`
- **Pop SCC:** pop `c, b, a` in turn. Result `['c', 'b', 'a']`
- Stack empty.
- `sccs = [['f', 'e'], ['d'], ['c', 'b', 'a']]`

### Final result

```python
[['f', 'e'], ['d'], ['c', 'b', 'a']]
```

**Note the order**: this is **reverse topological order**—**sink SCCs are output first**, **source SCCs are output last**.

Corresponding condensation graph:
```
SCC(a,b,c) → SCC(d) → SCC(e,f)
```

Tarjan output order: `[SCC(e,f), SCC(d), SCC(a,b,c)]`, exactly the **reverse** of the topological order.

---

## 5. Why is the output order "reverse topological order"?

In Tarjan's algorithm, an SCC is popped only after **all its outgoing edges have been fully DFS-traversed**. That is:

- If SCC A has an edge to SCC B, DFS will first go deep into B, B is popped first, and A is popped later.
- Therefore, SCCs popped earlier are "downstream" (toward sinks) in the condensation graph, and those popped later are "upstream" (toward sources).

This is exactly the **reverse** of the condensation graph's topological order. This property is very useful—when looking for `source_sccs` later, we only need to find those with in-degree 0 among the last few SCCs.

---

## 6. Complexity analysis

- **Time**: $O(V + E)$. Each node is visited once, each edge is checked once, and stack operations are amortized $O(1)$.
- **Space**: $O(V)$. The stack, timestamp arrays, and recursion depth are at most $V$.

---

## 7. Common misconceptions

| Misconception | Clarification |
|------|------|
| "Why ignore case C (visited but not on stack)?" | Because $w$ already belongs to a determined SCC, and that SCC lies downstream of $v$ in the condensation graph. $w$ cannot return to an earlier ancestor through $w$, so it does not affect `lowlink`. |
| "Does the internal order of a popped SCC matter?" | No. `['c', 'b', 'a']` is just the pop order and does not represent topological order. Inside an SCC all nodes are mutually reachable. |
| "Why update `lowlink` with `indices[w]` instead of `lowlink[w]` in case B?" | In case B (back edge), $w$ is still on the stack, indicating $w$ and $v$ are in the same unclosed region of the DFS tree. `indices[w]` is the "height" of $w$ as an ancestor; using it directly to update is sufficient. |

---

## Summary

The essence of Tarjan's algorithm can be summarized in one sentence:

> **Use DFS timestamps to number nodes, use lowlink to track the oldest ancestor they can reach, and when a node finds it can only reach itself, it is the "root" of a blob of strongly connected nodes—dump that blob out of the stack, and it is one SCC.**

Together with Kahn's `is_dag`, they form a perfect complement: Tarjan is responsible for **decomposing cycles**, and Kahn is responsible for **verifying acyclicity**.
