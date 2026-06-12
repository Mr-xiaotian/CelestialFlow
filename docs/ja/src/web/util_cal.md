# util_cal

> 📅 最終更新日: 2026/05/23

Web モジュールの計算ユーティリティ関数。

## cal_interval

```python
def cal_interval(refresh_interval: int) -> float:
    """ミリ秒の更新間隔を秒に変換し、[1.0, 60.0] の範囲に制限します。"""
```

フロントエンドから渡されたミリ秒単位の更新間隔を秒に変換し、適切な範囲に制限します。ポーリング頻度が高すぎてサーバー負荷が過大になることや、低すぎてデータ遅延が発生することを防止します。

## 使用例

### カレンダー/時間計算関数の使用例

```python
from celestialflow.web.util_cal import cal_interval

# 5000ms -> 5.0s（標準の5秒更新）
print(f"5000ms -> {cal_interval(5000)}s")    # 5.0

# 1000ms -> 1.0s（下限1秒）
print(f"1000ms -> {cal_interval(1000)}s")    # 1.0

# 500ms -> 1.0s（下限を下回り、1.0に制限）
print(f"500ms  -> {cal_interval(500)}s")     # 1.0

# 120000ms -> 60.0s（上限を超え、60.0に制限）
print(f"120000ms -> {cal_interval(120000)}s") # 60.0

# 境界：ちょうど上限に等しい
print(f"60000ms -> {cal_interval(60000)}s")   # 60.0

# 典型的な Web UI 更新間隔の設定
refresh_options_ms = [1000, 2000, 5000, 10000, 30000]
print("\n一般的な更新間隔の変換:")
for ms in refresh_options_ms:
    seconds = cal_interval(ms)
    print(f"  {ms:>6}ms -> {seconds:.1f}s")
# 出力：
#    1000ms -> 1.0s
#    2000ms -> 2.0s
#    5000ms -> 5.0s
#   10000ms -> 10.0s
#   30000ms -> 30.0s
```
