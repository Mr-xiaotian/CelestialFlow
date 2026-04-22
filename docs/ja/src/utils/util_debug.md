# UtilsDebug

> 📅 最終更新日: 2026/04/22

`utils/util_debug.py` はデバッグ補助関数を提供します。

## 主要関数

- `find_unpickleable(obj)`: オブジェクトが pickle 可能かどうかを検査し、失敗時に診断情報を出力します。

process モードでのオブジェクトシリアライズ問題の調査に一般的に使用されます。
