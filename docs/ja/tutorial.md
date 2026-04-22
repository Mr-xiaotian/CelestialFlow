# チュートリアル（Tutorial）：画像クローラーの構築

> 📅 最終更新日: 2026/04/22

このチュートリアルでは、完全な実践プロジェクト — **Baidu画像クローラー** — を通じて、CelestialFlowの使い方をゼロから学びます。

## プロジェクトの目標

Baidu画像の検索結果をクロールし、指定したキーワードの画像をローカルにダウンロードします。以下の方法を学びます：
1. タスクフローを分析し、分解する
2. 各ステージの処理関数を記述する
3. タスクグラフを組み立てて実行する
4. Web UIで実行状態を監視する

---

## ステップ1：タスクの分析と分解

コーディングを始める前に、クローラーの実行フローを分析する必要があります：

```
ユーザーがキーワードを入力 → 検索ページ → 画像リストの解析 → 画像のダウンロード → ファイルの保存
```

### タスク階層の設計

| 階層 | 機能 | 入力 | 出力 |
|------|------|------|------|
| **Layer 1: 検索** | 検索結果ページを取得 | キーワード | ページHTML |
| **Layer 2: 解析** | 画像URLリストを抽出 | HTML | 画像URLリスト |
| **Layer 3: ダウンロード** | 画像コンテンツをダウンロード | 画像URL | 画像バイナリデータ |
| **Layer 4: 保存** | ローカルに保存 | 画像データ | ファイルパス |

### タスクグラフの構造

```mermaid
flowchart LR
    subgraph TG[画像クローラー タスクグラフ]
        direction LR
        
        S1[ページ検索]
        S2[画像解析]
        S3[画像ダウンロード]
        S4[ファイル保存]
        
        S1 --> S2
        S2 --> S3
        S3 --> S4
    end
    
    style TG fill:#e8f2ff,stroke:#6b93d6,stroke-width:2px
    classDef blueNode fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px;
    class S1,S2,S3,S4 blueNode;
```

---

## ステップ2：処理関数の記述

まず各ステージの処理関数を記述し、個別にテスト・検証します。

### 2.1 ページ検索

```python
import requests
from urllib.parse import quote

def search_images(keyword: str) -> str:
    """
    キーワードでBaidu画像を検索し、ページHTMLを返します。
    
    :param keyword: 検索キーワード
    :return: ページHTMLコンテンツ
    """
    url = f"https://image.baidu.com/search/index?tn=baiduimage&word={quote(keyword)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.text

# 単体テスト
if __name__ == "__main__":
    html = search_images("猫咪")
    print(f"{len(html)} 文字のHTMLを取得しました")
```

### 2.2 画像URLの解析

```python
import re
import json

def parse_image_urls(html: str) -> list[str]:
    """
    HTMLから画像URLリストを解析します。
    
    :param html: ページHTML
    :return: 画像URLリスト
    """
    # Baidu画像のデータはJavaScriptに埋め込まれています
    pattern = r'"hoverURL":"(https?://[^"]+)"'
    urls = re.findall(pattern, html)
    # エスケープ文字の処理
    urls = [url.replace("\\/", "/") for url in urls]
    return urls[:20]  # 数量を制限

# 単体テスト
if __name__ == "__main__":
    html = search_images("猫咪")
    urls = parse_image_urls(html)
    print(f"{len(urls)} 個の画像URLを解析しました")
    for url in urls[:3]:
        print(f"  - {url}")
```

### 2.3 画像のダウンロード

```python
import time

def download_image(url: str) -> bytes | None:
    """
    画像コンテンツをダウンロードします。
    
    :param url: 画像URL
    :return: 画像バイナリデータ、失敗時はNone
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://image.baidu.com/"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"ダウンロード失敗: {url}, エラー: {e}")
        return None

# 単体テスト
if __name__ == "__main__":
    html = search_images("猫咪")
    urls = parse_image_urls(html)
    if urls:
        data = download_image(urls[0])
        if data:
            print(f"ダウンロード成功、サイズ: {len(data)} バイト")
```

### 2.4 ファイルの保存

