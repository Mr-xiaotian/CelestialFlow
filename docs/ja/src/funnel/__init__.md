# Funnel モジュール

> 📅 最終更新日: 2026/06/18

Funnel モジュールは CelestialFlow のキュー通信インフラストラクチャを提供し、Persistence モジュールの `LogSpout`/`LogInlet` や `FallbackSpout`/`FallbackInlet` の基底クラスです。

永続化の下位基盤としてだけでなく、`TaskGraph` / `TaskStage` から切り離して軽量な producer-consumer パイプラインを単独で構築することもできます。最小限の動作サンプルは [demo_funnel.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/demo/demo_funnel.md) を参照してください。

## エクスポートシンボル

| エクスポートシンボル | ソースモジュール | 説明 |
|---------|---------|------|
| `BaseInlet` | `core_inlet` | すべての入口クラスの基底クラス。キュー書き込み機能を提供 |
| `BaseSpout` | `core_spout` | すべての出口クラスの基底クラス。バックグラウンドスレッドによる監視とキュー消費機能を提供 |

## ファイル説明

### コアコンポーネント

1. **core_inlet.py** (`BaseInlet`)
   - **役割**: すべての入口クラスの基底クラス。キュー書き込み機能を提供
   - **主要機能**: キュー書き込みのカプセル化 (`_funnel`)

2. **core_spout.py** (`BaseSpout`)
   - **役割**: すべての出口クラスの基底クラス。バックグラウンドスレッドによる監視とキュー消費機能を提供
   - **主要機能**: バックグラウンドスレッド監視、ライフサイクルフック、グレースフルスタート/ストップ

## 継承関係

```mermaid
classDiagram
    class BaseSpout {
        +Queue queue
        +Thread _thread
        +start() None
        +stop() None
        +get_queue() Queue
        +_before_start() None
        +_handle_record(record) None
        +_after_stop() None
    }
    class BaseInlet {
        +Any queue
        +_funnel(record) None
    }
    class LogSpout {
    }
    class FallbackSpout {
    }
    class LogInlet {
    }
    class FallbackInlet {
    }

    BaseSpout <|-- LogSpout
    BaseSpout <|-- FallbackSpout
    BaseInlet <|-- LogInlet
    BaseInlet <|-- FallbackInlet
```

## モジュール連携

### 外部連携
- **Persistence モジュールとの連携**: `LogSpout`/`LogInlet`、`FallbackSpout`/`FallbackInlet` はいずれも本モジュールの基底クラスを継承
- **Runtime モジュールとの連携**: 停止シグナルとして `TerminationSignal` を使用、サブクラスが必ずオーバーライドすべき例外型として `CelestialFlowError` を使用

## 使用例

以下は `BaseInlet` と `BaseSpout` の基本的な使用パターンです。

### BaseSpout + BaseInlet 連携

```python
from celestialflow.funnel import BaseSpout, BaseInlet

# 1. カスタム Spout：受信したレコードをコンソールに出力
class PrintSpout(BaseSpout):
    def _handle_record(self, record):
        print(f"Spout 受信: {record}")

# 2. Spout と Inlet を作成
spout = PrintSpout()
inlet = BaseInlet(spout.get_queue())

# 3. バックグラウンド監視スレッドを起動
spout.start()

# 4. Inlet 経由でレコードを送信
inlet._funnel("Hello, World!")
inlet._funnel({"key": "value"})
inlet._funnel(42)

# 5. Spout を停止
spout.stop()
print("Spout が停止しました")
```

### BaseSpout のカスタムフックを使用

```python
from celestialflow.funnel import BaseSpout

class FileSpout(BaseSpout):
    def __init__(self, filename: str):
        super().__init__()
        self.filename = filename

    def _before_start(self):
        print(f"ファイルを開く: {self.filename}")

    def _handle_record(self, record):
        print(f"レコード処理: {record}")

    def _after_stop(self):
        print(f"ファイルを閉じる: {self.filename}")

spout = FileSpout("records.log")
spout.start()
spout.get_queue().put("record1")
spout.get_queue().put("record2")
spout.stop()
```
