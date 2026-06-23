"""Pydantic 模型定义。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, RootModel


class StructureModel(BaseModel):
    """任务结构数据模型"""

    graph_id: str = ""
    structure: dict[str, Any]


class StatusModel(BaseModel):
    """节点状态数据模型"""

    graph_id: str = ""
    timestamp: float
    status: dict[str, dict[str, Any]]


class ErrorsModel(BaseModel):
    """错误内容数据模型"""

    graph_id: str = ""
    errors: list[dict[str, Any]]


class AnalysisModel(BaseModel):
    """任务分析数据模型"""

    graph_id: str = ""
    analysis: dict[str, Any]


class TaskInjectionModel(RootModel[dict[str, list[Any]]]):
    """任务注入请求模型，格式为 {node_name: [tasklist]}"""


class TerminationInjectionModel(RootModel[list[str]]):
    """终止符注入请求模型，格式为 [node_name, ...]。"""


class DashboardConfigModel(BaseModel):
    """仪表盘卡片布局配置模型"""

    left: list[str]
    middle: list[str]
    right: list[str]


class GlobalConfigModel(BaseModel):
    """全局共享配置模型"""

    theme: str
    autoRefreshEnabled: bool = True
    refreshInterval: int
    language: str = "zh-CN"


class DashboardPageConfigModel(BaseModel):
    """仪表盘页面配置模型"""

    historyLimit: int
    showStructureEdgeDelta: bool = False
    useTotalPendingInStatus: bool = False
    layout: DashboardConfigModel


class ErrorsPageConfigModel(BaseModel):
    """错误页配置模型"""

    pageSize: int = 10
    sortOrder: str = "newest"
    jumpToInjectionAfterRetry: bool = True


class InjectionPageConfigModel(BaseModel):
    """注入页配置模型。"""

    showInjectableOnly: bool = True


class WebConfigModel(BaseModel):
    """Web UI 分组配置模型"""

    global_: GlobalConfigModel = Field(alias="global")
    dashboard: DashboardPageConfigModel
    errors: ErrorsPageConfigModel
    injection: InjectionPageConfigModel = Field(
        default_factory=InjectionPageConfigModel
    )
