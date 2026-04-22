# demo/__init__.py 説明

## 目的

`demo/` ディレクトリを Python パッケージとして認識させ、`from demo.xxx import ...` の形式でデモモジュールをインポートできるようにします。

## 内容

現在このファイルは空（0バイト）であり、パッケージマーカーとしてのみ存在します。

## 発生しうる問題

1. **tests/examples との命名競合**：`demo/` と `tests/examples/` に同名のファイル（例：`demo_executor.py`）が存在する場合、Python のインポートシステムが `sys.path` の順序に基づいて誤ったモジュールを解決する可能性があります。
2. **パッケージ内相対インポートの制限**：`demo/` はプロジェクトルートのデフォルト Python パスに含まれていないため、サブモジュールを直接実行すると `ModuleNotFoundError` が発生する場合があります。

## 実行方法

直接実行する必要はありません。demo をパッケージとしてインポートするには、プロジェクトルートが `PYTHONPATH` に含まれていることを確認してください：
```bash
set PYTHONPATH=D:\Project\CelestialFlow;%PYTHONPATH%
python -c "from demo import demo_executor"
```
