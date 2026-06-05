# funnel テストパッケージ

> 📅 最終更新日: 2026/06/05

## 目的

`BaseInlet` と `BaseSpout` の基本的なキュー挙動とライフサイクルを検証します。

## 主要ポイント

- 永続化実装ではなく、漏斗の基礎部品に焦点を当てます。
- 非同期タイミング helper を使ってスレッド挙動を確認します。

## 実行方法

```bash
pytest tests/funnel -v
pytest tests/funnel -k "inlet or spout" -v
```
