# demo_structure.py デモ説明

> 📅 最終更新日: 2026/04/22

## 目的

`core_structure.py` で事前定義された多様なグラフ構造（DAG および循環グラフ）を実演し、チェーン、クロス、グリッド、ループ、ホイール、完全グラフなど、複数のトポロジーにおける CelestialFlow の構築と実行方法を紹介します。

## デモ構造

### DAG（有向非巡回グラフ）

| 関数 | 構造 | 説明 |
|------|------|------|
| `demo_chain` | TaskChain | 5ノードの線形チェーン、プロセスモード |
| `demo_forest` | TaskGraph | 2つの独立したツリー型 DAG が共存 |
| `demo_cross` | TaskCross | 3層クロス構造（3->1->3） |
| `demo_network` | TaskCross | 多層多分岐ネットワーク（2->3->1） |
| `demo_star` | TaskCross | 中心ノードが複数のエッジノードを指す |
| `demo_fanin` | TaskCross | 複数のソースノードが1つのマージノードに集約 |
| `demo_grid` | TaskGrid | 4x4 プロセスグリッド、staged スケジューリング |

### 循環グラフ

| 関数 | 構造 | 説明 |
|------|------|------|
| `demo_loop` | TaskLoop | 3ノード閉ループ、自己ロック構造 |
| `demo_wheel` | TaskWheel | 中心ノード + 4つのリングノード |
| `demo_complete` | TaskComplete | 3ノード完全グラフ、ペアワイズ接続 |

## 主要設定

- DAG 構造：`stage_mode="process"`、`execution_mode="thread"`
- `demo_grid`：`staged` スケジューリングモード（レイヤーごとの実行）を使用
- 循環グラフ：`put_termination_signal=False`（外部からの停止制御を推奨）
- すべてのデモで `Reporter` と `CelestialTree` を有効化

## 発生しうる問題

1. **循環グラフは自動停止しません**：`demo_loop`、`demo_complete` などは `put_termination_signal=False` を使用しており、プロセスを手動で終了するまで継続的にループします。
2. **プロセス起動オーバーヘッド**：Windows 上では `stage_mode="process"` のノードが多数ある場合、起動が遅くなります。`demo_grid`（16プロセス）は初期化に数十秒かかる場合があります。
3. **スリープ遅延の蓄積**：`add_one_sleep` には1秒のスリープが含まれており、20タスク x 複数ノード = 長い合計実行時間となります。
4. **アサーションなし**：フレームワークが起動・実行できることのみを検証し、結果の値は確認しません。

## 実行方法

```bash
python demo/demo_structure.py
```

## 依存関係

- `celestialflow`（`TaskGraph`、`TaskChain`、`TaskCross`、`TaskGrid`、`TaskLoop`、`TaskWheel`、`TaskComplete`、`TaskStage`）
- `demo_utils`
- `python-dotenv`
- 外部サービス：CelestialTree（オプション）、Reporter（オプション）
