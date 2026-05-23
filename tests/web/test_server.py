from datetime import datetime

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
    assert "refreshInterval" in data
    assert "theme" in data
    assert "showStructureEdgeDelta" in data

def test_status_push_pull(client):
    """测试状态同步链路：验证已知版本号（known_rev）下的增量拉取逻辑"""
    # 1. 推送状态
    test_timestamp = 1710000000.0
    test_status = {"s1": {"tasks_succeeded": 10, "tasks_failed": 0}}
    push_resp = client.post(
        "/api/push_status",
        json={"timestamp": test_timestamp, "status": test_status},
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

    # 3. 再次拉取相同版本 (known_rev=current_rev)
    current_rev = pull_data["rev"]
    pull_resp_cached = client.get(f"/api/pull_status?known_rev={current_rev}")
    assert pull_resp_cached.json()["data"] is None

def test_task_injection(client):
    """测试任务手动注入流程：验证 POST 注入任务到队列，以及调度器的 GET 拉取消费逻辑"""
    # 1. 注入任务
    injection_data = {
        "node": "StageA",
        "task_datas": [1, 2, 3],
        "timestamp": datetime.now().isoformat()
    }
    push_resp = client.post("/api/push_injection_tasks", json=injection_data)
    assert push_resp.status_code == 200
    assert push_resp.json() == {"ok": True}

    # 2. 拉取注入任务
    pull_resp = client.get("/api/pull_task_injection")
    assert pull_resp.status_code == 200
    tasks = pull_resp.json()
    assert len(tasks) == 1
    assert tasks[0]["node"] == "StageA"
    assert tasks[0]["task_datas"] == [1, 2, 3]

    # 3. 再次拉取应为空（已清空）
    pull_again = client.get("/api/pull_task_injection")
    assert pull_again.json() == []

def test_errors_pagination(client):
    """测试错误日志分页与过滤 API：验证后端对错误记录的聚合与分页逻辑是否正确"""
    # 1. 模拟推送错误数据
    test_errors = [
        {"error_id": i, "stage": f"s{i%2}", "task_repr": f"task{i}"}
        for i in range(15)
    ]
    # 注意：由于 push_errors_meta 需要真实路径，我们直接用 push_errors_content
    client.post("/api/push_errors_content", json={
        "errors": test_errors,
        "jsonl_path": "dummy.jsonl",
        "rev": 1
    })

    # 2. 测试分页（第一页，每页10条）
    resp_p1 = client.get("/api/pull_errors?page=1&page_size=10")
    data_p1 = resp_p1.json()
    assert data_p1["total"] == 15
    assert data_p1["total_pages"] == 2
    assert len(data_p1["data"]) == 10

    # 3. 测试过滤 (node=s0)
    resp_filter = client.get("/api/pull_errors?node=s0")
    data_filter = resp_filter.json()
    # 0, 2, 4, 6, 8, 10, 12, 14 -> 8条
    assert data_filter["total"] == 8
