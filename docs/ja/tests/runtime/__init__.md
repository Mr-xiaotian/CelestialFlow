# runtime テストパッケージ

> 📅 最終更新日: 2026/06/05

## 目的

envelope、queue、hash、counter、error、時間推定など、runtime 層のテストを索引化します。

## 主要ポイント

- graph / stage 層が依存する低レベル実行基盤を守ります。
- 多くは純粋なランタイム契約に焦点を当てた高速ユニットテストです。

## 実行方法

```bash
pytest tests/runtime -v
pytest tests/runtime -k "hash or envelope or estimators" -v
```
