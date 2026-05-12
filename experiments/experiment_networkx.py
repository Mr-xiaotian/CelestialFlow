import networkx as nx

G = nx.DiGraph()

# 外层结构：1-2 fanout

# 分支 A：内部 3 节点循环 (A1 -> A2 -> A3 -> A1)
# 入口 A_in 指向循环中的 A1
G.add_edge('A1', 'A2')
G.add_edge('A2', 'A3')
G.add_edge('A3', 'A1')  # 闭合循环

# 分支 A 的出口（从循环引出）
G.add_edge('A3', 'B1')  # A3 引出到 B1，进入分支 B

# 分支 B：内部 4 节点循环 (B1 -> B2 -> B3 -> B4 -> B1)
G.add_edge('B1', 'B2')
G.add_edge('B2', 'B3')
G.add_edge('B3', 'B4')
G.add_edge('B4', 'B1')  # 闭合循环

# 分支 B 的出口
G.add_edge('A3', 'C1')

# 分支 C：内部 2 节点循环 (C1 -> C2 -> C1)
G.add_edge('C1', 'C2')
G.add_edge('C2', 'C1')


# 验证结构
print("节点:", list(G.nodes()))
print("边:", list(G.edges()))
print()

# SCC 分析
sccs = list(nx.strongly_connected_components(G))
print(f"SCC 数量: {len(sccs)}")
for i, scc in enumerate(sccs):
    print(f"  SCC {i}: {scc}")

# 缩合图
C = nx.condensation(G)
print(f"\n缩合图节点: {list(C.nodes(data=True))}")
print(f"缩合图边: {list(C.edges())}")

# Source SCC 代表点
source_scc_ids = [n for n, d in C.in_degree() if d == 0]
sources = [next(iter(C.nodes[scc_id]['members'])) for scc_id in source_scc_ids]
print(f"\n源点 SCC: {source_scc_ids}")
print(f"启动 BFS 的代表点: {sources}")

# 验证覆盖
visited = set()
for r in sources:
    visited |= set(nx.bfs_tree(G, r).nodes())
print(f"BFS 覆盖: {visited}")
print(f"完全覆盖: {visited == set(G.nodes())}")