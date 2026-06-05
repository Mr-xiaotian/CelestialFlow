# ランタイムキューテスト (test_queue.py)

> 📅 最終更新日: 2026/06/05

## 目的

envelope 流れと終了処理を含むタスク入出力キューの挙動を検証します。

## 主要ポイント

- キュー投入、drain、source 名追跡を扱います。
- graph / stage 実行が前提とするキュー契約を守ります。

## 実行方法

```bash
pytest tests/runtime/test_queue.py -v
pytest tests/runtime/test_queue.py -k "queue or termination" -v
```
