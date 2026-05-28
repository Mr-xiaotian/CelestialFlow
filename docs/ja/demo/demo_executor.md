# demo_executor.py デモ説明

> 📅 最終更新日: 2026/05/28

## 目的

`TaskExecutor` の3つの実行モード（`serial`、`thread`、`async`）でのスタンドアロン実行能力をデモンストレーションします。例外リトライ、進捗表示、タスク統計の完全なライフサイクルを示し、フレームワーク入門の最初の体験として適しています。

## デモ内容

3 つの実行モードのコア戦略比較：

```mermaid
flowchart TB
    subgraph Serial["シリアルモード serial"]
        direction LR
        T1_1["タスク 1<br/>fibonacci(25)"] --> T1_2["タスク 2<br/>fibonacci(26)"]
        T1_2 --> T1_3["..."]
        T1_3 --> T1_4["タスク 7<br/>fibonacci(31)"]
    end

    subgraph Thread["スレッドモード thread"]
        direction LR
        T2_1["タスク 1<br/>fibonacci(25)"]
        T2_2["タスク 2<br/>fibonacci(26)"]
        T2_3["タスク 3<br/>fibonacci(27)"]
        T2_4["タスク 4<br/>fibonacci(28)"]
        T2_5["タスク 5<br/>fibonacci(29)"]
        T2_6["タスク 6<br/>fibonacci(30)"]
        T2_7["タスク 7<br/>fibonacci(31)"]
    end

    subgraph Async["非同期モード async"]
        direction LR
        T3_1["タスク 1<br/>fibonacci_async(25)"]
        T3_2["タスク 2<br/>fibonacci_async(26)"]
        T3_3["タスク 3<br/>fibonacci_async(27)"]
        T3_4["タスク 4<br/>fibonacci_async(28)"]
        T3_5["タスク 5<br/>fibonacci_async(29)"]
        T3_6["タスク 6<br/>fibonacci_async(30)"]
        T3_7["タスク 7<br/>fibonacci_async(31)"]
    end

    Input["入力<br/>range(25,32) + [0,27,None,0,'']"] --> Serial
    Input --> Thread
    Input --> Async

    Serial --> Retry["自動リトライ 1 回<br/>max_retries=1"]
    Thread --> Retry
    Async --> Retry
```

| 関数 | モード | タスク | 特徴 |
|------|--------|--------|------|
| `demo_fibonacci_serial` | serial | フィボナッチ計算 | シングルスレッド逐次実行 |
| `demo_fibonacci_thread` | thread | フィボナッチ計算 | 6スレッド並行実行 |
| `demo_fibonacci_async` | async | 非同期フィボナッチ | コルーチンベース並行処理 |

- **入力**: `range(25, 32) + [0, 27, None, 0, ""]`
- **例外設計**: `0`、`None`、`""` は `ValueError` をトリガーし、フレームワークが自動的に1回リトライします

## 主要設定

- `max_workers = 6`
- `max_retries = 1`
- `executor.add_observer(TaskProgress())` でプログレスバーを追加

## 起こりうる問題

1. **再帰深度と所要時間**: `fibonacci(31)` は膨大な再帰呼び出しを含み、serial モードでは10秒以上かかる場合があります。
2. **`asyncio` 環境**: `demo_fibonacci_async` は `asyncio.run()` を使用しており、Jupyter Notebook で直接実行するとエラーになります（Notebook には既にイベントループが存在するため）。
3. **アサーションなし**: このファイルは**デモスクリプト**であり、`assert` を含みません。実行成功はキャッチされない例外がなかったことのみを意味し、結果の正確性は検証しません。

## 実行方法

```bash
python demo/demo_executor.py
```

## 期待される動作

スクリプトを実行すると、3 つのモードが順次実行され、以下のような出力が生成されます：

```
========================================
[serial] Fibonacci benchmark (N=12 tasks, max_workers=6)
========================================
 80%|████████████████░░░░| ...

--- Summary ---
  mode=serial  success=07  fail=05  dup=0  pending=0  elapsed=0.90s

========================================
[thread] Fibonacci benchmark (N=12 tasks, max_workers=6)
========================================
 80%|████████████████░░░░| ...

--- Summary ---
  mode=thread  success=07  fail=05  dup=0  pending=0  elapsed=0.86s

========================================
[async] Fibonacci benchmark (N=12 tasks, max_workers=6)
========================================
 80%|████████████████░░░░| ...

--- Summary ---
  mode=async  success=07  fail=05  dup=0  pending=0  elapsed=0.01s
```

> **説明**：12 タスク中、5 つのエッジケース入力（`0`、`27`、`None`、`0`、`""`）が `ValueError` をトリガーし、リトライ後も最終的に失敗とマークされます。`success=07` は正常に実行された 7 つのフィボナッチタスクです。
> 3 つのモードすべてが `demo_utils` のイテレーティブ版フィボナッチ（O(n)）を使用しており、パフォーマンスの比較が可能です。

## 依存関係

- `celestialflow`（`TaskExecutor`、`TaskProgress`）
- `demo_utils`（`fibonacci`、`fibonacci_async`）
