# UtilsCollections

> 📅 最終更新日: 2026/04/22

`utils/util_collections.py` はコレクション/辞書のクラスタリングツールを提供します。

## 主要関数

- `cluster_by_value_sorted(input_dict)`: 値でクラスタリングし、値の昇順で返します。

## 使用例

### cluster_by_value_sorted の完全な例

以下に様々なクラスタリングシナリオの使用方法を示します：

```python
from celestialflow.utils.util_collections import cluster_by_value_sorted

# 例 1：基本的な使い方——タスク処理量でステージをグループ化
stage_stats = {
    "data_loader": 100,
    "preprocessor": 50,
    "analyzer": 100,
    "exporter": 50,
    "validator": 200,
}
result = cluster_by_value_sorted(stage_stats)
print("処理量でクラスタリングした結果:")
for value, stages in result.items():
    print(f"  処理量 {value:>3}: {stages}")
# 出力：
#   処理量  50: ['preprocessor', 'exporter']
#   処理量 100: ['data_loader', 'analyzer']
#   処理量 200: ['validator']

# 例 2：独立したキーにより各キーが独自のクラスになる
test_data = {"a": 1, "b": 2, "c": 3}
print(f"\n独立値クラスタリング: {cluster_by_value_sorted(test_data)}")
# 出力：{1: ['a'], 2: ['b'], 3: ['c']}

# 例 3：全キーが同じ値を共有
test_data = {"x": 0, "y": 0, "z": 0}
print(f"\n同一値クラスタリング: {cluster_by_value_sorted(test_data)}")
# 出力：{0: ['x', 'y', 'z']}

# 例 4：エラー数でサービスをクラスタリング
error_counts = {
    "auth-service": 23,
    "payment-service": 45,
    "inventory-service": 12,
    "notification-service": 45,
    "search-service": 23,
    "gateway": 67,
}
grouped = cluster_by_value_sorted(error_counts)
print("\nエラー数でクラスタリング（同レベルの問題サービスを特定）:")
for count, services in grouped.items():
    bar = "#" * (count // 5)
    print(f"  {count:>2} 件のエラー {bar:>15}: {services}")
# 出力：
#  12 件のエラー           ##: ['inventory-service']
#  23 件のエラー          ####: ['auth-service', 'search-service']
#  45 件のエラー        #########: ['payment-service', 'notification-service']
#  67 件のエラー        #############: ['gateway']
```
