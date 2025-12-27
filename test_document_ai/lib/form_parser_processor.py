"""
Form Parser Document AI処理モジュール

Generic OCR ProcessorではなくForm Parserを使用して、
Document AIのモデル側で構造化データを自動抽出します。
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
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
        # 環境変数からプロジェクトIDを取得する必要があります
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
    Form ParserのレスポンスからformFieldsを抽出
    
    Args:
        document_ai_response: Document AIのJSONレスポンス
        
    Returns:
        Dict: 抽出されたフォームフィールド情報
    """
    document = document_ai_response.get("document", {})
    pages = document.get("pages", [])
    
    if not pages:
        return {"error": "No pages found"}
    
    # フォームフィールドを抽出
    extracted_fields = {}
    
    for page_idx, page in enumerate(pages):
        form_fields = page.get("formFields", [])
        
        page_fields = {}
        for field_idx, form_field in enumerate(form_fields):
            # フィールド名（ラベル）を取得
            field_name_layout = form_field.get("fieldName", {})
            field_value_layout = form_field.get("fieldValue", {})
            
            # テキストアンカーからフィールド名と値を取得
            field_name = _extract_text_from_layout(field_name_layout, document.get("text", ""))
            field_value = _extract_text_from_layout(field_value_layout, document.get("text", ""))
            
            # 信頼度を取得
            name_confidence = field_name_layout.get("confidence", 0.0)
            value_confidence = field_value_layout.get("confidence", 0.0)
            
            # 座標を取得
            name_coords = _extract_coordinates_from_layout(field_name_layout)
            value_coords = _extract_coordinates_from_layout(field_value_layout)
            
            if field_name or field_value:
                field_key = field_name if field_name else f"フィールド_{field_idx}"
                page_fields[field_key] = {
                    "フィールド名": field_name,
                    "値": field_value,
                    "フィールド名信頼度": round(name_confidence, 3),
                    "値信頼度": round(value_confidence, 3),
                    "フィールド名座標": name_coords,
                    "値座標": value_coords,
                    "検出方法": "Document AI Form Parser"
                }
        
        if page_fields:
            extracted_fields[f"ページ_{page_idx + 1}"] = page_fields
    
    return {
        "文書情報": {
            "処理日時": datetime.now().isoformat(),
            "ページ数": len(pages),
            "全文字数": len(document.get("text", "")),
            "処理方式": "Form Parser"
        },
        "抽出されたフォームフィールド": extracted_fields,
        "統計情報": {
            "総フィールド数": sum(len(fields) for fields in extracted_fields.values()),
            "ページ別フィールド数": {page: len(fields) for page, fields in extracted_fields.items()}
        }
    }


def extract_entities_from_response(document_ai_response: Dict) -> Dict[str, Any]:
    """
    Document AIレスポンスからentitiesを抽出
    
    Args:
        document_ai_response: Document AIのJSONレスポンス
        
    Returns:
        Dict: 抽出されたエンティティ情報
    """
    document = document_ai_response.get("document", {})
    entities = document.get("entities", [])
    
    if not entities:
        return {"message": "No entities found"}
    
    extracted_entities = {}
    
    for entity in entities:
        entity_type = entity.get("type", "Unknown")
        mention_text = entity.get("mentionText", "")
        confidence = entity.get("confidence", 0.0)
        
        # 正規化値があれば取得
        normalized_value = entity.get("normalizedValue", {})
        
        if entity_type not in extracted_entities:
            extracted_entities[entity_type] = []
        
        entity_info = {
            "テキスト": mention_text,
            "信頼度": round(confidence, 3),
            "検出方法": "Document AI Entity Extraction"
        }
        
        # 正規化値がある場合は追加
        if normalized_value:
            entity_info["正規化値"] = normalized_value
        
        extracted_entities[entity_type].append(entity_info)
    
    return {
        "抽出されたエンティティ": extracted_entities,
        "統計情報": {
            "エンティティタイプ数": len(extracted_entities),
            "総エンティティ数": sum(len(entities) for entities in extracted_entities.values()),
            "エンティティタイプ一覧": list(extracted_entities.keys())
        }
    }


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


def _extract_coordinates_from_layout(layout: Dict) -> Dict:
    """レイアウト情報から座標を抽出"""
    bounding_poly = layout.get("boundingPoly", {})
    normalized_vertices = bounding_poly.get("normalizedVertices", [])
    
    if not normalized_vertices:
        return {}
    
    x_coords = [v.get("x", 0.0) for v in normalized_vertices if "x" in v]
    y_coords = [v.get("y", 0.0) for v in normalized_vertices if "y" in v]
    
    if not x_coords or not y_coords:
        return {}
    
    return {
        "x_min": min(x_coords),
        "y_min": min(y_coords),
        "x_max": max(x_coords),
        "y_max": max(y_coords),
        "center_x": sum(x_coords) / len(x_coords),
        "center_y": sum(y_coords) / len(y_coords)
    }


def create_combined_structured_output(document_ai_response: Dict) -> Dict[str, Any]:
    """
    Form ParserとEntityの両方から情報を抽出して統合
    
    Args:
        document_ai_response: Document AIのJSONレスポンス
        
    Returns:
        Dict: 統合された構造化データ
    """
    # フォームフィールドを抽出
    form_fields_result = extract_form_fields_from_response(document_ai_response)
    
    # エンティティを抽出
    entities_result = extract_entities_from_response(document_ai_response)
    
    # 統合結果を作成
    combined_result = {
        "文書情報": form_fields_result.get("文書情報", {}),
        "Document AI抽出結果": {
            "フォームフィールド": form_fields_result.get("抽出されたフォームフィールド", {}),
            "エンティティ": entities_result.get("抽出されたエンティティ", {}),
        },
        "統計情報": {
            "フォームフィールド統計": form_fields_result.get("統計情報", {}),
            "エンティティ統計": entities_result.get("統計情報", {}),
            "抽出方式": "Document AI Form Parser + Entity Extraction"
        }
    }
    
    return combined_result


if __name__ == "__main__":
    # テスト実行
    print("Form Parser Document AI処理モジュールのテスト")
    print("実際の処理にはForm ParserプロセッサIDが必要です")