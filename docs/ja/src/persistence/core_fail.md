# エラー永続化 (Fail Persistence)

> 📅 最終更新日: 2026/05/09

`celestialflow.persistence` モジュールは堅牢なエラー収集と永続化メカニズムを提供し、マルチプロセス並行タスク実行時にすべての例外情報が安全かつ秩序正しく記録されることを保証します。後続の分析やリトライに使用できます。

コアコンポーネントは `FailSpout` と `FailInlet` です。

## アーキテクチャ設計

システムはエラーログの処理に**プロデューサー・コンシューマー**パターンを採用しています：

1.  **FailInlet（プロデューサー）**:
    -   各 Worker スレッドが保持。
    -   エラー情報とタスクメタデータを辞書にパッケージング。
    -   パッケージングされたデータをスレッドセーフなキュー（`queue.Queue`）に投入。

2.  **FailSpout（コンシューマー）**:
    -   独立したデーモンスレッドで実行。
    -   キューを継続的に監視し、新しいエラーレコードが到着すると即座にローカルファイルに書き込む。
    -   ファイル形式は JSONL（JSON Lines）で、ストリーミング読み取りと処理に便利。

この設計により、複数スレッドがファイル書き込みロックを競合することを回避し、高パフォーマンスとデータ整合性を保証します。

## FailSpout

`FailSpout` はエラーログファイルの作成と書き込みを管理します。

### 初期化と起動

```python
listener = FailSpout(error_source="graph_errors")
listener.start()
```

-   `error_source`: エラーソース識別子。ファイル名の一部として使用。
-   起動後、`./fallback/{date}/` ディレクトリに `{error_source}({time}).jsonl` という名前のファイルが作成されます。

### ファイルパス

エラーログはデフォルトで `./fallback/` ディレクトリに日付別にアーカイブされて保存されます：

```text
./fallback/
└── 2023-10-27/
    └── graph_errors(14-30-05-123).jsonl
```

### リスナーの停止

```python
listener.stop()
```

キューに終了シグナルを送信し、バックグラウンドスレッドが残りのデータの処理を完了するのを待ってから安全に終了します。

## FailInlet

`FailInlet` はエラーキューにデータを送信するインターフェースです。

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
-   `timestamp`: エラー発生時刻（ISO 形式）
-   `stage`: エラーが発生したステージタグ
-   `error_repr`: エラーメッセージの文字列表現（切り詰め）
-   `task_repr`: タスクデータの文字列表現（切り詰め）
-   `error`: 完全なエラータイプとメッセージ
-   `task`: 元のタスクデータ
-   `error_id`: エラーの一意識別子
-   `ts`: 元のタイムスタンプ

### メタデータの記録

`FailInlet` はメタデータの記録もサポートし、当時の実行環境の復元に役立ちます：

-   `start_graph(structure_json)`: タスクグラフの構造情報を記録。
-   `start_executor(executor_tag)`: エグゼキューターの起動情報を記録。

```python
sinker.start_graph({...})
```

## データリカバリ

エラーログは標準の JSONL 形式を使用しているため、これらのファイルを読み取るスクリプトを簡単に作成し、失敗したタスクデータを抽出してリトライや分析に使用できます。フレームワークが提供する `celestialflow.persistence.util_jsonl.load_jsonl_logs` 関数を読み取りに活用できます。
