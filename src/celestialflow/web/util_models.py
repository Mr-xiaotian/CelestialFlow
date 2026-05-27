"""Pydantic 模型定义。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class StructureModel(BaseModel):
    """任务结构数据模型"""

    items: list[dict[str, Any]]


class StatusModel(BaseModel):
    """节点状态数据模型"""

    timestamp: float
    status: dict[str, dict[str, Any]]


class ErrorsMetaModel(BaseModel):
    """错误元数据模型"""

    jsonl_path: str
    rev: int


class ErrorsContentModel(BaseModel):
    """错误内容数据模型"""

    errors: list[dict[str, Any]]
    jsonl_path: str
    rev: int


class AnalysisModel(BaseModel):
    """任务分析数据模型"""

    analysis: dict[str, Any]


class SummaryModel(BaseModel):
    """任务汇总数据模型"""

    summary: dict[str, Any]


class TaskInjectionModel(BaseModel):
    """任务注入请求模型"""

    node: str
    task_datas: list[Any]
    timestamp: datetime


class DashboardConfigModel(BaseModel):
    """仪表盘布局配置模型"""

    left: list[str]
    middle: list[str]
    right: list[str]


class WebConfigModel(BaseModel):
    """Web UI 全局配置模型"""

    theme: str
    refreshInterval: int
    historyLimit: int
    language: str = "zh-CN"
    errorPageSize: int = 10
    showStructureEdgeDelta: bool = True
    dashboard: DashboardConfigModel
