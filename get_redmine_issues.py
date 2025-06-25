#!/usr/bin/env python3
"""
Redmineチケット情報取得ツール

このスクリプトは、指定されたチケットIDのリストに対して、
Redmine APIを使用してチケット情報（コメント履歴を含む）を取得し、
個別のJSONファイルとして保存します。

使用例:
    python get_redmine_issues.py --output-dir /tmp/data 49121 49122 50000
"""

import argparse
import sys
import os
from typing import List
import logging

from config import ConfigManager, ConfigError
from redmine_client import RedmineClient, RedmineAPIError
from file_manager import FileManager
from history_manager import HistoryManager


def setup_logging() -> None:
    """
    ログ設定を初期化します。
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def parse_arguments() -> argparse.Namespace:
    """
    コマンドライン引数を解析します。
    
    Returns:
        argparse.Namespace: 解析された引数
    """
    parser = argparse.ArgumentParser(
        description='Redmineからチケット情報を取得してJSONファイルとして保存します。',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s --output-dir /tmp/redmine_data 49121 50001
  %(prog)s --output-dir ./data 49122
  %(prog)s -o /path/to/output 12345 12346 12347
  %(prog)s --show-history                    # 今日の実行履歴を表示
  %(prog)s --list-history-dates              # 履歴がある日付一覧を表示

注意:
  - .envファイルにREDMINE_URLとREDMINE_API_KEYを設定してください
  - 出力ディレクトリ配下にissuesフォルダが自動作成されます
  - 実行履歴は./history/yyyymmdd.logに自動保存されます
        """
    )
    
    # メイン機能のオプション
    parser.add_argument(
        '--output-dir', '-o',
        help='JSONファイルを保存する出力先ディレクトリ'
    )
    
    parser.add_argument(
        'issue_ids',
        nargs='*',
        type=int,
        help='取得するチケットのID（1つ以上指定）'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='詳細なログを出力'
    )
    
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='既に存在するファイルをスキップ'
    )
    
    parser.add_argument(
        '--no-attachments',
        action='store_true',
        help='添付ファイルをダウンロードしない'
    )
    
    # 履歴表示のオプション
    parser.add_argument(
        '--show-history',
        action='store_true',
        help='今日の実行履歴を表示'
    )
    
    parser.add_argument(
        '--list-history-dates',
        action='store_true',
        help='履歴がある日付一覧を表示'
    )
    
    args = parser.parse_args()
    
    # 履歴表示モードでない場合は、output-dirとissue_idsが必須
    if not args.show_history and not args.list_history_dates:
        if not args.output_dir:
            parser.error("--output-dir は必須です（履歴表示モード以外）")
        if not args.issue_ids:
            parser.error("issue_ids は1つ以上指定してください（履歴表示モード以外）")
    
    return args


def process_issue(
    client: RedmineClient, 
    file_manager: FileManager, 
    issue_id: int,
    skip_existing: bool = False,
    download_attachments: bool = True
) -> bool:
    """
    単一のチケットを処理します。
    
    Args:
        client (RedmineClient): Redmine APIクライアント
        file_manager (FileManager): ファイル管理オブジェクト
        issue_id (int): 処理するチケットID
        skip_existing (bool): 既存ファイルをスキップするかどうか
        download_attachments (bool): 添付ファイルをダウンロードするかどうか
        
    Returns:
        bool: 処理が成功した場合True
    """
    logger = logging.getLogger(__name__)
    
    try:
        # 既存ファイルのチェック
        if skip_existing and file_manager.file_exists(issue_id):
            logger.info(f"Issue {issue_id}: ファイルが既に存在するためスキップします")
            return True
        
        logger.info(f"Issue {issue_id}: チケット情報を取得中...")
        
        # チケット情報を取得
        issue_data = client.get_issue(issue_id)
        
        if issue_data is None:
            logger.error(f"Issue {issue_id}: チケットが見つかりません (404 Not Found)")
            return False
        
        # ファイルに保存
        saved_path = file_manager.save_issue_json(issue_id, issue_data)
        logger.info(f"Issue {issue_id}: 保存完了 -> {saved_path}")
        
        # 添付ファイルのダウンロード処理
        if download_attachments:
            attachments = client.get_attachments_from_issue(issue_data)
            if attachments:
                logger.info(f"Issue {issue_id}: {len(attachments)} 個の添付ファイルをダウンロード中...")
                download_successful = 0
                download_failed = 0
                
                for attachment in attachments:
                    attachment_id = attachment.get('id')
                    filename = attachment.get('filename', f'attachment_{attachment_id}')
                    
                    if attachment_id:
                        file_path = file_manager.get_attachment_file_path(issue_id, filename)
                        
                        # 既にファイルが存在する場合はスキップ
                        if os.path.exists(file_path):
                            logger.info(f"  📎 {filename} (既に存在するためスキップ)")
                            download_successful += 1
                            continue
                        
                        logger.info(f"  📎 {filename} をダウンロード中...")
                        
                        if client.download_attachment(attachment_id, file_path):
                            logger.info(f"  ✅ {filename} ダウンロード完了")
                            download_successful += 1
                        else:
                            logger.warning(f"  ❌ {filename} ダウンロード失敗")
                            download_failed += 1
                    else:
                        logger.warning(f"  ⚠️  添付ファイル情報が不正です: {attachment}")
                        download_failed += 1
                
                if download_failed > 0:
                    logger.warning(f"Issue {issue_id}: 添付ファイル {download_failed}/{len(attachments)} 個のダウンロードに失敗しました")
                else:
                    logger.info(f"Issue {issue_id}: すべての添付ファイルのダウンロードが完了しました")
            else:
                logger.info(f"Issue {issue_id}: 添付ファイルはありません")
        
        return True
        
    except RedmineAPIError as e:
        logger.error(f"Issue {issue_id}: API エラー - {str(e)}")
        return False
    
    except (OSError, ValueError) as e:
        logger.error(f"Issue {issue_id}: ファイル保存エラー - {str(e)}")
        return False
    
    except Exception as e:
        logger.error(f"Issue {issue_id}: 予期しないエラー - {str(e)}")
        return False


