# エラー永続化 (Fail Persistence)

`celestialflow.persistence` モジュールは、堅牢なエラー収集と永続化メカニズムを提供します。マルチプロセス並行タスク実行時に、すべての例外情報が安全かつ順序立てて記録され、後続の分析やリトライに使用できることを保証します。

コアコンポーネントは `FailSpout` と `FailInlet` です。

## アーキテクチャ設計

システムはエラーログの処理に**プロデューサー-コンシューマー**パターンを採用しています：

1.  **FailInlet (プロデューサー)**:
    -   各 Worker プロセス（またはスレッド）が保持します。
    -   エラー情報とタスクメタデータを辞書にパッケージ化する役割を担います。
    -   パッケージ化されたデータをマルチプロセス安全なキュー（`multiprocessing.Queue`）に配置します。

2.  **FailSpout (コンシューマー)**:
    -   メインプロセスの独立したデーモンスレッドで実行されます。
    -   キューを継続的にリッスンし、新しいエラーレコードがあれば即座にローカルファイルに書き込みます。
    -   ファイルフォーマットは JSONL (JSON Lines) で、ストリーミング読み取りと処理を容易にします。

この設計により、マルチプロセスがファイル書き込みロックを競合することを回避し、高パフォーマンスとデータ整合性を保証します。

## FailSpout

`FailSpout` はエラーログファイルの作成と書き込みを管理します。

### 初期化と起動

```python
listener = FailSpout(error_source="graph_errors")
listener.start()
```

-   `error_source`: エラーソースの識別子で、ファイル名の一部として使用されます。
-   起動すると、`./fallback/{date}/` ディレクトリに `{error_source}({time}).jsonl` という名前のファイルを作成します。

### ファイルパス

エラーログはデフォルトで `./fallback/` ディレクトリに保存され、日付別にアーカイブされます：

```text
./fallback/
└── 2023-10-27/
    └── graph_errors(14-30-05-123).jsonl
```

### リスナーの停止

```python
listener.stop()
```

キューに終了シグナルを送信し、バックグラウンドスレッドが残りのデータを処理し終えた後、安全に終了します。

## FailInlet

`FailInlet` はエラーキューにデータを送信するためのインターフェースです。

### タスクエラーの記録

タスクが失敗しリトライできない場合、`TaskExecutor` は `task_error` メソッドを呼び出してエラーを記録します：

```python
sinker.task_error(
    stage_tag="MyStage",
    error=ValueError("Invalid input"),
    err_id=12345,
    task=[1, 2, 3]
)
```

記録される JSONL 行には以下のフィールドが含まれます：
-   `timestamp`: エラー発生時刻（ISO フォーマット）
-   `stage`: エラーが発生したステージタグ
-   `error_repr`: エラーメッセージの文字列表現（切り詰め済み）
-   `task_repr`: タスクデータの文字列表現（切り詰め済み）
-   `error`: 完全なエラータイプとメッセージ
-   `task`: 元のタスクデータ
-   `error_id`: エラーの一意識別子
-   `ts`: 生のタイムスタンプ

### メタデータの記録

`FailInlet` は、当時の実行環境を再現するためのメタデータの記録もサポートしています：

-   `start_graph(structure_json)`: タスクグラフの構造情報を記録します。
-   `start_executor(executor_tag)`: エグゼキューターの起動情報を記録します。

```python
sinker.start_graph({...})
```

## データ復旧

エラーログは標準の JSONL フォーマットを使用しているため、これらのファイルを読み取り、失敗したタスクデータを抽出してリトライや分析を行うスクリプトを簡単に作成できます。フレームワークが提供する `celestialflow.persistence.util_jsonl.load_jsonl_logs` 関数が読み取りを支援します。
