"""
Redmine API クライアントモジュール

このモジュールは、Redmine REST APIとの通信を担当します。
チケット情報の取得とエラーハンドリングを提供します。
"""

import requests
from typing import Dict, Any, Optional, List
import json
import os
from pathlib import Path


class RedmineAPIError(Exception):
    """Redmine API関連のエラーを表すカスタム例外クラス"""
    pass


class RedmineClient:
    """
    Redmine APIクライアントクラス
    
    Redmineサーバーとの通信を管理し、チケット情報の取得を行います。
    """
    
    def __init__(self, base_url: str, api_key: str):
        """
        RedmineClientを初期化します。
        
        Args:
            base_url (str): RedmineサーバーのベースURL
            api_key (str): Redmine API キー
        """
        self.base_url = base_url.rstrip('/')  # 末尾のスラッシュを削除
        self.api_key = api_key
        self.session = requests.Session()
        
        # APIキーをヘッダーに設定
        self.session.headers.update({
            'X-Redmine-API-Key': self.api_key,
            'Content-Type': 'application/json'
        })
    
    def get_issue(self, issue_id: int) -> Optional[Dict[str, Any]]:
        """
        指定されたチケットIDの情報を取得します。
        
        Args:
            issue_id (int): 取得するチケットのID
            
        Returns:
            Optional[Dict[str, Any]]: チケット情報のJSON辞書。
                                    チケットが存在しない場合はNone。
            
        Raises:
            RedmineAPIError: API呼び出しでエラーが発生した場合
        """
        url = f"{self.base_url}/issues/{issue_id}.json"
        
        # コメント情報と添付ファイル情報を含めるためのパラメータを追加
        params = {'include': 'journals,attachments'}
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            
            # チケットが存在しない場合
            if response.status_code == 404:
                return None
            
            # その他のHTTPエラー
            if not response.ok:
                raise RedmineAPIError(
                    f"API request failed with status {response.status_code}: "
                    f"{response.text}"
                )
            
            # JSONレスポンスをパース
            return response.json()
            
        except requests.exceptions.Timeout:
            raise RedmineAPIError(f"Timeout occurred while fetching issue {issue_id}")
        
        except requests.exceptions.ConnectionError:
            raise RedmineAPIError(
                f"Connection error occurred while fetching issue {issue_id}. "
                f"Please check your network connection and Redmine URL."
            )
        
        except requests.exceptions.RequestException as e:
            raise RedmineAPIError(f"Request error occurred: {str(e)}")
        
        except json.JSONDecodeError:
            raise RedmineAPIError(
                f"Invalid JSON response received for issue {issue_id}"
            )
    
    def test_connection(self) -> bool:
        """
        Redmineサーバーへの接続とAPIキーの有効性をテストします。
        
        Returns:
            bool: 接続が成功した場合True、失敗した場合False
        """
        try:
            # プロジェクト一覧を取得して接続をテスト（軽量なエンドポイント）
            url = f"{self.base_url}/projects.json"
            response = self.session.get(url, params={'limit': 1}, timeout=10)
            return response.ok
        except requests.exceptions.RequestException:
            return False
    
    def download_attachment(self, attachment_id: int, file_path: str) -> bool:
        """
        指定された添付ファイルをダウンロードします。
        
        Args:
            attachment_id (int): 添付ファイルのID
            file_path (str): 保存先のファイルパス
            
        Returns:
            bool: ダウンロードが成功した場合True、失敗した場合False
        """
        url = f"{self.base_url}/attachments/{attachment_id}"
        
        try:
            response = self.session.get(url, timeout=60, stream=True)
            
            if not response.ok:
                print(f"  ⚠️  添付ファイル {attachment_id} のダウンロードに失敗しました (HTTP {response.status_code})")
                return False
            
            # ディレクトリが存在しない場合は作成
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # ファイルを保存
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return True
            
        except requests.exceptions.Timeout:
            print(f"  ⚠️  添付ファイル {attachment_id} のダウンロードがタイムアウトしました")
            return False
        
        except requests.exceptions.ConnectionError:
            print(f"  ⚠️  添付ファイル {attachment_id} のダウンロード中に接続エラーが発生しました")
            return False
        
        except requests.exceptions.RequestException as e:
            print(f"  ⚠️  添付ファイル {attachment_id} のダウンロード中にエラーが発生しました: {str(e)}")
            return False
        
        except OSError as e:
            print(f"  ⚠️  添付ファイル {attachment_id} の保存中にエラーが発生しました: {str(e)}")
            return False
    
    def get_attachments_from_issue(self, issue_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        チケットデータから添付ファイル情報を抽出します。
        
        Args:
            issue_data (Dict[str, Any]): チケット情報のJSON辞書
            
        Returns:
            List[Dict[str, Any]]: 添付ファイル情報のリスト
        """
        attachments = []
        
        # チケット本体の添付ファイル
        if 'issue' in issue_data and 'attachments' in issue_data['issue']:
            attachments.extend(issue_data['issue']['attachments'])
        
        # コメント（journals）の添付ファイル
        if 'issue' in issue_data and 'journals' in issue_data['issue']:
            for journal in issue_data['issue']['journals']:
                if 'attachments' in journal:
                    attachments.extend(journal['attachments'])
        
        return attachments
