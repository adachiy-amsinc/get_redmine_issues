"""
ファイル操作モジュール

このモジュールは、チケット情報のJSONファイルへの保存と
ディレクトリ管理を担当します。
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


class FileManager:
    """
    ファイル操作を管理するクラス
    
    チケット情報のJSONファイルへの保存とディレクトリ作成を行います。
    """
    
    def __init__(self, output_dir: str):
        """
        FileManagerを初期化します。
        
        Args:
            output_dir (str): 出力先のベースディレクトリパス
        """
        self.output_dir = Path(output_dir)
        self.issues_dir = self.output_dir / "issues"
        self.attachments_dir = self.output_dir / "attachments"
    
    def ensure_directories_exist(self) -> None:
        """
        必要なディレクトリが存在することを確認し、存在しない場合は作成します。
        
        Raises:
            OSError: ディレクトリの作成に失敗した場合
        """
        try:
            # issuesディレクトリを作成（親ディレクトリも含めて）
            self.issues_dir.mkdir(parents=True, exist_ok=True)
            # attachmentsディレクトリを作成
            self.attachments_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise OSError(f"Failed to create directories: {str(e)}")
    
    def save_issue_json(self, issue_id: int, issue_data: Dict[str, Any]) -> str:
        """
        チケット情報をJSONファイルとして保存します。
        
        Args:
            issue_id (int): チケットID
            issue_data (Dict[str, Any]): 保存するチケット情報
            
        Returns:
            str: 保存されたファイルのパス
            
        Raises:
            OSError: ファイルの保存に失敗した場合
        """
        # ファイルパスを生成
        file_path = self.issues_dir / f"{issue_id}.json"
        
        try:
            # JSONファイルとして整形して保存
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(
                    issue_data, 
                    f, 
                    ensure_ascii=False,  # 日本語文字を正しく保存
                    indent=2,            # 読みやすい形式で整形
                    sort_keys=True       # キーをソートして一貫性を保つ
                )
            
            return str(file_path)
            
        except OSError as e:
            raise OSError(f"Failed to save issue {issue_id} to {file_path}: {str(e)}")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid JSON data for issue {issue_id}: {str(e)}")
    
    def get_issue_file_path(self, issue_id: int) -> str:
        """
        指定されたチケットIDのファイルパスを取得します。
        
        Args:
            issue_id (int): チケットID
            
        Returns:
            str: ファイルパス
        """
        return str(self.issues_dir / f"{issue_id}.json")
    
    def file_exists(self, issue_id: int) -> bool:
        """
        指定されたチケットIDのファイルが既に存在するかチェックします。
        
        Args:
            issue_id (int): チケットID
            
        Returns:
            bool: ファイルが存在する場合True
        """
        file_path = self.issues_dir / f"{issue_id}.json"
        return file_path.exists() and file_path.is_file()
    
    def get_attachment_dir_path(self, issue_id: int) -> str:
        """
        指定されたチケットIDの添付ファイル用ディレクトリパスを取得します。
        
        Args:
            issue_id (int): チケットID
            
        Returns:
            str: 添付ファイル用ディレクトリパス
        """
        return str(self.attachments_dir / str(issue_id))
    
    def get_attachment_file_path(self, issue_id: int, filename: str) -> str:
        """
        指定されたチケットIDと添付ファイル名の完全なファイルパスを取得します。
        
        Args:
            issue_id (int): チケットID
            filename (str): 添付ファイル名
            
        Returns:
            str: 添付ファイルの完全なパス
        """
        return str(self.attachments_dir / str(issue_id) / filename)
