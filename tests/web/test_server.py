def test_store_snapshot_methods_return_isolated_copies(web_server):
    """测试 server 快照接口：返回值不应与内部 store 共享可变引用"""
    raw_status = {"s1": {"tasks_succeeded": 1, "total_remaining_time": 2.0}}
    raw_structure = {
        "nodes": {"s1": {"func_name": "f1"}},
        "edges": {"s1": []},
        "source_nodes": ["s1"],
    }
    raw_analysis = {"isDAG": True}
    raw_errors = [
        {
            "event_id": 1,
            "stage": "s1",
            "status": "failed",
            "task_json": None,
        }
    ]

    web_server.update_status_store(123.0, raw_status)
    web_server.update_structure_store(raw_structure)
    web_server.update_analysis_store(raw_analysis)
    web_server.update_errors_store(raw_errors)

    _, status_timestamp, status_snapshot = web_server.get_status_snapshot()
    _, structure_snapshot = web_server.get_structure_snapshot()
    _, analysis_snapshot = web_server.get_analysis_snapshot()
    _, errors_snapshot = web_server.get_errors_snapshot()

    raw_status["s1"]["tasks_succeeded"] = 99
    raw_structure["nodes"]["s1"]["func_name"] = "mutated"
    raw_analysis["isDAG"] = False
    raw_errors[0]["stage"] = "mutated"
    status_snapshot["s1"]["tasks_succeeded"] = 88
    structure_snapshot["nodes"]["s1"]["func_name"] = "snapshot-mutated"
    analysis_snapshot["isDAG"] = False
    errors_snapshot[0]["stage"] = "snapshot-mutated"

    _, status_timestamp_after, status_snapshot_after = web_server.get_status_snapshot()
    _, structure_snapshot_after = web_server.get_structure_snapshot()
    _, analysis_snapshot_after = web_server.get_analysis_snapshot()
    _, errors_snapshot_after = web_server.get_errors_snapshot()

    assert status_timestamp == 123.0
    assert status_timestamp_after == 123.0
    assert status_snapshot_after["s1"]["tasks_succeeded"] == 1
    assert structure_snapshot_after["nodes"]["s1"]["func_name"] == "f1"
    assert analysis_snapshot_after["isDAG"] is True
    assert errors_snapshot_after[0]["stage"] == "s1"


def test_get_error_type_counts_returns_grouped_stats(web_server):
    """测试 server 层可返回全部节点的错误类型聚合统计。"""
    web_server.update_errors_store(
        [
            {
                "event_id": 1,
                "stage": "s1",
                "status": "failed",
                "task_json": {"value": 1},
                "error_type": "ValueError",
                "error_message": "bad",
                "ts": 1.0,
            },
            {
                "event_id": 2,
                "stage": "s2",
                "status": "failed",
                "task_json": {"value": 2},
                "error_type": "TypeError",
                "error_message": "boom",
                "ts": 2.0,
            },
            {
                "event_id": 3,
                "stage": "s1",
                "status": "failed",
                "task_json": {"value": 3},
                "error_type": "ValueError",
                "error_message": "bad again",
                "ts": 3.0,
            },
        ]
    )

    rev, items = web_server.get_error_type_counts()

    assert rev == web_server.store_revs["errors"]
    assert items == [
        {"error_type": "ValueError", "count": 2},
        {"error_type": "TypeError", "count": 1},
    ]


def test_get_error_type_counts_supports_node_filter(web_server):
    """测试 server 层错误类型聚合支持按节点过滤。"""
    web_server.update_errors_store(
        [
            {
                "event_id": 1,
                "stage": "s1",
                "status": "failed",
                "task_json": {"value": 1},
                "error_type": "ValueError",
                "error_message": "bad",
                "ts": 1.0,
            },
            {
                "event_id": 2,
                "stage": "s1",
                "status": "failed",
                "task_json": {"value": 2},
                "error_type": "TypeError",
                "error_message": "boom",
                "ts": 2.0,
            },
            {
                "event_id": 3,
                "stage": "s2",
                "status": "failed",
                "task_json": {"value": 3},
                "error_type": "RuntimeError",
                "error_message": "oops",
                "ts": 3.0,
            },
        ]
    )

    rev, items = web_server.get_error_type_counts("s1")

    assert rev == web_server.store_revs["errors"]
    assert items == [
        {"error_type": "TypeError", "count": 1},
        {"error_type": "ValueError", "count": 1},
    ]


