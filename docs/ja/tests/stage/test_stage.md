# TaskStage テスト (test_stage.py)

> 📅 最終更新日: 2026/06/05

## 目的

ノード単位の stage ライフサイクル、キュー結線、グラフ連携時の実行挙動を検証します。

## 主要ポイント

- タスク取り込み、結果出力、シグナル処理を stage レベルで扱います。
- 全グラフトポロジで使う stage 抽象を守ります。

## 実行方法

```bash
pytest tests/stage/test_stage.py -v
pytest tests/stage/test_stage.py -k "stage or signal" -v
```
