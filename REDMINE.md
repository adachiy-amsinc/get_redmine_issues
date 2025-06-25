# Redmineチケット情報取得ツールの開発仕様書

## 1. 概要

Redmine APIを利用して、指定された複数のチケット（Issue）情報を取得し、個別のJSONファイルとして保存するコマンドラインツールを開発する。

このツールは、チケット本体の情報に加えて、それに紐づく全てのコメント（注記）履歴も取得することを目的とする。

## 2. 機能要件

### 2.1. 入力

-   **チケットID**:
    -   情報を取得したいチケットのIDを、コマンドライン引数として **1つ以上** 指定できること。
    -   例: `49121 49122 50000`
-   **出力先ディレクトリ**:
    -   取得したJSONファイルを保存する親ディレクトリを、コマンドライン引数で指定できること。
    -   例: `--output-dir /path/to/data`
    -   履歴表示モード（`--show-history` または `--list-history-dates`）の場合は省略可能

### 2.2. 設定

-   **Redmineサーバー情報**:
    -   接続先のRedmineサーバーのURLとAPIキーは、プログラム内に直接記述しない（ハードコーディングしない）。
    -   プロジェクトルートに置かれる `.env` ファイルから環境変数として読み込むこと。

    **.env ファイルの形式**
    ```env
    REDMINE_URL="http://redmine.example.com"
    REDMINE_API_KEY="your_secret_api_key_here"
    ```

### 2.3. 処理

-   **APIリクエスト**:
    -   指定された各チケットIDに対して、Redmineの `GET /issues/{issue_id}.json` APIエンドポイントを呼び出す。
    -   リクエストURLには、コメント情報と添付ファイル情報を取得するために必ず `?include=journals,attachments` パラメータを付与すること。
    -   HTTPリクエストのヘッダーには `X-Redmine-API-Key` を含め、認証を行うこと。

-   **ファイル保存**:
    -   取得したJSONデータは、整形（pretty-print）してファイルに保存する。
    -   保存先のパスは、`{出力先ディレクトリ}/issues/{チケットID}.json` というルールに従うこと。
        -   例: チケットID `49121` の場合 → `/path/to/data/issues/49121.json`
    -   `{出力先ディレクトリ}/issues` ディレクトリが存在しない場合は、プログラムが自動で作成すること。

-   **添付ファイルのダウンロード**:
    -   チケットに添付されているファイルを自動的にダウンロードする。
    -   添付ファイルの保存先: `{出力先ディレクトリ}/attachments/{チケットID}/{ファイル名}`
        -   例: チケットID `49121` の添付ファイル → `/path/to/data/attachments/49121/image.png`
    -   `{出力先ディレクトリ}/attachments` ディレクトリが存在しない場合は、プログラムが自動で作成すること。
    -   添付ファイルのダウンロードは `--no-attachments` オプションで無効化できること。
    -   既に同名のファイルが存在する場合はスキップする。
    -   ダウンロードに失敗した場合は警告メッセージを表示するが、処理は継続する。

-   **実行履歴の記録**:
    -   実行されたコマンドを日付別のログファイルに自動記録すること。
    -   履歴ファイルの保存場所: `./history/yyyymmdd.log`
    -   記録される情報: 実行日時、成功/失敗、コマンドライン、処理結果サマリー
    -   履歴ファイルは日付別に自動作成される
    -   履歴記録の失敗はメイン処理を停止させない

-   **履歴表示機能**:
    -   `--show-history` オプション: 今日の実行履歴を表示
    -   `--list-history-dates` オプション: 履歴がある日付一覧を表示
    -   履歴表示モードでは、チケット取得処理は実行されない

### 2.4. エラーハンドリング

-   指定されたチケットIDが存在しない場合（API応答が404 Not Found）、そのチケットIDに関するエラーメッセージを標準エラー出力に表示し、次のチケットIDの処理を続行すること。
-   APIキーが無効、またはネットワークエラーが発生した場合、エラーメッセージを表示してプログラムを終了すること。
-   `.env` ファイルが存在しない、または必要なキーが設定されていない場合、その旨を伝えるエラーメッセージを表示してプログラムを終了すること。

## 3. 非機能要件

-   **言語**: Python 3.x を使用する。
-   **依存ライブラリ**:
    -   HTTPリクエスト: `requests`
    -   環境変数読み込み: `python-dotenv`
    -   これらの依存関係は `requirements.txt` ファイルで管理すること。

## 4. 実行コマンド例

```bash
# 依存ライブラリのインストール
pip install -r requirements.txt

# 実行例1: 2つのチケットを/tmp/redmine_dataディレクトリに保存
python get_redmine_issues.py --output-dir /tmp/redmine_data 49121 50001

# 実行例2: 1つのチケットをカレントディレクトリ配下のdataディレクトリに保存
python get_redmine_issues.py --output-dir ./data 49122

# 実行例3: 詳細ログ付きで複数チケットを取得
python get_redmine_issues.py --output-dir ./output --verbose 12345 12346 12347

# 実行例4: 既存ファイルをスキップして取得
python get_redmine_issues.py --output-dir ./output --skip-existing 12345 12346

# 実行例5: 添付ファイルをダウンロードせずにチケット情報のみ取得
python get_redmine_issues.py --output-dir ./output --no-attachments 12345 12346

# 実行例6: 今日の実行履歴を表示
python get_redmine_issues.py --show-history

# 実行例7: 履歴がある日付一覧を表示
python get_redmine_issues.py --list-history-dates
```