def test_index_page(client):
    """测试 Web 仪表盘首页：验证 HTML 模板是否渲染正确且包含关键 DOM 容器"""
    response = client.get("/")
    assert response.status_code == 200
    assert "html" in response.headers["content-type"]
    # 验证模板是否包含关键元素
    assert 'id="dashboard"' in response.text

def test_config_api(client):
    """测试配置拉取 API：验证前端能够获取到刷新间隔、主题等运行时配置"""
    response = client.get("/api/pull_config")
    assert response.status_code == 200
    data = response.json()
    assert "global" in data
    assert "dashboard" in data
    assert "errors" in data
    assert "injection" in data
    assert "autoRefreshEnabled" in data["global"]
    assert "refreshInterval" in data["global"]
    assert "theme" in data["global"]
    assert "showStructureEdgeDelta" in data["dashboard"]
    assert "sortOrder" in data["errors"]
    assert "jumpToInjectionAfterRetry" in data["errors"]
    assert "showInjectableOnly" in data["injection"]

def test_server_state_api(client):
    """测试 reporter 拉取的服务端同步状态。"""
    response = client.get("/api/pull_server_state")

    assert response.status_code == 200
    data = response.json()
    assert data["interval"] > 0
    assert data["is_current_graph"] is True
    assert data["has_structure"] is False
    assert data["has_analysis"] is False
    assert data["max_event_id_in_fail"] is None


def test_push_errors_meta_route_removed(client):
    """`/api/push_errors_meta` 已删除，不应再接受请求。"""
    response = client.post(
        "/api/push_errors_meta",
        json={
            "graph_id": "demo@1000",
            "append": False,
        },
    )

    assert response.status_code == 404

def test_status_push_pull(client):
    """测试状态同步链路：验证已知版本号（known_rev）下的增量拉取逻辑"""
    graph_id = "demo@1000"
    state = client.get(f"/api/pull_server_state?graph_id={graph_id}").json()
    assert state["is_current_graph"] is False

    # 1. 推送状态
    test_timestamp = 1710000000.0
    test_status = {
        "s1": {
            "tasks_succeeded": 10,
            "tasks_failed": 0,
            "remaining_time": 3.5,
            "total_remaining_time": 8.0,
        }
    }
    push_resp = client.post(
        "/api/push_status",
        json={
            "graph_id": graph_id,
            "timestamp": test_timestamp,
            "status": test_status,
        },
    )
    assert push_resp.status_code == 200
    assert push_resp.json() == {"ok": True}

    # 2. 拉取状态 (known_rev=-1)
    pull_resp = client.get("/api/pull_status?known_rev=-1")
    assert pull_resp.status_code == 200
    pull_data = pull_resp.json()
    assert pull_data["rev"] > 0
    assert pull_data["timestamp"] == test_timestamp
    assert pull_data["data"] == test_status
    assert pull_data["data"]["s1"]["total_remaining_time"] == 8.0

    # 3. 再次拉取相同版本 (known_rev=current_rev)
    current_rev = pull_data["rev"]
    pull_resp_cached = client.get(f"/api/pull_status?known_rev={current_rev}")
    assert pull_resp_cached.json()["data"] is None

