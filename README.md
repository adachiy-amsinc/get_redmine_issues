# Redmineチケット情報取得ツール

Redmine APIを使用して、指定されたチケット情報（コメント履歴と添付ファイルを含む）を取得し、JSONファイルとして保存するコマンドラインツールです。

## 機能

- 複数のチケットIDを指定して一括取得
- チケット本体の情報に加えて、コメント（注記）履歴も取得
- **添付ファイルの自動ダウンロード** - チケットに添付されたファイルを自動的にダウンロード
- 取得したデータを整形されたJSONファイルとして保存
- エラーハンドリングと詳細なログ出力
- 既存ファイルのスキップ機能
- **実行履歴の自動記録** - 実行されたコマンドを日付別にログファイルに保存
- **履歴表示機能** - 過去の実行履歴を確認可能

## セットアップ

### 1. 依存ライブラリのインストール

```bash
pip install -r requirements.txt
```

### 2. 環境設定ファイルの作成

`.env.example`をコピーして`.env`ファイルを作成し、Redmineの接続情報を設定してください。

```bash
cp .env.example .env
```

`.env`ファイルを編集：

```env
REDMINE_URL="https://your-redmine-server.com"
REDMINE_API_KEY="your_api_key_here"
```

## 使用方法

### 基本的な使用方法

```bash
python get_redmine_issues.py --output-dir /path/to/output チケットID1 チケットID2 ...
```

### 使用例

```bash
# 2つのチケットを/tmp/redmine_dataディレクトリに保存
python get_redmine_issues.py --output-dir /tmp/redmine_data 49121 50001

# 1つのチケットをカレントディレクトリ配下のdataディレクトリに保存
python get_redmine_issues.py --output-dir ./data 49122

# 複数のチケットを詳細ログ付きで取得
python get_redmine_issues.py --output-dir ./output --verbose 12345 12346 12347

# 既存ファイルをスキップして取得
python get_redmine_issues.py --output-dir ./output --skip-existing 12345 12346

# 添付ファイルをダウンロードせずにチケット情報のみ取得
python get_redmine_issues.py --output-dir ./output --no-attachments 12345 12346

# 今日の実行履歴を表示
python get_redmine_issues.py --show-history

# 履歴がある日付一覧を表示
python get_redmine_issues.py --list-history-dates
```

### オプション

- `--output-dir, -o`: JSONファイルを保存する出力先ディレクトリ（チケット取得時は必須）
- `--verbose, -v`: 詳細なログを出力
- `--skip-existing`: 既に存在するファイルをスキップ
- `--no-attachments`: 添付ファイルをダウンロードしない
- `--show-history`: 今日の実行履歴を表示
- `--list-history-dates`: 履歴がある日付一覧を表示
- `--help, -h`: ヘルプメッセージを表示

### 実行履歴機能

このツールは実行されたコマンドを自動的に記録します：

- 履歴ファイルの保存場所: `./history/yyyymmdd.log`
- 記録される情報: 実行日時、成功/失敗、コマンドライン、処理結果サマリー
- 履歴ファイルは日付別に自動作成されます

#### 履歴ログの形式例

```
[2024-06-24 15:30:45] SUCCESS: python get_redmine_issues.py --output-dir ./data 12345 12346 | 成功:2, 失敗:0, 合計:2
[2024-06-24 16:15:22] FAILED: python get_redmine_issues.py --output-dir ./data 99999 | 成功:0, 失敗:1, 合計:1
```

## 出力形式

取得したチケット情報は以下の形式で保存されます：

```
{出力先ディレクトリ}/
├── issues/
│   ├── 49121.json
│   ├── 49122.json
│   └── 50001.json
└── attachments/
    ├── 49121/
    │   ├── document1.pdf
    │   └── screenshot.png
    ├── 49122/
    │   └── logfile.txt
    └── 50001/
        └── specification.docx
```

- `issues/`: チケット情報のJSONファイル（チケットの詳細情報とコメント履歴を含む）
- `attachments/{チケットID}/`: 各チケットの添付ファイル

## エラーハンドリング

- チケットが存在しない場合（404 Not Found）: エラーメッセージを表示して次のチケットの処理を継続
- APIキーが無効な場合: エラーメッセージを表示してプログラムを終了
- ネットワークエラー: エラーメッセージを表示してプログラムを終了
- `.env`ファイルが存在しない場合: エラーメッセージを表示してプログラムを終了

## ファイル構成

```
.
├── get_redmine_issues.py   # メインスクリプト
├── redmine_client.py       # Redmine APIクライアント
├── file_manager.py         # ファイル操作管理
├── history_manager.py      # 実行履歴管理
├── config.py              # 設定管理
├── requirements.txt       # 依存ライブラリ
├── .env                   # 環境設定（Git管理対象外）
├── .env.example          # 環境設定テンプレート
└── README.md             # このファイル
```

## トラブルシューティング

### 接続エラーが発生する場合

1. `.env`ファイルの`REDMINE_URL`が正しいか確認
2. APIキーが有効か確認
3. ネットワーク接続を確認
4. Redmineサーバーが稼働しているか確認

### 権限エラーが発生する場合

1. 出力先ディレクトリへの書き込み権限を確認
2. APIキーに適切な権限が設定されているか確認

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
