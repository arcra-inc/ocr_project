"""
Form Parser Document AI処理モジュール（簡素化版）

Document AIのForm Parserを使用して、
座標や信頼度を含まないシンプルなフィールド抽出を行います。
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import mimetypes

from google.cloud import documentai_v1 as documentai
from google.oauth2 import service_account


def setup_form_parser_client(location: str = "us", service_account_key_path: Optional[Path] = None):
    """
    Form Parser用のDocument AIクライアントを初期化
    
    Args:
        location: Document AIのリージョン
        service_account_key_path: サービスアカウントキーファイルのパス
        
    Returns:
        tuple: (client, project_id)
    """
    if service_account_key_path and service_account_key_path.exists():
        # サービスアカウントキーを使用
        credentials = service_account.Credentials.from_service_account_file(
            str(service_account_key_path),
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        # プロジェクトIDをキーファイルから取得
        with open(service_account_key_path, 'r') as f:
            key_data = json.load(f)
        project_id = key_data.get('project_id')
        
        client = documentai.DocumentProcessorServiceClient(credentials=credentials)
    else:
        # デフォルト認証を使用
        client = documentai.DocumentProcessorServiceClient()
        import os
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT環境変数が設定されていません")
    
    return client, project_id


def process_document_with_form_parser(
    client: documentai.DocumentProcessorServiceClient,
    project_id: str,
    processor_id: str,
    file_path: Path,
    location: str = "us"
) -> tuple[documentai.Document, dict]:
    """
    Form Parserを使用してOCR処理を実行
    
    Args:
        client: Document AIクライアント
        project_id: Google CloudプロジェクトID
        processor_id: Form ParserプロセッサID
        file_path: 処理する画像ファイルのパス
        location: Document AIのリージョン
        
    Returns:
        tuple[Document, dict]: OCR処理結果とJSONレスポンス
    """
    # MIMEタイプを自動判定
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if not mime_type:
        if file_path.suffix.lower() in ['.jpg', '.jpeg']:
            mime_type = 'image/jpeg'
        elif file_path.suffix.lower() == '.png':
            mime_type = 'image/png'
        else:
            mime_type = 'application/octet-stream'
    
    # ファイルを読み込み
    with open(file_path, "rb") as image_file:
        image_content = image_file.read()
    
    # Document AIリクエストを作成
    raw_document = documentai.RawDocument(content=image_content, mime_type=mime_type)
    name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"
    request = documentai.ProcessRequest(name=name, raw_document=raw_document)
    
    # Form Parser処理を実行
    response = client.process_document(request)
    
    # レスポンスをJSONに変換
    from google.protobuf.json_format import MessageToDict
    response_json = MessageToDict(response._pb)
    
    return response.document, response_json


def extract_form_fields_from_response(document_ai_response: Dict) -> Dict[str, Any]:
    """
    Form ParserのレスポンスからformFieldsを抽出（簡素化版）
    
    Args:
        document_ai_response: Document AIのJSONレスポンス
        
    Returns:
        Dict: 抽出されたフォームフィールド情報（フィールド名と値のみ）
    """
    document = document_ai_response.get("document", {})
    pages = document.get("pages", [])
    
    if not pages:
        return {}
    
    # フォームフィールドを抽出
    all_fields = {}
    
    for page_idx, page in enumerate(pages):
        form_fields = page.get("formFields", [])
        
        for field_idx, form_field in enumerate(form_fields):
            # フィールド名（ラベル）を取得
            field_name_layout = form_field.get("fieldName", {})
            field_value_layout = form_field.get("fieldValue", {})
            
            # テキストアンカーからフィールド名と値を取得
            field_name = _extract_text_from_layout(field_name_layout, document.get("text", ""))
            field_value = _extract_text_from_layout(field_value_layout, document.get("text", ""))
            
            if field_name and field_value:
                all_fields[field_name] = field_value
            elif field_value and not field_name:
                # フィールド名がない場合は番号で管理
                all_fields[f"フィールド_{len(all_fields) + 1}"] = field_value
    
    return all_fields


def extract_entities_from_response(document_ai_response: Dict) -> Dict[str, Any]:
    """
    Document AIレスポンスからentitiesを抽出（簡素化版）
    
    Args:
        document_ai_response: Document AIのJSONレスポンス
        
    Returns:
        Dict: 抽出されたエンティティ情報（タイプと値のみ）
    """
    document = document_ai_response.get("document", {})
    entities = document.get("entities", [])
    
    if not entities:
        return {}
    
    extracted_entities = {}
    
    for entity in entities:
        entity_type = entity.get("type", "Unknown")
        mention_text = entity.get("mentionText", "").strip()
        
        if mention_text:  # 空でないテキストのみ
            if entity_type not in extracted_entities:
                extracted_entities[entity_type] = []
            
            extracted_entities[entity_type].append(mention_text)
    
    return extracted_entities


def create_combined_structured_output(document_ai_response: Dict) -> Dict[str, Any]:
    """
    Form ParserとEntityの両方から情報を抽出して統合（簡素化版）
    
    Args:
        document_ai_response: Document AIのJSONレスポンス
        
    Returns:
        Dict: 統合された構造化データ（フィールドと値のみ）
    """
    # フォームフィールドを抽出
    form_fields = extract_form_fields_from_response(document_ai_response)
    
    # エンティティを抽出
    entities = extract_entities_from_response(document_ai_response)
    
    # 統合結果を作成（シンプル構造）
    result = {}
    
    # フォームフィールドを追加
    if form_fields:
        result.update(form_fields)
    
    # エンティティを追加（重複しないように）
    if entities:
        for entity_type, entity_values in entities.items():
            if entity_values:  # 空でないエンティティのみ
                # 複数の値がある場合は配列、1つの場合は文字列
                if len(entity_values) == 1:
                    result[entity_type] = entity_values[0]
                else:
                    result[entity_type] = entity_values
    
    return result


def _extract_text_from_layout(layout: Dict, full_text: str) -> str:
    """レイアウト情報からテキストを抽出"""
    text_anchor = layout.get("textAnchor", {})
    text_segments = text_anchor.get("textSegments", [])
    
    if not text_segments:
        return ""
    
    # 複数のセグメントがある場合は結合
    extracted_texts = []
    for segment in text_segments:
        start_idx = int(segment.get("startIndex", 0))
        end_idx = int(segment.get("endIndex", start_idx))
        text = full_text[start_idx:end_idx].strip()
        if text:
            extracted_texts.append(text)
    
    return " ".join(extracted_texts)


if __name__ == "__main__":
    # テスト実行
    print("Form Parser Document AI処理モジュール（簡素化版）のテスト")
    print("実際の処理にはForm ParserプロセッサIDが必要です")