def test_task_injection(client):
    """测试任务与终止符注入流程：验证服务端原子返回并在 pull 后清空。"""
    # 1. 注入任务
    injection_data = {
        "StageA": [1, 2, 3],
    }
    push_resp = client.post("/api/push_injection_tasks", json=injection_data)
    assert push_resp.status_code == 200
    assert push_resp.json() == {"ok": True}
    termination_resp = client.post(
        "/api/push_injection_terminations", json=["StageB"]
    )
    assert termination_resp.status_code == 200
    assert termination_resp.json() == {"ok": True}

    # 2. 拉取注入任务
    pull_resp = client.get("/api/pull_injection")
    assert pull_resp.status_code == 200
    tasks = pull_resp.json()
    assert tasks == {
        "tasks": injection_data,
        "terminations": ["StageB"],
    }

    # 3. 再次拉取应为空（已清空）
    pull_again = client.get("/api/pull_injection")
    assert pull_again.json() == {"tasks": {}, "terminations": []}


def test_task_injection_overwrites_tasklist_per_node(client):
    """新的 push 会逐个节点更新 task list，终止符单独存储。"""
    client.post(
        "/api/push_injection_tasks",
        json={
            "StageA": [1, 2, 3],
        },
    )
    client.post("/api/push_injection_terminations", json=["StageB"])

    client.post(
        "/api/push_injection_tasks",
        json={
            "StageA": [9],
            "StageC": ["new"],
        },
    )

    pull_resp = client.get("/api/pull_injection")

    assert pull_resp.status_code == 200
    assert pull_resp.json() == {
        "tasks": {
            "StageA": [9],
            "StageC": ["new"],
        },
        "terminations": ["StageB"],
    }


def test_task_injection_requires_tasklist_mapping(client):
    """任务注入接口要求每个节点值都是任务列表数组。"""
    invalid_payload = {
        "StageA": {"user_id": 1},
    }

    response = client.post("/api/push_injection_tasks", json=invalid_payload)

    assert response.status_code == 422


def test_termination_injection_requires_string_array(client):
    """终止符注入接口要求请求体为字符串数组。"""
    response = client.post(
        "/api/push_injection_terminations", json={"StageA": True}
    )

    assert response.status_code == 422

def test_errors_pagination(client):
    """测试错误日志分页与过滤 API：验证后端对错误记录的聚合与分页逻辑是否正确"""
    graph_id = "demo@1000"
    state = client.get(f"/api/pull_server_state?graph_id={graph_id}").json()
    assert state["is_current_graph"] is False

    # 1. 模拟推送错误数据
    test_errors = [
        {
            "event_id": i,
            "stage": f"s{i%2}",
            "status": "failed",
            "task_json": {"value": i, "label": f"task{i}"},
            "error_type": "ValueError" if i % 2 == 0 else "TypeError",
            "error_message": f"err{i}",
            "ts": i,
        }
        for i in range(15)
    ]
    # 错误同步已统一走 push_errors。
    client.post(
        "/api/push_errors",
        json={
            "graph_id": graph_id,
            "errors": test_errors,
        },
    )

    # 2. 测试分页（第一页，每页10条）
    resp_p1 = client.get("/api/pull_errors?page=1&page_size=10")
    data_p1 = resp_p1.json()
    assert data_p1["total"] == 15
    assert data_p1["total_pages"] == 2
    assert len(data_p1["data"]) == 10
    assert data_p1["sort_order"] == "newest"
    assert data_p1["data"][0]["event_id"] == 14
    assert data_p1["data"][0]["task_json"] == {"value": 14, "label": "task14"}

    # 3. 测试过滤 (node=s0)
    resp_filter = client.get("/api/pull_errors?node=s0")
    data_filter = resp_filter.json()
    # 0, 2, 4, 6, 8, 10, 12, 14 -> 8条
    assert data_filter["total"] == 8

    # 4. 测试关键词过滤（任务名与错误字段都可命中）
    resp_keyword = client.get("/api/pull_errors?keyword=task12")
    data_keyword = resp_keyword.json()
    assert data_keyword["total"] == 1
    assert data_keyword["data"][0]["event_id"] == 12

    resp_error_keyword = client.get("/api/pull_errors?keyword=typeerror")
    data_error_keyword = resp_error_keyword.json()
    assert data_error_keyword["total"] == 7

    # 5. 测试排序（最旧优先）
    resp_oldest = client.get("/api/pull_errors?sort_order=oldest&page_size=5")
    data_oldest = resp_oldest.json()
    assert data_oldest["sort_order"] == "oldest"
    assert len(data_oldest["data"]) == 5
    assert data_oldest["data"][0]["event_id"] == 0


