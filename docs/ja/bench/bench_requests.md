# bench_requests.py ベンチマーク説明

> 📅 最終更新日: 2026/06/22

## 目的

`requests` ライブラリの異なる使用モード（Session 使用有無、並行有無、Session 共有粒度）における HTTP リクエスト性能を定量比較する。CelestialFlow の HTTP 通信を含むモジュール（Reporter、CelestialTree HTTP クライアント）の最適化根拠を提供する。

## テスト内容

| シナリオ | Session 使用方法 | 並行 |
|----------|-----------------|------|
| Sequential - no session | 毎回新しい `requests.get()` | なし |
| Sequential - with session | 単一 `Session` を再利用 | なし |
| Concurrent - no session | 毎回新しい `requests.get()` | 10 スレッド |
| Concurrent - per-thread session | 各スレッド独立 `Session` | 10 スレッド |

- **デフォルトターゲット URL**：`http://127.0.0.1:5005/api/pull_server_state`
- **上書き方法**：`--url` パラメータまたは `CELESTIALFLOW_BENCH_URL` 環境変数
- **リクエスト数**：`NUM_REQUESTS = 50`
- **タイムアウト**：`TIMEOUT = 30`

## 主要指標

各グループのリクエストの mean、median、stdev、min、max（ミリ秒）を出力する。

## 発生し得る問題

1. **デフォルトターゲットはローカルサービス**：デフォルト URL は `http://127.0.0.1:5005/api/pull_server_state` である。公網の `httpbin.org` 等に変更した場合、遅延はネットワーク品質の影響を受け、単一結果に再現性はない。
2. **接続プール未ウォームアップ**：`requests.Session` の接続プールは初回リクエスト時に TCP/TLS 接続を確立する。最初の数リクエストの所要時間が後続より顕著に高くなる可能性がある。
3. **GIL 制限**：`ThreadPoolExecutor` 内のスレッドは Python GIL に制約され、`requests` の CPU 集約部分（TLS ハンドシェイク、JSON 解析等）は真の並列化ができない。
4. **公網ターゲットのレート制限**：`httpbin.org` 等の公網サービスを指した場合、頻繁なテストはレート制限をトリガーし、429 または接続リセットが返る可能性がある。

## ベンチマーク結果（実測）

### 履歴結果 - 公網 httpbin（日時未記録）

> 環境：Windows、Python 3.10、ターゲット https://httpbin.org/get、50 リクエスト、10 並行スレッド

| シナリオ | 平均所要時間 | 中央値 | 標準偏差 | 最小値 | 最大値 |
|----------|--------------|--------|----------|--------|--------|
| **Sequential - no session** | 1144.1 ms | 1059.7 ms | 169.0 ms | 991.9 ms | 1680.1 ms |
| **Sequential - with session** | **274.7 ms** | **166.8 ms** | 204.5 ms | 162.1 ms | 1047.7 ms |
| **Concurrent - no session** | 1795.4 ms | 1738.8 ms | 417.9 ms | 1180.0 ms | 2837.8 ms |
| **Concurrent - per-thread session** | 1734.6 ms | 1738.8 ms | 215.9 ms | 1154.4 ms | 2407.4 ms |

**主要な結論**：
- **Session 再利用が最大の利益源**：逐次リクエストにおいて、Session 使用は非使用より **4.2x** 高速（1144ms → 275ms）。繰り返しの TCP/TLS ハンドシェイクを回避するため
- **並行化は追加利益をもたらさなかった**：本テストでは、並行シナリオ（10 スレッド）の平均は逐次よりむしろ高かった。原因は httpbin の公網遅延とサーバー側処理がボトルネックとなり、クライアント側の並行化では突破できないため
- **スレッド毎の独立 Session は無意味**：並行シナリオでは、各スレッド独立 Session と非 Session の性能がほぼ同じ。接続再利用の利点が高並行下での接続プール競合によって相殺されるため
- CelestialFlow への示唆：Reporter と CelestialTree HTTP クライアントは `requests.Session` をグローバル再利用すべき

### 2026/06/16 - ローカル TaskWebServer

> 環境：Windows、ターゲット `http://127.0.0.1:5005/api/pull_server_state`、50 リクエスト、10 並行スレッド  
> 説明：今回のテストは修正された `bench_concurrent_with_session()` に基づき、真の「スレッドごとに 1 つの Session を再利用」を実現

