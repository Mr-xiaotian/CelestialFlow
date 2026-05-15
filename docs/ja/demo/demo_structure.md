# demo_structure.py デモ説明

> 📅 最終更新日: 2026/05/15

## 目的

`core_structure.py` で事前定義された複数のグラフ構造（DAG および循環グラフ）をデモンストレーションし、チェーン、クロス、グリッド、ループ、ホイール、完全グラフなど、さまざまなトポロジーでの CelestialFlow の構築と実行方法を示します。

## デモ構造

### DAG（有向非巡回グラフ）

| 関数 | 構造 | 説明 |
|------|------|------|
| `demo_chain` | TaskChain | 5ノード線形チェーン、スレッドモード |
| `demo_forest` | TaskGraph | 2つの独立したツリー型 DAG の共存 |
| `demo_cross` | TaskCross | 3層クロス構造（3→1→3） |
| `demo_network` | TaskCross | 多層多分岐ネットワーク（2→3→1） |
| `demo_star` | TaskCross | 中心ノードが複数のエッジノードを指す |
| `demo_fanin` | TaskCross | 複数のソースノードが1つのマージノードに収束 |
| `demo_grid` | TaskGrid | 4×4 スレッドグリッド、staged スケジューリング |

### 循環グラフ

| 関数 | 構造 | 説明 |
|------|------|------|
| `demo_loop` | TaskLoop | 3ノード閉ループ、セルフロック構造 |
| `demo_wheel` | TaskWheel | 中心ノード + 4つのリングノード |
| `demo_complete` | TaskComplete | 3ノード完全グラフ、全結合 |
| `demo_multi_cycle` | TaskGraph | マルチサイクル相互接続グラフ: 3組の2ノードサイクル（A/B/C）、A2 が B1 と C1 に分岐 |

## 主要設定

- DAG 構造: `stage_mode="thread"`、`execution_mode="thread"`
- `demo_grid`: `staged` スケジューリングモードを使用（レイヤーごとの実行）
- 循環グラフ: `put_termination_signal=False`（外部からの停止制御を推奨）
- すべてのデモで `Reporter` と `CelestialTree` を有効化

## 起こりうる問題

1. **循環グラフは自動停止しない**: `demo_loop`、`demo_complete` などは `put_termination_signal=False` を使用し、プロセスを手動で終了するまで継続的にループします。
2. **sleep 遅延の蓄積**: `add_one_sleep` には1秒の sleep が含まれ、20タスク × 複数ノード = 長い合計所要時間となります。
3. **アサーションなし**: フレームワークが起動・実行できることのみを検証し、結果の数値は確認しません。

## 実行方法

```bash
python demo/demo_structure.py
```

## 依存関係

- `celestialflow`（`TaskGraph`、`TaskChain`、`TaskCross`、`TaskGrid`、`TaskLoop`、`TaskWheel`、`TaskComplete`、`TaskStage`）
- `demo_utils`
- `python-dotenv`
- 外部サービス: CelestialTree（オプション）、Reporter（オプション）
