# Funnel モジュール

> 📅 最終更新日: 2026/04/22

Funnel モジュールは CelestialFlow のキュー通信インフラストラクチャを提供し、Persistence モジュールにおける `LogSpout`/`LogInlet` および `FailSpout`/`FailInlet` の基底クラスです。

## モジュール概要

Funnel モジュールは Spout/Inlet（出口/入口）パターンを採用し、マルチプロセス安全な非同期キュー通信を実現します。Inlet はレコードをキューに書き込む役割を担い、Spout はバックグラウンドスレッドでキューからレコードを読み取り処理します。

## ファイル説明

### コアコンポーネント

1. **core_spout.py** (`BaseSpout`)
   - **役割**: すべての出口クラスの基底クラスで、バックグラウンドスレッドのリスニングとキュー消費機能を提供します
   - **主な機能**: バックグラウンドスレッドリスニング、グレースフルな起動/停止、マルチプロセス安全なキュー

2. **core_inlet.py** (`BaseInlet`)
   - **役割**: すべての入口クラスの基底クラスで、キューへの書き込み機能を提供します
   - **主な機能**: キュー書き込みのカプセル化

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

## モジュールの関連

### 外部との関連
- **Persistence モジュールとの関連**: `LogSpout`/`LogInlet`、`FailSpout`/`FailInlet`、`SuccessSpout` はすべてこのモジュールの基底クラスを継承しています
- **Runtime モジュールとの関連**: 停止シグナルとして `TerminationSignal` を使用し、キューのクリーンアップに `cleanup_mpqueue` を使用します
