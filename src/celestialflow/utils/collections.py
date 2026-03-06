from collections import defaultdict
from typing import Dict, List


def cluster_by_value_sorted(input_dict: Dict[str, int]) -> Dict[int, List[str]]:
    """
    按值聚类，并确保按 value（键）升序排序

    :param input_dict: 输入字典
    :return: 聚类后的字典，键为值，值为键的列表
    """
    clusters = defaultdict(list)
    for key, val in input_dict.items():
        clusters[val].append(key)

    return dict(sorted(clusters.items()))  # 按键排序