def main() -> int:
    """
    メイン処理関数
    
    Returns:
        int: 終了コード（0: 成功, 1: エラー）
    """
    # ログ設定
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 履歴管理の初期化
    history_manager = HistoryManager()
    command_args = history_manager.get_command_args_from_sys_argv()
    
    try:
        # コマンドライン引数の解析
        args = parse_arguments()
        
        # 詳細ログの設定
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        # 履歴表示モードの処理
        if args.show_history:
            history_entries = history_manager.read_history_log()
            if history_entries:
                print("=== 今日の実行履歴 ===")
                for entry in history_entries:
                    print(entry)
            else:
                print("今日の履歴がありません")
            return 0
        
        if args.list_history_dates:
            dates = history_manager.list_available_log_dates()
            if dates:
                print("=== 履歴がある日付一覧 ===")
                for date in dates:
                    formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
                    print(f"{date} ({formatted_date})")
            else:
                print("履歴ファイルがありません")
            return 0
        
        # 通常のチケット取得処理
        logger.info("Redmineチケット情報取得ツールを開始します")
        logger.info(f"対象チケットID: {args.issue_ids}")
        logger.info(f"出力先ディレクトリ: {args.output_dir}")
        
        # 設定の読み込み
        logger.info("設定を読み込み中...")
        config = ConfigManager.load_config()
        ConfigManager.validate_config(config)
        
        # Redmineクライアントの初期化
        logger.info("Redmine APIクライアントを初期化中...")
        client = RedmineClient(config.url, config.api_key)
        
        # 接続テスト
        logger.info("Redmineサーバーへの接続をテスト中...")
        if not client.test_connection():
            logger.error("Redmineサーバーへの接続に失敗しました。URLとAPIキーを確認してください。")
            # 履歴に失敗を記録
            history_manager.log_command_execution(command_args, False, "接続失敗")
            return 1
        
        logger.info("接続テスト成功")
        
        # ファイルマネージャーの初期化
        file_manager = FileManager(args.output_dir)
        file_manager.ensure_directories_exist()
        
        logger.info(f"出力ディレクトリを準備しました:")
        logger.info(f"  チケット情報: {file_manager.issues_dir}")
        logger.info(f"  添付ファイル: {file_manager.attachments_dir}")
        
        # 添付ファイルダウンロードの設定
        download_attachments = not args.no_attachments
        if download_attachments:
            logger.info("添付ファイルのダウンロードが有効です")
        else:
            logger.info("添付ファイルのダウンロードは無効です (--no-attachments)")
        
        # 各チケットを処理
        successful_count = 0
        failed_count = 0
        
        for issue_id in args.issue_ids:
            if process_issue(client, file_manager, issue_id, args.skip_existing, download_attachments):
                successful_count += 1
            else:
                failed_count += 1
        
        # 結果の表示
        logger.info("=" * 50)
        logger.info("処理結果:")
        logger.info(f"  成功: {successful_count} 件")
        logger.info(f"  失敗: {failed_count} 件")
        logger.info(f"  合計: {len(args.issue_ids)} 件")
        
        # 履歴に記録
        summary_info = history_manager.format_summary_info(
            successful_count, failed_count, len(args.issue_ids)
        )
        
        if failed_count > 0:
            logger.warning(f"{failed_count} 件のチケットで処理に失敗しました")
            history_manager.log_command_execution(command_args, False, summary_info)
            return 1
        
        logger.info("すべてのチケットの処理が完了しました")
        history_manager.log_command_execution(command_args, True, summary_info)
        return 0
        
    except ConfigError as e:
        logger.error(f"設定エラー: {str(e)}")
        history_manager.log_command_execution(command_args, False, f"設定エラー: {str(e)}")
        return 1
    
    except KeyboardInterrupt:
        logger.info("ユーザーによって処理が中断されました")
        history_manager.log_command_execution(command_args, False, "ユーザー中断")
        return 1
    
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {str(e)}")
        history_manager.log_command_execution(command_args, False, f"予期しないエラー: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
