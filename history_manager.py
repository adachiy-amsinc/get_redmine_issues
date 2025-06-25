#!/usr/bin/env python3
"""
履歴管理モジュール

実行されたコマンドを日付別のログファイルに記録する機能を提供します。
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import logging


class HistoryManager:
    """
    コマンド実行履歴を管理するクラス
    """
    
    def __init__(self, base_dir: str = "."):
        """
        HistoryManagerを初期化します。
        
        Args:
            base_dir (str): 履歴ディレクトリの基準となるディレクトリ
        """
        self.base_dir = Path(base_dir)
        self.history_dir = self.base_dir / "history"
        self.logger = logging.getLogger(__name__)
    
    def ensure_history_directory_exists(self) -> None:
        """
        履歴ディレクトリが存在することを確認し、必要に応じて作成します。
        """
        try:
            self.history_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"履歴ディレクトリを確認/作成しました: {self.history_dir}")
        except OSError as e:
            self.logger.error(f"履歴ディレクトリの作成に失敗しました: {e}")
            raise
    
    def get_log_file_path(self, date: Optional[datetime] = None) -> Path:
        """
        指定された日付のログファイルパスを取得します。
        
        Args:
            date (Optional[datetime]): ログファイルの日付。Noneの場合は現在日付を使用
            
        Returns:
            Path: ログファイルのパス
        """
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime("%Y%m%d")
        return self.history_dir / f"{date_str}.log"
    
    def log_command_execution(
        self, 
        command_args: List[str], 
        success: bool = True,
        additional_info: Optional[str] = None
    ) -> None:
        """
        コマンドの実行履歴をログファイルに記録します。
        
        Args:
            command_args (List[str]): 実行されたコマンドの引数リスト
            success (bool): コマンドの実行が成功したかどうか
            additional_info (Optional[str]): 追加情報（成功/失敗件数など）
        """
        try:
            self.ensure_history_directory_exists()
            
            # ログエントリの作成
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "SUCCESS" if success else "FAILED"
            
            # コマンドライン文字列の再構築
            command_line = " ".join(command_args)
            
            # ログエントリの構築
            log_entry = f"[{timestamp}] {status}: {command_line}"
            
            if additional_info:
                log_entry += f" | {additional_info}"
            
            log_entry += "\n"
            
            # ログファイルに追記
            log_file_path = self.get_log_file_path()
            
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            
            self.logger.debug(f"コマンド履歴をログに記録しました: {log_file_path}")
            
        except Exception as e:
            self.logger.error(f"履歴ログの記録に失敗しました: {e}")
            # 履歴ログの失敗はメイン処理を停止させない
    
    def get_command_args_from_sys_argv(self) -> List[str]:
        """
        sys.argvからコマンド引数を取得します。
        
        Returns:
            List[str]: コマンド引数のリスト
        """
        # スクリプト名を含む完全なコマンドライン
        return sys.argv.copy()
    
    def read_history_log(self, date: Optional[datetime] = None) -> List[str]:
        """
        指定された日付の履歴ログを読み取ります。
        
        Args:
            date (Optional[datetime]): 読み取る日付。Noneの場合は現在日付を使用
            
        Returns:
            List[str]: ログエントリのリスト
        """
        log_file_path = self.get_log_file_path(date)
        
        if not log_file_path.exists():
            self.logger.info(f"履歴ログファイルが存在しません: {log_file_path}")
            return []
        
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                return [line.rstrip('\n') for line in f.readlines()]
        except Exception as e:
            self.logger.error(f"履歴ログの読み取りに失敗しました: {e}")
            return []
    
    def list_available_log_dates(self) -> List[str]:
        """
        利用可能な履歴ログの日付一覧を取得します。
        
        Returns:
            List[str]: 日付文字列のリスト（YYYYMMDD形式）
        """
        if not self.history_dir.exists():
            return []
        
        try:
            log_files = []
            for file_path in self.history_dir.glob("*.log"):
                # ファイル名から日付部分を抽出（拡張子を除く）
                date_str = file_path.stem
                # YYYYMMDD形式の8桁数字かチェック
                if len(date_str) == 8 and date_str.isdigit():
                    log_files.append(date_str)
            
            return sorted(log_files)
            
        except Exception as e:
            self.logger.error(f"履歴ログファイル一覧の取得に失敗しました: {e}")
            return []
    
    def format_summary_info(self, successful_count: int, failed_count: int, total_count: int) -> str:
        """
        処理結果のサマリー情報をフォーマットします。
        
        Args:
            successful_count (int): 成功件数
            failed_count (int): 失敗件数
            total_count (int): 総件数
            
        Returns:
            str: フォーマットされたサマリー情報
        """
        return f"成功:{successful_count}, 失敗:{failed_count}, 合計:{total_count}"


def main():
    """
    テスト用のメイン関数
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='履歴管理のテスト')
    parser.add_argument('--test-log', action='store_true', help='テストログを記録')
    parser.add_argument('--show-history', action='store_true', help='履歴を表示')
    parser.add_argument('--list-dates', action='store_true', help='利用可能な日付を表示')
    
    args = parser.parse_args()
    
    # ログ設定
    logging.basicConfig(level=logging.DEBUG)
    
    history_manager = HistoryManager()
    
    if args.test_log:
        # テストログの記録
        test_args = ['python', 'get_redmine_issues.py', '--output-dir', './test', '12345', '12346']
        summary = history_manager.format_summary_info(2, 0, 2)
        history_manager.log_command_execution(test_args, True, summary)
        print("テストログを記録しました")
    
    if args.show_history:
        # 履歴の表示
        history_entries = history_manager.read_history_log()
        if history_entries:
            print("=== 今日の実行履歴 ===")
            for entry in history_entries:
                print(entry)
        else:
            print("履歴がありません")
    
    if args.list_dates:
        # 利用可能な日付の表示
        dates = history_manager.list_available_log_dates()
        if dates:
            print("=== 利用可能な履歴日付 ===")
            for date in dates:
                formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
                print(f"{date} ({formatted_date})")
        else:
            print("履歴ファイルがありません")


if __name__ == '__main__':
    main()
