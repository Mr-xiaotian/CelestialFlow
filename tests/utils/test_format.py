from celestialflow.utils.util_format import format_repr, format_table

class TestUtilFormat:
    def test_format_repr_no_truncation(self):
        """测试不截断的情况"""
        assert format_repr("hello world", 20) == "hello world"
        assert format_repr("short", 5) == "short"
        assert format_repr("", 10) == ""

    def test_format_repr_truncation(self):
        long_str = "this is a very very very long string that needs to be truncated"
        result = format_repr(long_str, 30)
        assert "..." in result
        assert len(result) <= 33  # 20 (first 2/3) + 3 dots + 10 (last 1/3)

    def test_format_repr_edge_cases(self):
        assert format_repr("abcde", 3) == "ab...e"
        assert format_repr("abcdef", 3) == "ab...f"

    def test_format_repr_escape_chars(self):
        """测试特殊字符转义"""
        assert format_repr("line1\nline2\\path", 50) == "line1\\nline2\\\\path"

    def test_format_table_empty_data(self):
        """测试空数据"""
        assert format_table([]) == "表格数据为空！"

    def test_format_table_basic(self):
        """测试基本表格格式化"""
        data = [[1, 2], [3, 4]]
        expected = (
            "+---+---+---+\n"
            "| # | A | B |\n"
            "+---+---+---+\n"
            "| 0 | 1 | 2 |\n"
            "| 1 | 3 | 4 |\n"
            "+---+---+---+"
        )
        assert format_table(data) == expected

    def test_format_table_with_names(self):
        data = [["apple", 10], ["banana", 20]]
        row_names = ["Fruit A", "Fruit B"]
        column_names = ["Name", "Count"]
        expected = (
            "+---------+--------+-------+\n"
            "| #       | Name   | Count |\n"
            "+---------+--------+-------+\n"
            "| Fruit A | apple  | 10    |\n"
            "| Fruit B | banana | 20    |\n"
            "+---------+--------+-------+"
        )
        assert format_table(data, row_names=row_names, column_names=column_names) == expected

    def test_format_table_fill_value(self):
        """测试填充值"""
        data = [[1], [2, 3]]
        expected = (
            "+---+---+-----+\n"
            "| # | A | B   |\n"
            "+---+---+-----+\n"
            "| 0 | 1 | N/A |\n"
            "| 1 | 2 | 3   |\n"
            "+---+---+-----+"
        )
        assert format_table(data, fill_value="N/A") == expected

    def test_format_table_alignment(self):
        """测试对齐方式"""
        data = [["a", 100], ["bb", 20]]
        expected_right = (
            "+---+----+-----+\n"
            "| # |  A |   B |\n"
            "+---+----+-----+\n"
            "| 0 |  a | 100 |\n"
            "| 1 | bb |  20 |\n"
            "+---+----+-----+"
        )
        assert format_table(data, align="right") == expected_right

        expected_left = (
            "+---+----+-----+\n"
            "| # | A  | B   |\n"
            "+---+----+-----+\n"
            "| 0 | a  | 100 |\n"
            "| 1 | bb | 20  |\n"
            "+---+----+-----+"
        )
        assert format_table(data, align="left") == expected_left
