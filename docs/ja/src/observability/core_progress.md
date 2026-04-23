# TaskProgress

> 📅 最終更新日: 2026/04/22

TaskProgress モジュールは、`tqdm` ベースのタスク進捗可視化を提供します。

## 機能

- **動的更新**: 総タスク数の動的な増加（`add_total`）をサポートし、ストリーミングタスクやタスク分割のシナリオに対応します。
- **マルチモードサポート**: 
  - 通常モード: 標準の `tqdm` を使用します。
  - 非同期モード: `tqdm.asyncio` を使用し、`async` 実行モードに適しています。
- **Null モード**: `NullTaskProgress` はプログレスバー表示が無効な場合の Null 実装で、コード中に `if show_progress` の判定が散在するのを避けます。

## 使用方法

`TaskExecutor` または `TaskStage` 内で初期化します：

```python
self.task_progress = TaskProgress(
    total_tasks=0,  # 初期値は通常 0、タスクの入力に応じて動的に増加
    desc="Processing",
    mode="normal"
)
```

進捗を更新：

```python
self.task_progress.update(1)
```

総数を動的に増加：

```python
self.task_progress.add_total(100)
```
