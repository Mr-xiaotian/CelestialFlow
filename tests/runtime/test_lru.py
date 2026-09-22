"""``LruHashSet`` 有界 LRU 集合测试。

覆盖容量上界、LRU 淘汰顺序、命中刷新以及非法容量配置。
"""

import pytest

from celestialflow.runtime.util_errors import ConfigurationError
from celestialflow.runtime.util_lru import LruHashSet


class TestLruHashSet:
    def test_add_if_absent_returns_new_flag(self) -> None:
        """首次加入返回 True，重复加入返回 False。"""
        lru = LruHashSet(max_size=4)
        assert lru.add_if_absent(b"a") is True
        assert lru.add_if_absent(b"a") is False
        assert lru.add_if_absent(b"b") is True

    def test_check_membership(self) -> None:
        """check 对已存在元素返回 True，对未知元素返回 False。"""
        lru = LruHashSet(max_size=4)
        lru.add_if_absent(b"a")
        assert lru.check(b"a") is True
        assert lru.check(b"b") is False

    def test_never_exceeds_max_size(self) -> None:
        """超出容量后集合大小不超过 max_size。"""
        lru = LruHashSet(max_size=3)
        for i in range(10):
            lru.add_if_absent(str(i).encode())
        assert len(lru) == 3

    def test_evicts_least_recently_used(self) -> None:
        """超出容量时淘汰最久未访问的键。"""
        lru = LruHashSet(max_size=2)
        lru.add_if_absent(b"a")
        lru.add_if_absent(b"b")
        lru.add_if_absent(b"c")

        assert b"a" not in lru
        assert lru.check(b"b") is True
        assert lru.check(b"c") is True

    def test_hit_refreshes_recency(self) -> None:
        """命中 check 会刷新 LRU 位置，避免热点键被淘汰。"""
        lru = LruHashSet(max_size=2)
        lru.add_if_absent(b"a")
        lru.add_if_absent(b"b")

        # 访问 a 使其成为最近使用，随后插入 c 应淘汰 b。
        assert lru.check(b"a") is True
        lru.add_if_absent(b"c")

        assert lru.check(b"a") is True
        assert b"b" not in lru
        assert lru.check(b"c") is True

    def test_add_existing_refreshes_recency(self) -> None:
        """重复加入已存在键同样刷新 LRU 位置。"""
        lru = LruHashSet(max_size=2)
        lru.add_if_absent(b"a")
        lru.add_if_absent(b"b")
        lru.add_if_absent(b"a")
        lru.add_if_absent(b"c")

        assert lru.check(b"a") is True
        assert b"b" not in lru

    def test_clear(self) -> None:
        """clear 后集合为空。"""
        lru = LruHashSet(max_size=4)
        lru.add_if_absent(b"a")
        lru.clear()
        assert len(lru) == 0
        assert lru.check(b"a") is False

    def test_rejects_non_positive_max_size(self) -> None:
        """非正整数容量应抛出 ConfigurationError。"""
        with pytest.raises(ConfigurationError):
            LruHashSet(max_size=0)
        with pytest.raises(ConfigurationError):
            LruHashSet(max_size=-1)