def test_pull_error_type_counts(client):
    """测试错误类型聚合 API：支持全部节点、单节点和缓存命中。"""
    graph_id = "demo@1001"
    state = client.get(f"/api/pull_server_state?graph_id={graph_id}").json()
    assert state["is_current_graph"] is False

    test_errors = [
        {
            "event_id": 1,
            "stage": "s1",
            "status": "failed",
            "task_json": {"value": 1},
            "error_type": "ValueError",
            "error_message": "err1",
            "ts": 1,
        },
        {
            "event_id": 2,
            "stage": "s1",
            "status": "failed",
            "task_json": {"value": 2},
            "error_type": "TypeError",
            "error_message": "err2",
            "ts": 2,
        },
        {
            "event_id": 3,
            "stage": "s2",
            "status": "failed",
            "task_json": {"value": 3},
            "error_type": "ValueError",
            "error_message": "err3",
            "ts": 3,
        },
    ]
    client.post(
        "/api/push_errors",
        json={
            "graph_id": graph_id,
            "errors": test_errors,
        },
    )

    resp_all = client.get("/api/pull_error_type_counts")
    assert resp_all.status_code == 200
    all_data = resp_all.json()
    assert all_data["data"] == [
        {"error_type": "ValueError", "count": 2},
        {"error_type": "TypeError", "count": 1},
    ]

    resp_node = client.get("/api/pull_error_type_counts?node=s1")
    assert resp_node.status_code == 200
    node_data = resp_node.json()
    assert node_data["data"] == [
        {"error_type": "TypeError", "count": 1},
        {"error_type": "ValueError", "count": 1},
    ]

    rev = node_data["rev"]
    resp_cached = client.get(f"/api/pull_error_type_counts?node=s1&known_rev={rev}")
    assert resp_cached.status_code == 200
    assert resp_cached.json()["data"] is None


def test_push_errors_appends_for_same_graph(client):
    """相同 graph_id 下，push_errors 只追加新错误。"""
    graph_id = "demo@2000"

    first_batch = [
        {
            "event_id": 1,
            "stage": "s1",
            "status": "failed",
            "task_json": {"value": 1},
            "error_type": "ValueError",
            "error_message": "err1",
            "ts": 1.0,
        },
        {
            "event_id": 2,
            "stage": "s2",
            "status": "failed",
            "task_json": {"value": 2},
            "error_type": "TypeError",
            "error_message": "err2",
            "ts": 2.0,
        },
    ]
    second_batch = [
        {
            "event_id": 3,
            "stage": "s1",
            "status": "failed",
            "task_json": {"value": 3},
            "error_type": "RuntimeError",
            "error_message": "err3",
            "ts": 3.0,
        }
    ]

    state = client.get(f"/api/pull_server_state?graph_id={graph_id}").json()
    assert state["is_current_graph"] is False

    analysis_resp = client.post(
        "/api/push_analysis",
        json={
            "graph_id": graph_id,
            "analysis": {"graphId": graph_id, "name": "demo", "startTime": 2.0},
        },
    )
    assert analysis_resp.status_code == 200
    assert analysis_resp.json() == {"ok": True}

    response = client.post(
        "/api/push_errors",
        json={
            "graph_id": graph_id,
            "errors": first_batch,
        },
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True}

    state = client.get(f"/api/pull_server_state?graph_id={graph_id}").json()
    assert state["is_current_graph"] is True
    assert state["max_event_id_in_fail"] == 2
    assert state["has_analysis"] is True

    response = client.post(
        "/api/push_errors",
        json={
            "graph_id": graph_id,
            "errors": second_batch,
        },
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True}

    pulled = client.get("/api/pull_errors?page=1&page_size=10").json()
    assert pulled["total"] == 3
    assert [item["event_id"] for item in pulled["data"]] == [3, 2, 1]


