from celestialflow.runtime.util_hash import make_hashable, object_to_hash


class TestUtilHash:
    # ====================== make_hashable ======================

    def test_make_hashable_basic_types(self):
        """基本类型（int, str, float, bool, None）应原样返回。"""
        assert make_hashable(42) == 42
        assert make_hashable("hello") == "hello"
        assert make_hashable(3.14) == 3.14
        assert make_hashable(True) is True
        assert make_hashable(None) is None

    def test_make_hashable_tuple_already_hashable(self):
        """元组本身可哈希，应原样返回。"""
        assert make_hashable((1, 2, 3)) == (1, 2, 3)
        assert make_hashable(("a", "b")) == ("a", "b")
        assert make_hashable(()) == ()

    def test_make_hashable_empty_containers(self):
        """空容器：[] → ()，{} → ()。"""
        assert make_hashable([]) == ()
        assert make_hashable({}) == ()

    def test_make_hashable_list_to_tuple(self):
        """列表应转为元组。"""
        assert make_hashable([1, 2, 3]) == (1, 2, 3)
        assert make_hashable(["a", "b"]) == ("a", "b")

    def test_make_hashable_nested_lists(self):
        """嵌套列表：list of list → tuple of tuples。"""
        assert make_hashable([[1, 2], [3, 4]]) == ((1, 2), (3, 4))
        assert make_hashable([["a"], ["b", "c"]]) == (("a",), ("b", "c"))

    def test_make_hashable_dict(self):
        """字典转为排序后的 (key, value) 元组。"""
        result = make_hashable({"b": 2, "a": 1})
        # 排序后 key 顺序为 "a", "b"
        assert result == (("a", 1), ("b", 2))

    def test_make_hashable_nested_dict(self):
        """嵌套字典的递归转换。"""
        obj = {"outer": {"inner_a": 1, "inner_b": 2}}
        result = make_hashable(obj)
        expected = (("outer", (("inner_a", 1), ("inner_b", 2))),)
        assert result == expected

    def test_make_hashable_dict_of_list(self):
        """字典的值包含列表。"""
        obj = {"nums": [3, 1, 2], "letters": ["c", "a"]}
        result = make_hashable(obj)
        expected = (("letters", ("c", "a")), ("nums", (3, 1, 2)))
        assert result == expected

    def test_make_hashable_mixed_types(self):
        """混合类型：列表中包含字典和基本类型。"""
        obj = [{"key": "value"}, 42, "text", [1, 2]]
        result = make_hashable(obj)
        expected = ((("key", "value"),), 42, "text", (1, 2))
        assert result == expected

    def test_make_hashable_set(self):
        """set 转为排序后的元组。"""
        obj = {3, 1, 2}
        result = make_hashable(obj)
        assert result == (1, 2, 3)

    def test_make_hashable_result_is_hashable(self):
        """验证 make_hashable 的结果确实可哈希（可用于 set / dict key）。"""
        obj = [{"b": [3, 4]}, {"a": [1, 2]}]
        result = make_hashable(obj)
        # 若能放入 set 说明可哈希
        s = {result}
        assert len(s) == 1

    # ====================== object_to_hash ======================

    def test_object_to_hash_return_type(self):
        """返回值应为 20 字节的 SHA1 摘要。"""
        h = object_to_hash("test")
        assert isinstance(h, bytes)
        assert len(h) == 20

    def test_object_to_hash_basic_types(self):
        """基本类型均可计算哈希且不抛异常。"""
        assert isinstance(object_to_hash(42), bytes)
        assert isinstance(object_to_hash("hello"), bytes)
        assert isinstance(object_to_hash(3.14), bytes)
        assert isinstance(object_to_hash(True), bytes)
        assert isinstance(object_to_hash(None), bytes)

    def test_object_to_hash_idempotent(self):
        """同一对象多次调用应产生完全相同的哈希值。"""
        obj = {"key": [1, 2, 3], "nested": {"a": "b"}}
        h1 = object_to_hash(obj)
        h2 = object_to_hash(obj)
        assert h1 == h2
        assert h1 == object_to_hash(obj)  # 第三次调用也一致

    def test_object_to_hash_same_structure_same_hash(self):
        """相同结构的对象应产生相同哈希。"""
        a = [1, 2, 3]
        b = [1, 2, 3]
        assert object_to_hash(a) == object_to_hash(b)

    def test_object_to_hash_different_objects_different_hash(self):
        """不同对象应产生不同哈希。"""
        h_int = object_to_hash(1)
        h_str = object_to_hash("1")
        h_list = object_to_hash([1])
        h_dict = object_to_hash({"a": 1})

        # 所有都应互不相同
        hashes = {h_int, h_str, h_list, h_dict}
        assert len(hashes) == 4

    def test_object_to_hash_nested_structures(self):
        """嵌套结构可正确计算哈希。"""
        obj = {"a": [{"b": 2}, {"c": 3}]}
        h = object_to_hash(obj)
        assert isinstance(h, bytes)
        assert len(h) == 20

    def test_object_to_hash_empty_containers(self):
        """空容器可正确计算哈希，且不同的空容器产生不同哈希。"""
        h_empty_list = object_to_hash([])
        h_empty_dict = object_to_hash({})
        h_empty_tuple = object_to_hash(())
        assert isinstance(h_empty_list, bytes)
        assert isinstance(h_empty_dict, bytes)
        assert isinstance(h_empty_tuple, bytes)
        # 不同类型应不同
        assert h_empty_list != h_empty_dict
        assert h_empty_list != h_empty_tuple

    def test_object_to_hash_consistent_across_calls(self):
        """相同值 / 相同结构在多次调用中的哈希一致。"""
        v1 = [1, "a", 3.0]
        v2 = [1, "a", 3.0]  # 等值但不同对象
        assert object_to_hash(v1) == object_to_hash(v2)
        assert object_to_hash(v1) == object_to_hash(v1)


# ============================================================
# 运行方式:
#   python -m pytest tests/utils/test_utils_hash.py -v
# ============================================================
