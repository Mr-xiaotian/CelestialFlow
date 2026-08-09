from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from .core_fallback import get_fallback_spout
from .core_log import get_log_spout


@contextmanager
def funnel_scope() -> Generator[None, None, None]:
    """
    管理全局 funnel 生命周期的单层作用域。

    - 进入作用域时启动全局 ``fallback`` / ``log`` spout
    - 退出作用域时统一停止 spout
    - 当前实现不承诺嵌套作用域复用
    :return: ``None``
    :rtype: Iterator[None]
    :raises ExceptionGroup: 进入或退出作用域时存在一个或多个异常
    """
    error_list: list[Exception] = []
    
    try:
        get_fallback_spout().start()
        get_log_spout().start()
        yield
    except Exception as exception:
        error_list.append(exception)
    finally:
        try:
            get_log_spout().stop()
        except Exception as exception:
            error_list.append(exception)
        try:
            get_fallback_spout().stop()
        except Exception as exception:
            error_list.append(exception)

    if error_list:
        raise ExceptionGroup("Errors occurred during funnel scope", error_list)
