# bench_requests.py ベンチマーク説明

> 📅 最終更新日: 2026/04/22

## 目的

`requests` ライブラリの異なる使用モード（Session 使用有無、並行有無、Session 共有粒度）における HTTP リクエスト性能を定量比較する。CelestialFlow の HTTP 通信を含むモジュール（Reporter、CelestialTree HTTP クライアント）の最適化根拠を提供する。

## テスト内容

| シナリオ | Session 使用方法 | 並行 |
|----------|-----------------|------|
| Sequential - no session | 毎回新しい `requests.get()` | なし |
| Sequential - with session | 単一 `Session` を再利用 | なし |
| Concurrent - no session | 毎回新しい `requests.get()` | 10 スレッド |
| Concurrent - per-thread session | 各スレッド独立 `Session` | 10 スレッド |

- **ターゲット URL**：`https://httpbin.org/get`
- **リクエスト数**：`NUM_REQUESTS = 50`
- **タイムアウト**：`TIMEOUT = 30`

## 主要指標

各グループのリクエストの mean、median、stdev、min、max（ミリ秒）を出力。

## 発生し得る問題

1. **ネットワーク変動**：ターゲット `httpbin.org` はパブリックネットワーク上にあり、遅延はローカルネットワークと国際リンク品質の影響を受け、単一結果に再現性はない。
2. **接続プール未ウォームアップ**：`requests.Session` の接続プールは初回リクエスト時に TCP/TLS 接続を確立する。最初の数リクエストの所要時間が後続より顕著に高くなる可能性がある。
3. **GIL 制限**：`ThreadPoolExecutor` 内のスレッドは Python GIL に制約され、`requests` の CPU 集約部分（TLS ハンドシェイク、JSON 解析等）は真の並列化ができない。
4. **httpbin レート制限**：頻繁なテストは httpbin のレート制限をトリガーし、429 または接続リセットが返る可能性がある。

## ベンチマーク結果（実測）

> 環境：Windows、Python 3.10、ターゲット https://httpbin.org/get、50 リクエスト、10 並行スレッド

| シナリオ | 平均所要時間 | 中央値 | 標準偏差 | 最小値 | 最大値 |
|----------|-------------|--------|---------|--------|--------|
| **Sequential - no session** | 1144.1 ms | 1059.7 ms | 169.0 ms | 991.9 ms | 1680.1 ms |
| **Sequential - with session** | **274.7 ms** | **166.8 ms** | 204.5 ms | 162.1 ms | 1047.7 ms |
| **Concurrent - no session** | 1795.4 ms | 1738.8 ms | 417.9 ms | 1180.0 ms | 2837.8 ms |
| **Concurrent - per-thread session** | 1734.6 ms | 1738.8 ms | 215.9 ms | 1154.4 ms | 2407.4 ms |

**主要な結論**：
- **Session 再利用が最大の利益源**：逐次リクエストにおいて、Session 使用は非使用より **4.2x** 高速（1144ms → 275ms）。繰り返しの TCP/TLS ハンドシェイクを回避するため
- **並行化は追加利益をもたらさなかった**：本テストでは、並行シナリオ（10 スレッド）の平均は逐次よりむしろ高かった。原因は httpbin のパブリックネットワーク遅延とサーバー側処理がボトルネックとなり、クライアント側の並行化では突破できないため
- **スレッド毎の独立 Session は無意味**：並行シナリオでは、各スレッド独立 Session と非 Session の性能がほぼ同じ。接続再利用の利点が高並行下での接続プール競合によって相殺されるため
- CelestialFlow への示唆：Reporter と CelestialTree HTTP クライアントは `requests.Session` をグローバル再利用すべき

## 実行方法

```bash
python bench/bench_requests.py
```

## パラメータ調整

### リクエスト数と並行数の変更

`bench/bench_requests.py` の先頭で設定を変更：

```python
NUM_REQUESTS = 10          # リクエスト数を減らして素早く検証
# NUM_REQUESTS = 200       # リクエスト数を増やし、接続プールウォームアップ後の定常性能を観察

CONCURRENT_WORKERS = 4     # 並行スレッド数を削減
# CONCURRENT_WORKERS = 50  # 高並行シナリオ
```

### テストターゲットの変更

```python
TEST_URL = "https://httpbin.org/get"             # デフォルトのパブリックターゲット
# TEST_URL = "http://localhost:8000/api/health"  # ローカルテストサービス
```

### 特定シナリオのみをテスト

```python
if __name__ == "__main__":
    print("\n[1/4] Sequential - no session")
    # test_without_session(...)             # 非 Session テストをスキップ

    print("\n[2/4] Sequential - with session")  # Session 再利用のみテスト
    test_with_session(TEST_URL, NUM_REQUESTS)
    # ...
```

修正後に実行：

```bash
python bench/bench_requests.py
```

## 依存関係

- `requests`
