from __future__ import annotations

import json
import mimetypes
from pathlib import Path
from typing import List, Optional, Dict, Any

import google.auth
from google.api_core.client_options import ClientOptions
from google.cloud import documentai


def setup_document_ai_client(
    location: str, 
    service_account_key_path: Optional[str] = None
) -> tuple[documentai.DocumentProcessorServiceClient, str]:
    """
    Document AIクライアントをセットアップ
    
    Args:
        location: Document AIのリージョン
        service_account_key_path: サービスアカウントキーファイルのパス（オプション）
        
    Returns:
        tuple: (Document AIクライアント, プロジェクトID)
    """
    # 認証情報を取得
    if service_account_key_path:
        from google.oauth2 import service_account
        credential = service_account.Credentials.from_service_account_file(
            service_account_key_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        project_id = credential.project_id
    else:
        credential, project_id = google.auth.default()
        auth_req = google.auth.transport.requests.Request()
        credential.refresh(auth_req)
    
    # クライアントを作成
    opts = ClientOptions(
        api_endpoint=f"{location}-documentai.googleapis.com", 
        quota_project_id=project_id
    )
    client = documentai.DocumentProcessorServiceClient(
        client_options=opts, 
        credentials=credential
    )
    
    return client, project_id



def main(
    images_dir: Path, 
    output_dir: Path, 
    processor_id: str,
    location: str,
    exts: set,
    service_account_key_path: Optional[str] = None,
    output_text: bool = True,
    output_raw_json: bool = True, 
    output_structured_json: bool = True
):
    """
    Document AI Form Parserを使用してOCR処理を実行
    
    Args:
        images_dir: 処理する画像ファイルが格納されているディレクトリ
        output_dir: OCR結果のテキストファイルを保存するディレクトリ  
        processor_id: Document AI Form ParserプロセッサID
        location: Document AIのリージョン
        exts: 対象とする画像の拡張子セット
        service_account_key_path: サービスアカウントキーファイルのパス（オプション）
        output_text: テキストファイル出力フラグ
        output_raw_json: 生JSONファイル出力フラグ
        output_structured_json: 構造化JSONファイル出力フラグ
    """
    if exts is None:
        exts = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".pdf"}
    
    # ディレクトリの存在確認
    if not images_dir.exists():
        raise FileNotFoundError(f"images_dir not found: {images_dir}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 処理対象の画像ファイルを取得
    image_paths: List[Path] = [
        p for p in images_dir.iterdir() 
        if p.is_file() and p.suffix.lower() in exts
    ]
    
    if not image_paths:
        print(f"No images found in: {images_dir}")
        return
    
    # Document AIクライアントをセットアップ
    try:
        client, project_id = setup_document_ai_client(location, service_account_key_path)
        print(f"Document AIクライアントを初期化しました (プロジェクト: {project_id})")
    except Exception as e:
        print(f"Document AIクライアントの初期化に失敗: {e}")
        print("Google Cloud認証が正しく設定されているか確認してください")
        return
    
    ok = 0
    ng = 0
    
    for img_path in image_paths:
        try:
            print(f"処理中: {img_path.name}")
            
            # Form Parserを使用してDocument AIのモデル側で構造抽出（パターンマッチング不使用）
            from lib.form_parser_processor import process_document_with_form_parser, create_combined_structured_output
            
            document, response_json = process_document_with_form_parser(client, project_id, processor_id, img_path, location)
            
            # 出力カウント
            generated_files = []
            
            # 1. テキストファイル出力（フラグ制御）
            if output_text:
                full_text = document.text if document.text else ""
                text_file = output_dir / f"{img_path.stem}_text.txt"
                text_file.write_text(full_text, encoding="utf-8")
                generated_files.append(f"テキスト: {text_file.name} ({len(full_text)} 文字)")
            
            # 2. 生JSONファイル出力（フラグ制御）
            if output_raw_json:
                json_file = output_dir / f"{img_path.stem}_raw_response.json"
                json_file.write_text(json.dumps(response_json, ensure_ascii=False, indent=2), encoding="utf-8")
                generated_files.append(f"生JSON: {json_file.name} ({json_file.stat().st_size} bytes)")
            
            # 3. 構造化JSONファイル出力（フラグ制御）
            if output_structured_json:
                form_parser_data = create_combined_structured_output(response_json)
                structured_file = output_dir / f"{img_path.stem}_structured_fields.json"
                structured_file.write_text(json.dumps(form_parser_data, ensure_ascii=False, indent=2), encoding="utf-8")
                generated_files.append(f"構造化JSON: {structured_file.name} (フィールド数: {len(form_parser_data)}個)")
            
            # 結果表示
            file_count = len(generated_files)
            print(f"[OK] {img_path.name} -> {file_count}ファイル生成")
            for file_info in generated_files:
                print(f"     {file_info}")
            ok += 1
            
        except Exception as e:
            print(f"[NG] {img_path.name} -> エラー: {e}")
            ng += 1
    
    print(f"処理完了. 成功={ok}, 失敗={ng}, 合計={len(image_paths)}")


if __name__ == "__main__":
    import sys
    
    # コマンドライン引数の確認
    if len(sys.argv) > 1 and sys.argv[1] == "setup_test":
        # セットアップテストを実行
        from lib.setup_test import main as setup_main
        
        # デフォルト設定でセットアップテスト実行
        processor_id = "1d1c870c661d0805"  # 実際のプロセッサIDを設定
        location = "us"
        service_account_key_path = Path(r"C:\Users\NakanoShiryu\Downloads\project-7ab97012-eca6-4d91-8e4-82f6cf52e321.json")
        
        print("Document AI セットアップテストを実行します")
        print("設定を変更する場合は lib/setup_test.py を直接編集してください")
        print()
        
        success = setup_main(processor_id, location, service_account_key_path)
        if success:
            print("\nセットアップテストが完了しました！")
            print("main.pyを実行してOCR処理を開始できます")
        else:
            print("\nセットアップに問題があります。上記のエラーを確認してください")
        sys.exit(0 if success else 1)
    
    # ===== 設定ここから =====
    # 現在のファイルを基準とした相対パスを使用
    current_dir = Path(__file__).parent
    images_dir = current_dir / "documents" / "images" / "test"
    output_dir = current_dir / "documents" / "ocr_results" / "test"
    
    #images_dir = current_dir / "documents" / "images" / "one_file"
    #output_dir = current_dir / "documents" / "ocr_results" / "one_file"
    
    # Document AIプロセッサの設定
    #processor_id = "1d1c870c661d0805"  # 実際のプロセッサID
    location = "us"  # プロセッサのリージョン（通常は "us" または "eu"）
    # Parserプロセッサを使用する場合は以下
    processor_id = "41fc98b4e98caeae"
    
    # 認証設定（どちらか一つを選択）
    # オプション1: Application Default Credentials (ADC) を使用
    # service_account_key_path = None
    
    # オプション2: サービスアカウントキーファイルを使用
    service_account_key_path = r"C:\Users\NakanoShiryu\Downloads\project-7ab97012-eca6-4d91-8e4-82f6cf52e321.json"
    
    # 対象拡張子
    exts = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".pdf"}
    
    # ===== 出力ファイル制御フラグ =====
    output_text = False            # テキストファイル(.txt)出力
    output_raw_json = False        # 生JSONファイル(.json)出力  
    output_structured_json = True # 構造化JSONファイル(.json)出力
    # ===== 設定ここまで =====
    
    print("Document AI OCR処理を開始します")
    print(f"画像ディレクトリ: {images_dir}")
    print(f"出力ディレクトリ: {output_dir}")
    print(f"プロセッサID: {processor_id}")
    print(f"処理モード: Form Parser (モデル側構造抽出 - パターンマッチング不使用)")
    print(f"出力設定: テキスト={output_text}, 生JSON={output_raw_json}, 構造化JSON={output_structured_json}")
    print(f"画像ディレクトリ存在確認: {images_dir.exists()}")
    if service_account_key_path:
        print(f"認証方法: サービスアカウントキーファイル ({service_account_key_path})")
    else:
        print("認証方法: Application Default Credentials (ADC)")
    
    if processor_id == "YOUR_PROCESSOR_ID_HERE":
        print("\n[警告] プロセッサIDが設定されていません!")
        print("main.pyの processor_id 変数を実際のDocument AIプロセッサIDに設定してください")
        exit(1)
    
    main(images_dir, output_dir, processor_id, location, exts, service_account_key_path, 
            output_text, output_raw_json, output_structured_json)