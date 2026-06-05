# observability テストパッケージ

> 📅 最終更新日: 2026/06/05

## 目的

reporter と observer 系のランタイム監視挙動をまとめるテスト群です。

## 主要ポイント

- グラフ実行そのものではなく状態報告に焦点を当てます。
- graph / stage テストを監視専用の観点で補完します。

## 実行方法

```bash
pytest tests/observability -v
pytest tests/observability/test_observer.py -v
```