| シナリオ | 平均所要時間 | 中央値 | 標準偏差 | 最小値 | 最大値 |
|----------|--------------|--------|----------|--------|--------|
| **Sequential - no session** | 20.7 ms | 20.6 ms | 11.6 ms | 5.5 ms | 64.7 ms |
| **Sequential - with session** | **5.8 ms** | **5.3 ms** | 3.1 ms | 4.5 ms | 26.6 ms |
| **Concurrent - no session** | 36.6 ms | 33.8 ms | 11.9 ms | 10.5 ms | 65.9 ms |
| **Concurrent - per-thread session** | 32.6 ms | 34.8 ms | 6.3 ms | 9.6 ms | 46.4 ms |

**今回の補足結論**：
- ローカルの安定したターゲットでは、**逐次 Session 再利用の利益が非常に顕著**で、平均所要時間は約 **72%** 低下（20.7ms → 5.8ms）
- 並行シナリオでは、**スレッドごとの Session 再利用**は依然として並行非 Session より優れるが、逐次シナリオより優位性が明らかに小さい。ローカルインターフェース処理とスレッドスケジューリングオーバーヘッドが主要な構成要素になっている
- 旧版の公網 `httpbin` 結果と比較して、ローカル結果は変動が小さく、コードレベルの接続再利用比較により適している
- 現在のスクリプトは CelestialFlow 自身の Web インターフェース上での HTTP クライアント戦略の検証により適しており、公網ネットワーク品質の測定には適さない

### 2026/06/16 - ローカル TaskWebServer（第 2 回再テスト）

> 環境：Windows、ターゲット `http://127.0.0.1:5005/api/pull_server_state`、50 リクエスト、10 並行スレッド

| シナリオ | 平均所要時間 | 中央値 | 標準偏差 | 最小値 | 最大値 |
|----------|--------------|--------|----------|--------|--------|
| **Sequential - no session** | 16.0 ms | 13.1 ms | 10.1 ms | 5.7 ms | 33.0 ms |
| **Sequential - with session** | **6.0 ms** | **5.8 ms** | 1.8 ms | 4.0 ms | 17.3 ms |
| **Concurrent - no session** | 37.3 ms | 37.1 ms | 10.5 ms | 8.2 ms | 55.5 ms |
| **Concurrent - per-thread session** | 33.2 ms | 35.6 ms | 6.9 ms | 10.4 ms | 39.8 ms |

**今回の補足結論**：
- 逐次シナリオでは `Session` 再利用が引き続き最も顕著な利益点で、平均所要時間は約 **62%** 低下（16.0ms → 6.0ms）
- 並行シナリオではスレッドごとの `Session` 再利用が依然として非 Session より優れるが、利益は逐次シナリオより明らかに小さい。ローカルインターフェース処理とスレッドスケジューリングがすでに主要な割合を占めている
- 同日の前回ローカル結果と比較して、全体の平均値はわずかに低下しており、この benchmark がサーバーのその時点の負荷とローカルマシンの状態に依然として敏感であることを示している

## 実行方法

```bash
python bench/bench_requests.py
```

## パラメータ調整

### リクエスト数と並行数の変更

`bench/bench_requests.py` の先頭で設定を変更：

```python
NUM_REQUESTS = 10          # 减少请求数，快速验证
# NUM_REQUESTS = 200       # 增加请求数，观察连接池预热后的稳态性能

CONCURRENT_WORKERS = 4     # 减少并发线程
# CONCURRENT_WORKERS = 50  # 高并发场景
```

### テストターゲットの変更

```bash
python bench/bench_requests.py --url http://127.0.0.1:5005/api/pull_server_state
```

または環境変数を使用：

```bash
set CELESTIALFLOW_BENCH_URL=http://127.0.0.1:5005/api/pull_server_state
python bench/bench_requests.py
```

### 特定シナリオのみをテスト

`if __name__ == "__main__":` 内で不要な呼び出しをコメントアウトするだけである：

```python
print("\n[1/4] Sequential - no session")
# print_stats("no session", bench_without_session(args.url, NUM_REQUESTS))

print("\n[2/4] Sequential - with session")
print_stats("with session", bench_with_session(args.url, NUM_REQUESTS))
```

修正後に実行：

```bash
python bench/bench_requests.py
```

## 依存関係

- `requests`
