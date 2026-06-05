# JSONL 永続化 helper テスト (test_jsonl.py)

> 📅 最終更新日: 2026/06/05

## 目的

永続化ファイルからタスクログを読み出す JSONL helper を検証します。

## 主要ポイント

- ステージ別・エラー別の読み出しを確認します。
- Web のエラー閲覧経路で使う問い合わせ処理を保護します。

## 実行方法

```bash
pytest tests/persistence/test_jsonl.py -v
pytest tests/persistence/test_jsonl.py -k "stage or error" -v
```
