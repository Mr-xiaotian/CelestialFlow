# 組み込み Stage helper テスト (test_stages.py)

> 📅 最終更新日: 2026/06/05

## 目的

splitter、router、Redis transport/source/ack など、同梱 stage helper を検証します。

## 主要ポイント

- stage 固有の便利機能を確認します。
- 組み込みパイプライン helper の回帰を防ぎます。

## 実行方法

```bash
pytest tests/stage/test_stages.py -v
pytest tests/stage/test_stages.py -k "split or route or redis" -v
```
