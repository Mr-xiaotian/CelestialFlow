# bench_requests.py ベンチマーク説明

> 📅 最終更新日: 2026/04/22

## 目標

`requests` ライブラリの異なる使用パターンにおける HTTP リクエスト性能を定量的に比較します：Session の使用有無、並行処理の有無、Session の共有粒度。CelestialFlow で HTTP 通信を行うモジュール（Reporter、CelestialTree HTTP クライアント）の最適化の根拠を提供します。

## テスト内容

| シナリオ | Session 使用方法 | 並行性 |
|---------|----------------|--------|
| Sequential - no session | 毎回 `requests.get()` を新規作成 | なし |
| Sequential - with session | 単一の `Session` を再利用 | なし |
| Concurrent - no session | 毎回 `requests.get()` を新規作成 | 10 スレッド |
| Concurrent - per-thread session | 各スレッドで独立した `Session` | 10 スレッド |

- **対象 URL**：`https://httpbin.org/get`
- **リクエスト数**：`NUM_REQUESTS = 50`
- **タイムアウト**：`TIMEOUT = 30`

## 主要指標

各グループの平均値、中央値、標準偏差、最小値、最大値（ミリ秒単位）を出力します。

## 発生しうる問題

1. **ネットワーク変動**：対象の `httpbin.org` はパブリックインターネット上にあります。遅延はローカルネットワーク品質や国際回線の状態に影響され、単回の結果は再現性がありません。
2. **コネクションプール未ウォームアップ**：`requests.Session` のコネクションプールは最初のリクエスト時に TCP/TLS 接続を確立します。最初の数リクエストは後続のリクエストより大幅に遅くなる場合があります。
3. **GIL 制限**：`ThreadPoolExecutor` のスレッドは Python GIL に制約されます。`requests` の CPU 集約的な部分（TLS ハンドシェイク、JSON パースなど）は真に並列実行できません。
4. **httpbin レート制限**：頻繁なテストにより httpbin のレートリミッターがトリガーされ、429 レスポンスや接続リセットが返される場合があります。

## ベンチマーク結果（実測）

> 環境：Windows、Python 3.10、対象 https://httpbin.org/get、50 リクエスト、10 並行スレッド

| シナリオ | 平均所要時間 | 中央値 | 標準偏差 | 最小値 | 最大値 |
|---------|------------|--------|---------|--------|--------|
| **Sequential - no session** | 1144.1 ms | 1059.7 ms | 169.0 ms | 991.9 ms | 1680.1 ms |
| **Sequential - with session** | **274.7 ms** | **166.8 ms** | 204.5 ms | 162.1 ms | 1047.7 ms |
| **Concurrent - no session** | 1795.4 ms | 1738.8 ms | 417.9 ms | 1180.0 ms | 2837.8 ms |
| **Concurrent - per-thread session** | 1734.6 ms | 1738.8 ms | 215.9 ms | 1154.4 ms | 2407.4 ms |

**主要な結論**：
- **Session の再利用が最大の性能向上要因**：逐次リクエストにおいて、Session の使用は未使用時と比較して **4.2x** 高速です（1144ms -> 275ms）。TCP/TLS ハンドシェイクの繰り返しを回避するためです
- **並行処理は追加の利点をもたらしませんでした**：このテストでは、並行シナリオ（10 スレッド）の平均値は逐次よりむしろ高くなりました。httpbin のパブリックネットワーク遅延とサーバー側の処理がボトルネックとなり、クライアント側の並行性では突破できないためです
- **スレッドごとの独立 Session は無意味**：並行シナリオでは、スレッドごとの独立 Session は Session なしとほぼ同等の性能です。接続再利用の優位性が高並行性下のコネクションプール競合によって相殺されるためです
- CelestialFlow への示唆：Reporter と CelestialTree HTTP クライアントは `requests.Session` をグローバルに再利用すべきです

## 実行方法

```bash
python bench/bench_requests.py
```

## 依存関係

- `requests`