```python
import os
import hashlib

def save_image(image_data: bytes, keyword: str) -> str:
    """
    画像をローカルに保存します。
    
    :param image_data: 画像バイナリデータ
    :param keyword: キーワード（ディレクトリ作成に使用）
    :return: 保存されたファイルパス
    """
    # ディレクトリの作成
    save_dir = os.path.join("images", keyword)
    os.makedirs(save_dir, exist_ok=True)
    
    # データハッシュをファイル名として使用
    file_hash = hashlib.md5(image_data).hexdigest()[:12]
    file_path = os.path.join(save_dir, f"{file_hash}.jpg")
    
    # 重複ダウンロードを回避
    if not os.path.exists(file_path):
        with open(file_path, "wb") as f:
            f.write(image_data)
    
    return file_path

# 単体テスト
if __name__ == "__main__":
    html = search_images("猫咪")
    urls = parse_image_urls(html)
    if urls:
        data = download_image(urls[0])
        if data:
            path = save_image(data, "猫咪")
            print(f"保存成功: {path}")
```

---

## ステップ3：タスクグラフの組み立て

処理関数の検証が完了したら、それぞれを`TaskStage`に割り当て、`TaskGraph`で構造を組織します。

### 3.1 ノードの作成

```python
from celestialflow import TaskStage, TaskSplitter

# 検索ステージ：キーワードを入力、HTMLを出力
stage_search = TaskStage(
    func=search_images,
    execution_mode="serial",  # キーワードは1つだけなので、シリアルで十分
    max_retries=2,
)

# 解析ステージ：HTMLを入力、複数の画像URLを出力（分割が必要）
# URLリストを分割するためのカスタムSplitterが必要
class URLSplitter(TaskSplitter):
    """URLリストを複数の独立したタスクに分割します。"""
    
    def _split(self, html: str):
        urls = parse_image_urls(html)
        print(f"{len(urls)} 個の画像URLを解析しました")
        return tuple(urls)

stage_parse = URLSplitter()

# ダウンロードステージ：URLを入力、画像データを出力
stage_download = TaskStage(
    func=download_image,
    execution_mode="thread",  # ネットワークIO集約型なのでスレッドプールを使用
    worker_limit=10,          # 10枚同時ダウンロード
    max_retries=3,
)

# 保存ステージ：画像データを入力、ファイルパスを出力
stage_save = TaskStage(
    func=lambda data: save_image(data, "猫咪") if data else None,
    execution_mode="serial",
    enable_duplicate_check=False,  # 重複データの保存を許可（リトライ用）
)
```

### 3.2 タスクグラフの構築

```python
from celestialflow import TaskGraph

# タスクグラフの作成
graph = TaskGraph(schedule_mode="eager", log_level="SUCCESS")

# ノードの設定
graph.set_stages(root_stages=[stage_search], stages=[stage_parse, stage_download, stage_save])

# ノード間の接続関係を設定
graph.connect([stage_search], [stage_parse])
graph.connect([stage_parse], [stage_download])
graph.connect([stage_download], [stage_save])
```

### 3.3 Web監視の起動（オプション）

```python
# Web監視を有効化
graph.set_reporter(True, host="127.0.0.1", port=5005)
```

Webサービスを起動します：
```bash
celestialflow-web --port 5005
```

http://localhost:5005 にアクセスしてリアルタイムの状態を確認できます。

### 3.4 タスクグラフの実行

```python
# 初期タスクの準備
init_tasks = {
    stage_search.get_tag(): ["猫咪", "小狗", "风景"]
}

# 開始
print("画像のクロールを開始します...")
graph.start_graph(init_tasks)

# 統計の取得
print(f"成功: {graph.get_graph_summary().get('total_succeeded', 0)}")
print(f"失敗: {graph.get_graph_summary().get('total_failed', 0)}")
```

---

## ステップ4：完全なコード

すべてのコードを1つのファイルに統合します：

