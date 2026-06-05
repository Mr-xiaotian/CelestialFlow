# stage テストパッケージ

> 📅 最終更新日: 2026/06/05

## 目的

`TaskStage`、`TaskExecutor`、組み込み stage helper のテストを索引化します。

## 主要ポイント

- ライフサイクル、実行モード、routing、splitting、transport を扱います。
- graph テストをノード単位の実行観点で補完します。

## 実行方法

```bash
pytest tests/stage -v
pytest tests/stage -k "executor or stage" -v
```
