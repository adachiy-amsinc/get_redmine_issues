"""
設定管理モジュール

このモジュールは、環境変数の読み込みと設定値の管理を担当します。
.envファイルからRedmineの接続情報を取得します。
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import NamedTuple


class ConfigError(Exception):
    """設定関連のエラーを表すカスタム例外クラス"""
    pass


class RedmineConfig(NamedTuple):
    """
    Redmine設定情報を格納するデータクラス
    
    Attributes:
        url (str): RedmineサーバーのURL
        api_key (str): Redmine API キー
    """
    url: str
    api_key: str


class ConfigManager:
    """
    設定管理クラス
    
    環境変数の読み込みと設定値の検証を行います。
    """
    
    @staticmethod
    def load_config() -> RedmineConfig:
        """
        .envファイルから設定を読み込みます。
        
        Returns:
            RedmineConfig: Redmine接続設定
            
        Raises:
            ConfigError: 設定ファイルが見つからない、または必要な設定が不足している場合
        """
        # プロジェクトルートの.envファイルを探す
        env_path = Path('.env')
        
        if not env_path.exists():
            raise ConfigError(
                ".env file not found. Please create a .env file based on .env.example"
            )
        
        # .envファイルを読み込み
        load_dotenv(env_path)
        
        # 必要な環境変数を取得
        redmine_url = os.getenv('REDMINE_URL')
        redmine_api_key = os.getenv('REDMINE_API_KEY')
        
        # 設定値の検証
        if not redmine_url:
            raise ConfigError(
                "REDMINE_URL is not set in .env file. "
                "Please set your Redmine server URL."
            )
        
        if not redmine_api_key:
            raise ConfigError(
                "REDMINE_API_KEY is not set in .env file. "
                "Please set your Redmine API key."
            )
        
        # URLの形式を簡単にチェック
        if not (redmine_url.startswith('http://') or redmine_url.startswith('https://')):
            raise ConfigError(
                f"Invalid REDMINE_URL format: {redmine_url}. "
                "URL must start with http:// or https://"
            )
        
        return RedmineConfig(
            url=redmine_url.strip(),
            api_key=redmine_api_key.strip()
        )
    
    @staticmethod
    def validate_config(config: RedmineConfig) -> None:
        """
        設定値の詳細な検証を行います。
        
        Args:
            config (RedmineConfig): 検証する設定
            
        Raises:
            ConfigError: 設定値が無効な場合
        """
        if not config.url or len(config.url.strip()) == 0:
            raise ConfigError("REDMINE_URL cannot be empty")
        
        if not config.api_key or len(config.api_key.strip()) == 0:
            raise ConfigError("REDMINE_API_KEY cannot be empty")
        
        # APIキーの長さをチェック（一般的なRedmine APIキーは40文字）
        if len(config.api_key.strip()) < 10:
            raise ConfigError(
                "REDMINE_API_KEY seems too short. "
                "Please check your API key."
            )
