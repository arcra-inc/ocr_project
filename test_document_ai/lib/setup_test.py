"""
Document AI セットアップとテストスクリプト
"""

from pathlib import Path
from typing import Optional
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent  # lib/ から test_document_ai/ へ
sys.path.insert(0, str(project_root))

from lib.auth_setup import setup_credentials, create_document_ai_client, create_document_ai_client_from_key_file
from lib.document_processor import DocumentAIProcessor, TextExtractor


def test_authentication(service_account_key_path: Path = None):
    """認証テスト"""
    print("=== 認証テスト ===")
    try:
        credentials, project_id = setup_credentials(service_account_key_path)
        print(f"✓ 認証成功: プロジェクトID = {project_id}")
        return credentials, project_id
    except Exception as e:
        print(f"✗ 認証失敗: {e}")
        return None, None


def test_client_creation(location: str = "us", service_account_key_path: Path = None):
    """クライアント作成テスト"""
    print(f"\n=== Document AIクライアント作成テスト (location: {location}) ===")
    try:
        if service_account_key_path and service_account_key_path.exists():
            client, project_id = create_document_ai_client_from_key_file(service_account_key_path, location)
            print(f"✓ サービスアカウントキーを使用してDocument AIクライアントを作成: {project_id}")
        else:
            client = create_document_ai_client(location)
            print("✓ デフォルト認証でDocument AIクライアントを作成")
        return client
    except Exception as e:
        print(f"✗ クライアント作成失敗: {e}")
        return None


def test_processor_setup(client, project_id: str, processor_id: str, location: str):
    """プロセッサセットアップテスト"""
    print(f"\n=== プロセッサセットアップテスト ===")
    try:
        processor = DocumentAIProcessor(client, project_id, processor_id, location)
        print(f"✓ プロセッサセットアップ成功")
        print(f"  プロセッサ名: {processor.processor_name}")
        return processor
    except Exception as e:
        print(f"✗ プロセッサセットアップ失敗: {e}")
        return None


def test_document_processing(processor: DocumentAIProcessor, test_image_path: Path):
    """ドキュメント処理テスト"""
    print(f"\n=== ドキュメント処理テスト ===")
    if not test_image_path.exists():
        print(f"✗ テスト画像が見つかりません: {test_image_path}")
        return None
    
    try:
        print(f"処理中: {test_image_path}")
        document = processor.process_document(test_image_path)
        
        # テキスト抽出テスト
        full_text = TextExtractor.extract_full_text(document)
        blocks = TextExtractor.extract_blocks(document)
        paragraphs = TextExtractor.extract_paragraphs(document)
        lines = TextExtractor.extract_lines(document)
        
        # 構造情報取得
        structure_info = TextExtractor.get_document_structure_info(document)
        
        print("✓ ドキュメント処理成功")
        print(f"  全文文字数: {len(full_text)}")
        print(f"  ブロック数: {len(blocks)}")
        print(f"  パラグラフ数: {len(paragraphs)}")
        print(f"  行数: {len(lines)}")
        print(f"  ページ数: {structure_info['total_pages']}")
        
        if full_text:
            print(f"  テキストプレビュー: {full_text[:100]}{'...' if len(full_text) > 100 else ''}")
        
        return document
        
    except Exception as e:
        print(f"✗ ドキュメント処理失敗: {e}")
        return None


def main(processor_id: str, location: str, service_account_key_path: Optional[Path] = None):
    """メインテスト関数"""
    print("Document AI セットアップとテスト")
    print("=" * 50)
    
    # テスト用画像パス
    current_dir = Path(__file__).parent.parent 
    test_image_path = current_dir / "documents" / "images" / "test" / "sample.png"
    
    print(f"プロセッサID: {processor_id}")
    print(f"リージョン: {location}")
    print(f"サービスアカウントキー: {service_account_key_path or 'デフォルト認証を使用'}")
    print(f"テスト画像: {test_image_path}")
    print()
    
    # 1. 認証テスト
    credentials, project_id = test_authentication(service_account_key_path)
    if not credentials or not project_id:
        print("\n認証に失敗しました。セットアップ手順:")
        print("1. Google Cloud SDKをインストール")
        print("2. gcloud auth application-default login を実行")
        print("3. または、サービスアカウントキーファイルのパスを service_account_key_path に設定")
        return False
    
    # 2. クライアント作成テスト
    client = test_client_creation(location, service_account_key_path)
    if not client:
        return False
    
    # 3. プロセッサセットアップテスト
    if processor_id == "YOUR_PROCESSOR_ID_HERE":
        print(f"\n[警告] プロセッサIDがデフォルトのままです: {processor_id}")
        print("Google Cloud ConsoleでDocument AIプロセッサを作成し、")
        print("そのプロセッサIDを processor_id 変数に設定してください")
        return False
    
    # プロセッサが設定されている場合はテストを継続
    print(f"\n[情報] プロセッサID '{processor_id}' をテストします")
    
    processor = test_processor_setup(client, project_id, processor_id, location)
    if not processor:
        return False
    
    # 4. ドキュメント処理テスト（テスト画像がある場合）
    if test_image_path.exists():
        document = test_document_processing(processor, test_image_path)
        if document:
            print("\n✓ 全てのテストが成功しました！")
            return True
    else:
        print(f"\n[情報] テスト画像がありません: {test_image_path}")
        print("テスト画像を配置してドキュメント処理をテストしてください")
        print("✓ 認証とクライアント作成は成功しました")
        return True
    
    return False


if __name__ == "__main__":
    # ===== 設定ここから =====
    # Document AI プロセッサ設定
    processor_id = "1d1c870c661d0805"  # 実際のプロセッサIDに置き換え
    location = "us"
    
    # サービスアカウントキーファイルのパス（オプション）
    # None に設定するとデフォルト認証（ADC）を使用します
    service_account_key_path = Path(r"C:\Users\NakanoShiryu\Downloads\project-7ab97012-eca6-4d91-8e4-82f6cf52e321.json")
    # 例: service_account_key_path = Path(r"C:\path\to\your\service-account-key.json")
    # ===== 設定ここまで =====
    
    success = main(processor_id, location, service_account_key_path)
    if success:
        print("\nDocument AIの設定が完了しました！")
        print("main.pyを実行してOCR処理を開始できます")
    else:
        print("\nセットアップに問題があります。上記のエラーを確認してください")
    
    sys.exit(0 if success else 1)