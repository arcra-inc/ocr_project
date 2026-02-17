"""
Document AI認証設定モジュール
Google Cloud認証の設定を管理します
"""

import os
from pathlib import Path
import google.auth
from google.oauth2 import service_account
from google.auth import load_credentials_from_file
from google.api_core.client_options import ClientOptions
from google.cloud import documentai


def setup_credentials(service_account_key_path: Path = None) -> tuple:
    """
    Google Cloud認証情報をセットアップ
    
    Args:
        service_account_key_path: サービスアカウントキーファイルのパス（オプション）
        
    Returns:
        tuple: (認証情報, プロジェクトID)
    """
    if service_account_key_path and service_account_key_path.exists():
        # サービスアカウントキーファイルから認証情報を読み込み
        print(f"サービスアカウントキーを使用: {service_account_key_path}")
        
        # Document AI用のスコープを明示的に設定
        credentials = service_account.Credentials.from_service_account_file(
            str(service_account_key_path),
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        project_id = credentials.project_id
        return credentials, project_id
    
    # デフォルト認証情報を取得（ADCまたは環境変数から）
    try:
        credentials, project_id = google.auth.default()
        print("デフォルト認証情報を使用")
        return credentials, project_id
    except Exception as e:
        raise RuntimeError(f"Google Cloud認証に失敗しました: {e}")


def create_document_ai_client_from_key_file(
    service_account_key_path: Path, 
    location: str = "us"
) -> tuple[documentai.DocumentProcessorServiceClient, str]:
    """
    サービスアカウントキーファイルからDocument AIクライアントを作成
    
    Args:
        service_account_key_path: サービスアカウントキーファイルのパス
        location: Document AIのリージョン
        
    Returns:
        tuple: (Document AIクライアント, プロジェクトID)
    """
    if not service_account_key_path.exists():
        raise FileNotFoundError(f"サービスアカウントキーファイルが見つかりません: {service_account_key_path}")
    
    # キーファイルから認証情報を読み込み（適切なスコープ付き）
    credentials = service_account.Credentials.from_service_account_file(
        str(service_account_key_path),
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    project_id = credentials.project_id
    
    # 認証情報を更新
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    
    # クライアントオプションを設定
    opts = ClientOptions(
        api_endpoint=f"{location}-documentai.googleapis.com",
        quota_project_id=project_id
    )
    
    # クライアントを作成
    client = documentai.DocumentProcessorServiceClient(
        client_options=opts,
        credentials=credentials
    )
    
    return client, project_id


def create_document_ai_client(location: str = "us", credentials=None, project_id=None) -> documentai.DocumentProcessorServiceClient:
    """
    Document AIクライアントを作成
    
    Args:
        location: Document AIのリージョン
        credentials: Google Cloud認証情報
        project_id: Google CloudプロジェクトID
        
    Returns:
        DocumentProcessorServiceClient: Document AIクライアント
    """
    if credentials is None or project_id is None:
        credentials, project_id = setup_credentials()
    
    # 認証情報を更新
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    
    # クライアントオプションを設定
    opts = ClientOptions(
        api_endpoint=f"{location}-documentai.googleapis.com",
        quota_project_id=project_id
    )
    
    # クライアントを作成
    client = documentai.DocumentProcessorServiceClient(
        client_options=opts,
        credentials=credentials
    )
    
    return client


if __name__ == "__main__":
    # 認証テスト
    try:
        credentials, project_id = setup_credentials()
        print(f"認証成功: プロジェクトID = {project_id}")
        
        client = create_document_ai_client()
        print("Document AIクライアントの作成に成功しました")
        
    except Exception as e:
        print(f"認証エラー: {e}")
        print("\n認証設定のヒント:")
        print("1. gcloud auth application-default login を実行")
        print("2. GOOGLE_APPLICATION_CREDENTIALS環境変数にサービスアカウントキーのパスを設定")
        print("3. サービスアカウントキーファイルをプロジェクトに配置")