## 5. 期待されるファイル構成

```
.
├── get_redmine_issues.py   # メインのPythonスクリプト
├── redmine_client.py       # Redmine APIクライアント
├── file_manager.py         # ファイル操作管理
├── history_manager.py      # 実行履歴管理
├── config.py              # 設定管理
├── requirements.txt        # 依存ライブラリ一覧
├── .env                    # Redmineの接続情報を格納（Git管理対象外）
├── .env.example            # .envファイルのテンプレート
├── .gitignore             # Git管理対象外ファイルの設定
├── issues/                # チケット情報JSONファイル保存ディレクトリ
│   └── {チケットID}.json  # 各チケットのJSON情報
├── attachments/           # 添付ファイル保存ディレクトリ
│   └── {チケットID}/      # チケット別の添付ファイルフォルダ
│       └── {ファイル名}   # ダウンロードされた添付ファイル
└── history/               # 実行履歴ディレクトリ（Git管理対象外）
    └── yyyymmdd.log       # 日付別の実行履歴ログ
```

## 6. 履歴ログの形式

実行履歴は以下の形式で記録される：

```
[YYYY-MM-DD HH:MM:SS] STATUS: command_line | additional_info
```

**例：**
```
[2024-06-24 15:30:45] SUCCESS: python get_redmine_issues.py --output-dir ./data 12345 12346 | 成功:2, 失敗:0, 合計:2
[2024-06-24 16:15:22] FAILED: python get_redmine_issues.py --output-dir ./data 99999 | 成功:0, 失敗:1, 合計:1
```

## 7. コマンドラインオプション

| オプション | 短縮形 | 説明 | 必須 |
|-----------|--------|------|------|
| `--output-dir` | `-o` | JSONファイルを保存する出力先ディレクトリ | チケット取得時のみ |
| `--verbose` | `-v` | 詳細なログを出力 | × |
| `--skip-existing` | - | 既に存在するファイルをスキップ | × |
| `--no-attachments` | - | 添付ファイルをダウンロードしない | × |
| `--show-history` | - | 今日の実行履歴を表示 | × |
| `--list-history-dates` | - | 履歴がある日付一覧を表示 | × |
| `--help` | `-h` | ヘルプメッセージを表示 | × |

---
### AIへの指示例

この仕様書をコピー＆ペーストして、AIに以下のように指示してみてください。

**プロンプト例：**
「こんにちは。あなたはプロのPython開発者です。以下の仕様書に基づいて、Redmineからチケット情報を取得するコマンドラインツールを作成してください。コードはモジュール化され、読みやすいようにコメントも適切に含めてください。実行履歴機能も含めて実装してください。」

## 8. 追加機能の詳細

### 8.1. 実行履歴管理

- **目的**: 実行されたコマンドの記録と追跡
- **実装**: `HistoryManager` クラスによる履歴管理
- **保存場所**: `./history/yyyymmdd.log`
- **記録タイミング**: コマンド実行完了時（成功・失敗問わず）

### 8.2. エラーハンドリングの拡張

- 履歴記録の失敗はメイン処理を停止させない
- 各種エラー（設定エラー、接続エラー、ユーザー中断など）も履歴に記録
- エラー内容も履歴ログに含める

### 8.3. モジュール設計

- **config.py**: 環境設定の読み込みと検証
- **redmine_client.py**: Redmine API通信
- **file_manager.py**: ファイル操作とディレクトリ管理
- **history_manager.py**: 実行履歴の記録と表示
- **get_redmine_issues.py**: メイン処理とコマンドライン解析

### 8.4. 添付ファイル機能

- **自動ダウンロード**: チケットに添付されているファイルを自動的にダウンロード
- **ディレクトリ構造**: `attachments/{チケットID}/{ファイル名}` の形式で保存
- **対応ファイル形式**: 画像ファイル（PNG、JPG等）、文書ファイル（PDF、DOC等）、その他すべての形式
- **エラーハンドリング**: ダウンロード失敗時は警告表示するが処理継続
- **重複回避**: 既存ファイルは自動的にスキップ
- **無効化オプション**: `--no-attachments` で添付ファイルダウンロードを無効化可能

**添付ファイルダウンロードの実行例：**

```bash
# 添付ファイルも含めて取得（デフォルト動作）
python get_redmine_issues.py --output-dir ./data 49121

# 添付ファイルをダウンロードしない
python get_redmine_issues.py --output-dir ./data --no-attachments 49121

# 詳細ログで添付ファイルのダウンロード状況を確認
python get_redmine_issues.py --output-dir ./data --verbose 49121
```

**添付ファイルダウンロード時のログ出力例：**

```
Issue 49121: 2 個の添付ファイルをダウンロード中...
  📎 clipboard-202503171856-ouvhb.png をダウンロード中...
  ✅ clipboard-202503171856-ouvhb.png ダウンロード完了
  📎 clipboard-202503181659-2rfjh.png をダウンロード中...
  ✅ clipboard-202503181659-2rfjh.png ダウンロード完了
Issue 49121: すべての添付ファイルのダウンロードが完了しました
```

