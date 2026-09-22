# runtime/util_lru.py
from __future__ import annotations

from collections import OrderedDict

from .util_errors import ConfigurationError


class LruHashSet:
    """有容量上限的精确哈希集合，超出上限后按 LRU 淘汰最久未访问元素。

    用于任务去重：内存占用有硬上界，代价是被淘汰的键之后再次出现时会被当作
    新键处理，因此只会导致任务重复执行，而不会丢弃任务。
    """

    max_size: int
    _entries: OrderedDict[bytes, None]

    def __init__(self, max_size: int) -> None:
        """
        初始化有界 LRU 哈希集合。

        :param max_size: 集合可容纳元素的最大数量，必须为正整数
        :raises ConfigurationError: ``max_size`` 不是正整数
        """
        if max_size <= 0:
            raise ConfigurationError(
                f"max_size of LruHashSet must be a positive integer, got {max_size}"
            )
        self.max_size = max_size
        self._entries = OrderedDict()

    def add_if_absent(self, key: bytes) -> bool:
        """
        加入一个键。

        键不存在时插入并返回 ``True``；已存在时仅刷新其 LRU 位置并返回
        ``False``。插入后若超出 ``max_size``，淘汰最久未访问的键。

        :param key: 待加入的哈希键
        :return: 键是否为本次新插入
        :rtype: bool
        """
        if key in self._entries:
            self._entries.move_to_end(key)
            return False
        self._entries[key] = None
        if len(self._entries) > self.max_size:
            self._entries.popitem(last=False)
        return True

    def check(self, key: bytes) -> bool:
        """
        判断键是否已存在，存在时刷新其 LRU 位置。

        :param key: 待检查的哈希键
        :return: 键是否已存在
        :rtype: bool
        """
        if key not in self._entries:
            return False
        self._entries.move_to_end(key)
        return True

    def __contains__(self, key: bytes) -> bool:
        """判断键是否已存在（不改变 LRU 位置）。"""
        return key in self._entries

    def __len__(self) -> int:
        """返回当前元素数量。"""
        return len(self._entries)

    def clear(self) -> None:
        """清空集合。"""
        self._entries.clear()
