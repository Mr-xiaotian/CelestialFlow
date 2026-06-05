# util_cal

> 📅 最終更新日: 2026/05/23

Web モジュールの計算ユーティリティ関数です。

## cal_interval

```python
def cal_interval(refresh_interval: int) -> float:
    """ミリ秒単位のリフレッシュ間隔を秒に換算し、[1.0, 60.0] の範囲に制限します。"""
```

フロントエンドから渡されるミリ秒単位のリフレッシュ間隔を秒に変換し、適切な範囲に制限することで、ポーリング頻度が高すぎてサーバーに過大な負荷がかかるのを防ぎ、また頻度が低すぎてデータ遅延が発生するのを防ぎます。

## 使用例

### カレンダー/時間計算関数の使用例

```python
from celestialflow.web.util_cal import cal_interval

# 5000ms -> 5.0s（標準の 5 秒リフレッシュ）
print(f"5000ms -> {cal_interval(5000)}s")    # 5.0

# 1000ms -> 1.0s（下限 1 秒）
print(f"1000ms -> {cal_interval(1000)}s")    # 1.0

# 500ms -> 1.0s（下限を下回るため、1.0 に制限）
print(f"500ms  -> {cal_interval(500)}s")     # 1.0

# 120000ms -> 60.0s（上限を超えるため、60.0 に制限）
print(f"120000ms -> {cal_interval(120000)}s") # 60.0

# 境界：上限とちょうど等しい場合
print(f"60000ms -> {cal_interval(60000)}s")   # 60.0

# 典型的な Web UI リフレッシュ間隔の設定
refresh_options_ms = [1000, 2000, 5000, 10000, 30000]
print("\n一般的なリフレッシュ間隔の変換:")
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
