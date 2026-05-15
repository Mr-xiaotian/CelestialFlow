# bench_requests.py ベンチマーク説明

> 📅 最終更新日: 2026/04/22

## 目的

`requests` ライブラリの異なる使用パターンにおける HTTP リクエスト性能を定量的に比較する：Session の有無、並行処理の有無、Session の共有粒度。CelestialFlow の HTTP 通信モジュール（Reporter、CelestialTree HTTP クライアント）に最適化のガイダンスを提供する。

## テスト内容

| シナリオ | Session の使用方法 | 並行処理 |
|----------|-------------------|---------|
| Sequential - no session | 毎回新規 `requests.get()` | なし |
| Sequential - with session | 単一 `Session` を再利用 | なし |
| Concurrent - no session | 毎回新規 `requests.get()` | 10 スレッド |
| Concurrent - per-thread session | スレッドごとに独立した `Session` | 10 スレッド |

- **ターゲット URL**：`https://httpbin.org/get`
- **リクエスト数**：`NUM_REQUESTS = 50`
- **タイムアウト**：`TIMEOUT = 30`

## 主要指標

各グループのリクエストについて、平均、中央値、標準偏差、最小値、最大値（ミリ秒）を出力。

## 発生し得る問題

1. **ネットワーク変動**：ターゲット `httpbin.org` はパブリックインターネット上にあり、遅延はローカルネットワークと国際リンク品質に影響される。単一実行の結果は再現性がない。
2. **コネクションプール未ウォームアップ**：`requests.Session` のコネクションプールは最初のリクエストで TCP/TLS 接続を確立する。最初の数リクエストの遅延は後続のリクエストより著しく高い場合がある。
3. **GIL の制約**：`ThreadPoolExecutor` のスレッドは Python の GIL に制約される。`requests` の CPU 集約的な部分（TLS ハンドシェイク、JSON 解析など）は真の並列化ができない。
4. **httpbin のレート制限**：頻繁なテストは httpbin のレート制限をトリガーし、429 やコネクションリセットが返される可能性がある。

## ベンチマーク結果（実測）

> 環境：Windows、Python 3.10、ターゲット https://httpbin.org/get、50 リクエスト、10 並行スレッド

| シナリオ | 平均 | 中央値 | 標準偏差 | 最小値 | 最大値 |
|----------|------|--------|---------|--------|--------|
| **Sequential - no session** | 1144.1 ms | 1059.7 ms | 169.0 ms | 991.9 ms | 1680.1 ms |
| **Sequential - with session** | **274.7 ms** | **166.8 ms** | 204.5 ms | 162.1 ms | 1047.7 ms |
| **Concurrent - no session** | 1795.4 ms | 1738.8 ms | 417.9 ms | 1180.0 ms | 2837.8 ms |
| **Concurrent - per-thread session** | 1734.6 ms | 1738.8 ms | 215.9 ms | 1154.4 ms | 2407.4 ms |

**主要な結論**：
- **Session の再利用が最大のパフォーマンス向上源**：逐次リクエストで Session を使用すると未使用時の **4.2 倍**高速（1144ms → 275ms）。TCP/TLS ハンドシェイクの繰り返しを回避
- **並行処理は追加の利点を提供しなかった**：本テストでは並行シナリオ（10 スレッド）の平均値はむしろ逐次より高かった。httpbin のパブリックネットワーク遅延とサーバー側処理がボトルネックとなり、クライアント側の並行処理では突破できなかった
- **スレッドごとの独立 Session は無意味**：並行シナリオでは、スレッドごとの Session は Session なしとほぼ同じ性能。高並行下でのコネクションプール競合によりコネクション再利用の優位性が相殺される
- CelestialFlow への示唆：Reporter と CelestialTree HTTP クライアントは `requests.Session` をグローバルに再利用すべき

## 実行方法

```bash
python bench/bench_requests.py
```

## 依存関係

- `requests`