def test_push_errors_duplicate_append_is_idempotent(client):
    """重复追加相同 event_id 时，错误缓存不应出现重复行。"""
    graph_id = "demo@3000"
    duplicated_batch = [
        {
            "event_id": 1,
            "stage": "s1",
            "status": "failed",
            "task_json": {"value": 1},
            "error_type": "ValueError",
            "error_message": "err1",
            "ts": 1.0,
        }
    ]

    client.get(f"/api/pull_server_state?graph_id={graph_id}")
    client.post(
        "/api/push_analysis",
        json={
            "graph_id": graph_id,
            "analysis": {"graphId": graph_id, "name": "demo", "startTime": 3.0},
        },
    )

    first = client.post(
        "/api/push_errors",
        json={
            "graph_id": graph_id,
            "errors": duplicated_batch,
        },
    )
    second = client.post(
        "/api/push_errors",
        json={
            "graph_id": graph_id,
            "errors": duplicated_batch,
        },
    )

    assert first.status_code == 200
    assert second.status_code == 200

    pulled = client.get("/api/pull_errors?page=1&page_size=10").json()
    assert pulled["total"] == 1
    assert [item["event_id"] for item in pulled["data"]] == [1]


def test_newer_graph_replaces_previous_graph_context(client):
    """较新的 graph_id 到来时，server 会切换图上下文并清空旧错误。"""
    old_graph_id = "demo@1000"
    new_graph_id = "demo@2000"

    state = client.get(f"/api/pull_server_state?graph_id={old_graph_id}").json()
    assert state["is_current_graph"] is False

    client.post(
        "/api/push_analysis",
        json={
            "graph_id": old_graph_id,
            "analysis": {"graphId": old_graph_id, "name": "demo", "startTime": 1.0},
        },
    )
    client.post(
        "/api/push_errors",
        json={
            "graph_id": old_graph_id,
            "errors": [
                {
                    "event_id": 1,
                    "stage": "s1",
                    "status": "failed",
                    "task_json": {"value": 1},
                    "error_type": "ValueError",
                    "error_message": "old",
                    "ts": 1.0,
                }
            ],
        },
    )

    state = client.get(f"/api/pull_server_state?graph_id={new_graph_id}").json()
    assert state["is_current_graph"] is False
    assert state["max_event_id_in_fail"] is None

    pulled = client.get("/api/pull_errors?page=1&page_size=10").json()
    assert pulled["total"] == 0

    analysis = client.get("/api/pull_analysis?known_rev=-1").json()
    assert analysis["data"] is None


def test_stale_graph_pushes_are_ignored(client):
    """切换到新 graph 后，旧 graph 的迟到 push 不应污染当前缓存。"""
    old_graph_id = "demo@1000"
    new_graph_id = "demo@2000"

    client.get(f"/api/pull_server_state?graph_id={old_graph_id}")
    client.post(
        "/api/push_analysis",
        json={
            "graph_id": old_graph_id,
            "analysis": {"graphId": old_graph_id, "name": "demo", "startTime": 1.0},
        },
    )

    client.get(f"/api/pull_server_state?graph_id={new_graph_id}")

    stale_analysis = client.post(
        "/api/push_analysis",
        json={
            "graph_id": old_graph_id,
            "analysis": {"graphId": old_graph_id, "name": "old", "startTime": 1.0},
        },
    )
    assert stale_analysis.status_code == 200
    assert stale_analysis.json() == {"ok": False}

    stale_errors = client.post(
        "/api/push_errors",
        json={
            "graph_id": old_graph_id,
            "errors": [
                {
                    "event_id": 1,
                    "stage": "s1",
                    "status": "failed",
                    "task_json": {"value": 1},
                    "error_type": "ValueError",
                    "error_message": "old",
                    "ts": 1.0,
                }
            ],
        },
    )
    assert stale_errors.status_code == 200
    assert stale_errors.json() == {"ok": False}

    state = client.get(f"/api/pull_server_state?graph_id={new_graph_id}").json()
    assert state["is_current_graph"] is True
    assert state["has_analysis"] is False
    assert state["max_event_id_in_fail"] is None
