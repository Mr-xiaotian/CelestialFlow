# Funnel モジュール

> 📅 最終更新日: 2026/05/09

Funnel モジュールは CelestialFlow のキュー通信インフラストラクチャを提供し、Persistence モジュールにおける `LogSpout`/`LogInlet` および `FailSpout`/`FailInlet` の基底クラスです。

## モジュール概要

Funnel モジュールは Spout/Inlet（出口/入口）パターンを採用し、マルチプロセス安全な非同期キュー通信を実現しています。Inlet はレコードをキューに書き込み、Spout はバックグラウンドスレッドでキューからレコードを読み取り処理します。

## ファイル説明

### コアコンポーネント

1. **core_spout.py** (`BaseSpout`)
   - **役割**: すべての Spout クラスの基底クラス。バックグラウンドスレッド監視とキュー消費機能を提供
   - **主要機能**: バックグラウンドスレッド監視、グレースフルな起動/停止、マルチプロセス安全なキュー

2. **core_inlet.py** (`BaseInlet`)
   - **役割**: すべての Inlet クラスの基底クラス。キュー書き込み機能を提供
   - **主要機能**: キュー書き込みのカプセル化

## 継承関係

```
BaseSpout (funnel/core_spout.py)
├── LogSpout (persistence/core_log.py)
├── FailSpout (persistence/core_fail.py)
└── SuccessSpout (persistence/core_success.py)

BaseInlet (funnel/core_inlet.py)
├── LogInlet (persistence/core_log.py)
└── FailInlet (persistence/core_fail.py)
```

## モジュール関連

### 外部関連
- **Persistence モジュール**: `LogSpout`/`LogInlet`、`FailSpout`/`FailInlet`、`SuccessSpout` はすべて本モジュールの基底クラスを継承
- **Runtime モジュール**: `TerminationSignal` を停止シグナルとして使用
