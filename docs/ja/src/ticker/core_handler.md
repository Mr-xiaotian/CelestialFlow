# src/celestialflow/ticker/core_handler.py

> 📅 最終更新日: 2026/11/13

`core_handler.py` はすべての拍ハンドラの基底クラス `TickHandler` と、モジュールレベルの検証関数 `validate_tick_period()` を定義します。これは 3 つのことを規定します：

1. あるハンドラが**何拍ごとに**トリガーされるか（`tick_period`）；
2. 現在の拍が**ヒットするか**（`should_tick()`）；
3. コールバックが例外を送出したときに**どう処理するか**（`handle_exception()`）。

## TickHandler

```python
class TickHandler:
    tick_period: int = 1

    def should_tick(self, event: TickEvent) -> bool: ...
    def set_tick_period(self, tick_period: int) -> None: ...
    def on_tick(self, event: TickEvent) -> None: ...
    def handle_exception(self, exception: Exception) -> None: ...
```

| メンバー | 説明 |
|------|------|
| `tick_period` | クラス属性。デフォルトは `1`（毎拍トリガー）。サブクラスで上書きでき、実行時に `set_tick_period()` でも変更可能 |
| `should_tick(event)` | フィルタ式：`(event.seq - 1) % self.tick_period == 0` |
| `set_tick_period(tick_period)` | 新しい拍数を設定。`1` 未満なら `ConfigurationError` を送出 |
| `on_tick(event)` | 拍コールバック。デフォルトは空実装。サブクラスはこれをオーバーライドするだけでよい |
| `handle_exception(exception)` | コールバック例外処理。デフォルトは `traceback.print_exception()` で標準エラーへ出力 |

### フィルタ式

```text
ヒット条件：(seq - 1) % tick_period == 0
```

| `tick_period` | ヒットする `seq` | 実際の周期（`Ticker.interval = 1.0`） |
|:-------------:|:------------:|:----------------------------------:|
| 1 | 1, 2, 3, 4, 5, 6, … | 1 秒 |
| 2 | 1, 3, 5, 7, 9, … | 2 秒 |
| 3 | 1, 4, 7, 10, … | 3 秒 |
| 5 | 1, 6, 11, 16, … | 5 秒 |

> 1 拍目は必ずヒットするため、ハンドラが動作を開始するために余分に 1 周期待つ必要はありません。位相のアンカーは `seq == 1` に固定されています。

### 実行時の速度調整

`TickHub` と `Ticker` は**各拍の配信前**にハンドラの現在の `tick_period` を再読み取りするため、次のように動作します：

```python
handler.set_tick_period(5)   # 次の拍から有効。Ticker の再起動は不要
```

フィルタは引き続き `seq` を基準とするため、変更後は位相が `seq == 1` に再固定されます。例えば `tick_period=3` から `5` に変更すると、以降のヒットは `1, 6, 11, …` となり、現在の番号から累加し続けるわけではありません。

> `tick_period` に直接代入することもできますが、その場合は**検証が実行されません**。`0` を代入すると、`should_tick()` が剰余のゼロ除算により `ZeroDivisionError` を送出します。常に `set_tick_period()` を使用することを推奨します。

### 例外処理の契約

| シナリオ | 挙動 |
|------|------|
| `on_tick()` が例外を送出（`TickHub` が配信） | `TickHub` が捕捉し、そのハンドラ自身の `handle_exception()` を呼び出す |
| `on_tick()` が例外を送出（ハンドラが `Ticker` のルートハンドラ） | `Ticker` が捕捉し、そのハンドラ自身の `handle_exception()` を呼び出す |
| `handle_exception()` 自身がさらに送出（ハンドラが hub 内） | 例外は上位の hub の `handle_exception()` に伝播してフォールバック処理 |
| `handle_exception()` 自身がさらに送出（ハンドラが ticker のルートハンドラ） | 例外が脱出し、バックグラウンド拍スレッドを終了させる |
| デフォルト実装 | `traceback.print_exception(exception)`。配信は終了しない |

例外を出力するのではなく収集したい場合は、`handle_exception()` をオーバーライドします：

```python
class CollectingHandler(TickHandler):
    def __init__(self) -> None:
        self.errors: list[Exception] = []

    def handle_exception(self, exception: Exception) -> None:
        self.errors.append(exception)
```

## validate_tick_period

```python
def validate_tick_period(handler: TickHandler) -> None: ...
```

`handler.tick_period >= 1` を検証し、そうでなければ送出します：

```text
ConfigurationError: tick_period must be a positive integer, got <value>
```

呼び出し元：

- `TickHub.add_handler()`：子ハンドラ登録時に検証；
- `Ticker.__init__()`：構築時にルートハンドラを検証。

> この関数は `celestialflow.ticker.__init__` から再エクスポートされていません。カスタムのアセンブリコードで再利用する場合は `from celestialflow.ticker.core_handler import validate_tick_period` としてください。

## 使用例

以下の例はバックグラウンドスレッドを起動せず、`should_tick()` と実行時の速度調整を直接検証します：

```python
from celestialflow.ticker import TickEvent, TickHandler


class RecordingHandler(TickHandler):
    tick_period = 3

    def __init__(self) -> None:
        self.hits: list[int] = []

    def on_tick(self, event: TickEvent) -> None:
        self.hits.append(event.seq)


def make_event(seq: int) -> TickEvent:
    return TickEvent(
        seq=seq,
        interval=1.0,
        scheduled_at=float(seq - 1),
        fired_at=float(seq - 1),
        wall_time=0.0,
        drift=0.0,
        skipped=0,
    )


handler = RecordingHandler()
for seq in range(1, 8):
    event = make_event(seq)
    if handler.should_tick(event):
        handler.on_tick(event)

print(handler.hits)  # [1, 4, 7]

handler.set_tick_period(2)
print([seq for seq in range(1, 7) if handler.should_tick(make_event(seq))])
# [1, 3, 5]
```

## 注意事項

1. **ハンドラは自前でカウント不要**：`TickHub` / `Ticker` は `on_tick()` を呼ぶ前に `should_tick()` のフィルタを完了しています。
2. **`tick_period` は拍数であり秒数ではない**：実際の秒数 = `Ticker.interval × tick_period`。
3. **速度調整は即時有効**：配信経路が毎拍属性を再読み取りするため、タイマーの再起動は不要です。
4. **例外は握り潰さない**：デフォルトは出力のみです。レポートや統計が必要な場合は `handle_exception()` をオーバーライドしてください。そのコールバック自身が例外を送出すると拍スレッドが終了する可能性があるため注意してください。
5. **基底クラスのコールバックはすべて空実装**：`TickHandler` を継承したら `on_tick()` をオーバーライドするだけで十分です。