```python
# crawler.py
import os
import re
import hashlib
import requests
from urllib.parse import quote

from celestialflow import (
    TaskStage, 
    TaskSplitter, 
    TaskGraph,
)

# ========== 処理関数 ==========

def search_images(keyword: str) -> str:
    """Baidu画像を検索します。"""
    url = f"https://image.baidu.com/search/index?tn=baiduimage&word={quote(keyword)}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.text

def parse_image_urls(html: str) -> list[str]:
    """画像URLを解析します。"""
    pattern = r'"hoverURL":"(https?://[^"]+)"'
    urls = re.findall(pattern, html)
    return [url.replace("\\/", "/") for url in urls][:20]

def download_image(url: str) -> bytes | None:
    """画像をダウンロードします。"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://image.baidu.com/"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.content
    except Exception:
        return None

def save_image(image_data: bytes, keyword: str) -> str | None:
    """画像を保存します。"""
    if not image_data:
        return None
    save_dir = os.path.join("images", keyword)
    os.makedirs(save_dir, exist_ok=True)
    file_hash = hashlib.md5(image_data).hexdigest()[:12]
    file_path = os.path.join(save_dir, f"{file_hash}.jpg")
    if not os.path.exists(file_path):
        with open(file_path, "wb") as f:
            f.write(image_data)
    return file_path

# ========== カスタムノード ==========

class URLSplitter(TaskSplitter):
    """URLリスト分割器。"""
    
    def _split(self, html: str):
        urls = parse_image_urls(html)
        print(f"{len(urls)} 個の画像URLを解析しました")
        return tuple(urls)

# ========== タスクグラフの構築 ==========

def build_crawler_graph(keyword: str) -> TaskGraph:
    """クローラータスクグラフを構築します。"""
    
    # ノードの作成
    stage_search = TaskStage(
        func=search_images,
        execution_mode="serial",
        max_retries=2,
    )
    
    stage_parse = URLSplitter()
    
    stage_download = TaskStage(
        func=download_image,
        execution_mode="thread",
        worker_limit=10,
        max_retries=3,
    )
    
    # クロージャでkeywordを渡す
    stage_save = TaskStage(
        func=lambda data: save_image(data, keyword),
        execution_mode="serial",
        enable_duplicate_check=False,
    )
    
    # 接続の設定
    graph = TaskGraph(schedule_mode="eager", log_level="SUCCESS")
    graph.set_stages(root_stages=[stage_search], stages=[stage_parse, stage_download, stage_save])
    graph.connect([stage_search], [stage_parse])
    graph.connect([stage_parse], [stage_download])
    graph.connect([stage_download], [stage_save])
    
    return graph

# ========== メインプログラム ==========

if __name__ == "__main__":
    # 設定
    KEYWORDS = ["猫咪", "小狗", "风景"]
    
    # グラフの構築
    graph = build_crawler_graph(KEYWORDS[0])
    graph.set_reporter(True, host="127.0.0.1", port=5005)
    
    # 実行
    print("画像のクロールを開始します...")
    graph.start_graph({
        graph.root_stages[0].get_tag(): KEYWORDS
    })
    
    # 統計
    summary = graph.get_graph_summary()
    print(f"\nクロール完了！")
    print(f"成功: {summary.get('total_succeeded', 0)}")
    print(f"失敗: {summary.get('total_failed', 0)}")
```

---

## ステップ5：実行とデバッグ

### 5.1 Webサービスの起動

```bash
# ターミナル1：Webサービスを起動
celestialflow-web --port 5005
```

### 5.2 クローラーの実行

```bash
# ターミナル2：クローラーを実行
python crawler.py
```

### 5.3 Web UIの確認

http://localhost:5005 を開くと、以下を確認できます：

1. **Dashboard**: 各ノードの処理進捗をリアルタイム表示
2. **Structure**: タスクグラフ構造の可視化
3. **Errors**: ダウンロード失敗した画像URLとエラー情報
4. **Task Injection**: 新しいキーワードの動的注入

### 5.4 結果の確認

```bash
# ダウンロードした画像を確認
ls images/猫咪/
ls images/小狗/
ls images/风景/
```

---

## 拡張：動的タスク注入

Web UIを通じて新しいキーワードを動的に注入できます：

```python
# またはコードで注入
from celestialflow import TerminationSignal

# 新しいキーワードの注入
graph.put_stage_queue({
    stage_search.get_tag(): ["汽车", "美食"]
})

# 終了シグナルの注入（クロールを停止）
graph.put_stage_queue({
    stage_search.get_tag(): [TerminationSignal()]
})
```

---

## まとめ

このチュートリアルでは、CelestialFlowの完全なワークフローを紹介しました：

1. **タスク分析**: 複雑なタスクを独立した階層に分解する
2. **関数の記述**: 各階層の処理関数を記述し、個別にテストする
3. **ノードの作成**: 関数を`TaskStage`でラップする
4. **グラフの組み立て**: `TaskGraph`でノード関係を組織する
5. **監視付き実行**: Web UIで実行状態をリアルタイムに監視する

### 主要概念の振り返り

| 概念 | 説明 |
|------|------|
| `TaskStage` | タスクノード、処理関数をラップします |
| `TaskSplitter` | 分割器、1つのタスクを複数に分割します |
| `TaskGraph` | タスクグラフ、ノード関係と実行フローを組織します |
| `stage_mode` | ノードの実行モード（serial/thread/process） |
| `execution_mode` | ノード内部の実行モード（serial/thread） |

### 次のステップ

- `TaskRouter`を使用した条件付きルーティングを試す
- `TaskRedisTransport`でクロス言語連携を探る
- その他の[APIリファレンス](reference/stage/core_executor.md)で詳細な機能を確認する
