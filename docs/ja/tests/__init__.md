# tests パッケージ

> 📅 最終更新日: 2026/06/05

## 目的

`tests/` 配下の pytest スイートを索引化し、各サブパッケージの役割を説明します。

## 主要ポイント

- funnel、graph、observability、persistence、runtime、stage、web の各テスト群をまとめます。
- `tests/conftest.py` に共通 helper があることを示します。

## 実行方法

```bash
pytest tests -v
pytest tests/runtime -v
pytest tests/stage -k "executor or stage" -v
```
