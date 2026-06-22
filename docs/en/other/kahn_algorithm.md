# **Kahn's Algorithm**

The core idea is:

> **Repeatedly peel off nodes whose in-degree is 0. If all nodes can eventually be removed, the graph is acyclic; otherwise, it must contain a cycle.**

---

## 1. Why are nodes with in-degree 0 always safe?

An in-degree of 0 means **no edges point to it**. In a directed graph, such a node cannot be part of any cycle (because a cycle requires every node to be pointed to by at least one edge).

So we can safely delete it (along with all edges it emits) from the graph without affecting whether the remaining graph contains a cycle.

---

## 2. Algorithm steps broken down

Take this code as an example:

```python
def is_dag(graph: OrderGraph) -> bool:
    deg = in_degree(graph)              # ① 计算所有节点入度
    stack = [n for n, d in deg.items() 
             if d == 0]                 # ② 收集所有入度为0的节点
    visited = 0                          # ③ 计数：已被剥离的节点数

    while stack:                         # ④ 不断处理入度为0的节点
        u = stack.pop()                  # ⑤ 取出一个节点
        visited += 1                     # ⑥ 计数+1

        for v in graph._out.get(u, []):  # ⑦ 遍历它的所有出边 u→v
            deg[v] -= 1                  # ⑧ 删除这条边：v的入度-1
            if deg[v] == 0:              # ⑨ 如果v的入度恰好变为0
                stack.append(v)          # ⑩ 说明v现在"安全"了，加入处理队列

    return visited == len(graph._nodes) # ⑪ 全部剥离完？是则DAG
```

### Line-by-line explanation

| Step | Action | Meaning |
|------|------|------|
| **①** | `deg = in_degree(graph)` | First compute how many edges point to each node. For example, if `a←b`, then `a`'s in-degree +1. |
| **②** | `stack = [nodes with in-degree 0]` | These nodes are the current "starting points" of the graph and cannot be part of a cycle. |
| **③** | `visited = 0` | Records how many nodes we have "peeled off". |
| **④~⑥** | `while stack: pop → visited += 1` | Each time, take a safe node out of the stack and mark it as removed. |
| **⑦~⑧** | `for v in out[u]: deg[v] -= 1` | **Key**: after node `u` is removed, all edges it emits also disappear. Edge disappearance means downstream node `v` loses one incoming edge, so `v`'s in-degree decreases by 1. |
| **⑨~⑩** | `if deg[v] == 0: stack.append(v)` | **Core**: when `v`'s last incoming edge is deleted, `v` becomes a new "starting point"; it can no longer belong to any cycle, so it can be safely added to the processing queue. |
| **⑪** | `visited == len(nodes)` | If all nodes are peeled off, the graph can be fully topologically sorted and is **acyclic**; if `visited < len(nodes)`, some nodes remain that cannot be removed—they point to each other and form a **cycle**. |

---

## 3. Intuitive example

Suppose the graph is as follows:

```
a → b → c
↑       ↓
└───────┘   (c points to a, forming a cycle)
```

**Initial in-degrees:**

| Node | In-degree | Source |
|------|------|------|
| a    | 1    | ← c |
| b    | 1    | ← a |
| c    | 1    | ← b |

**Execution process:**

1. Find nodes with in-degree 0: `[]` (none!)
2. `stack` is empty, the `while` loop ends immediately.
3. `visited = 0`, `len(nodes) = 3`.
4. `0 == 3`? **No** → `is_dag` returns `False`.

**Why?** Because a, b, and c all have in-degree 1; none is a starting point, and none can be deleted. They form a cycle.

---

Now suppose the graph is a DAG:

```
a → b → c
```

**Initial in-degrees:** a=0, b=1, c=1

**Round 1:** `stack = [a]`
- Pop `a`, `visited = 1`
- Delete `a→b`, `b`'s in-degree becomes 0, push onto stack
- `stack = [b]`

**Round 2:**
- Pop `b`, `visited = 2`
- Delete `b→c`, `c`'s in-degree becomes 0, push onto stack
- `stack = [c]`

**Round 3:**
- Pop `c`, `visited = 3`
- `c` has no outgoing edges, no further action

End: `visited == 3` → **it is a DAG**.

---

## 4. Why can nodes in a cycle never enter the stack?

Suppose node `x` belongs to some cycle. Every node in the cycle is pointed to by at least one other edge inside the cycle, so their in-degrees are at least 1 (just from within the cycle).

When you peel off nodes outside the cycle, you may reduce some in-degrees, but **edges inside the cycle are never deleted** (because nodes inside the cycle never enter the stack, are never deleted, and the edges they emit are never removed).

Therefore, the in-degree of nodes inside the cycle **can never drop to 0**; they remain stuck at `deg >= 1`, so `visited` cannot cover them.

---

## 5. Complexity

- **Time:** $O(V + E)$. Each node is pushed and popped at most once; each edge is "deleted" at most once (triggering one `deg[v] -= 1`).
- **Space:** $O(V)$. The size of the stack and the in-degree array.

---

## Summary

The essence of `is_dag()` is **simulating topological sorting**:

> If the sort can finish (all nodes are peeled off) = no cycle = DAG  
> If the sort cannot finish (a clump of nodes pointing to each other remains) = has cycle = not a DAG

This is why in the code `topo_sort()` and `is_dag()` look almost identical—`is_dag` is essentially the "decision version" of topological sorting, only caring whether the sort can finish, not recording the order.
