"""
Document AI処理モジュール
Document AIを使用したOCR処理の実装
"""

import mimetypes
from pathlib import Path
from typing import List, Dict, Any
from google.cloud import documentai


class DocumentAIProcessor:
    """Document AIプロセッサクラス"""
    
    def __init__(self, client: documentai.DocumentProcessorServiceClient, project_id: str, processor_id: str, location: str = "us"):
        """
        Args:
            client: Document AIクライアント
            project_id: Google CloudプロジェクトID
            processor_id: Document AIプロセッサID
            location: プロセッサのリージョン
        """
        self.client = client
        self.project_id = project_id
        self.processor_id = processor_id
        self.location = location
        self.processor_name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"
    
    def process_document(self, file_path: Path) -> documentai.Document:
        """
        ドキュメントを処理してOCR結果を取得
        
        Args:
            file_path: 処理するファイルのパス
            
        Returns:
            Document: OCR処理結果
        """
        # MIMEタイプを判定
        mime_type = self._get_mime_type(file_path)
        
        # ファイル読み込み
        with open(file_path, "rb") as file:
            image_content = file.read()
        
        # リクエスト作成
        raw_document = documentai.RawDocument(content=image_content, mime_type=mime_type)
        request = documentai.ProcessRequest(name=self.processor_name, raw_document=raw_document)
        
        # Document AI処理実行
        response = self.client.process_document(request)
        return response.document
    
    def _get_mime_type(self, file_path: Path) -> str:
        """ファイルのMIMEタイプを取得"""
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        if not mime_type:
            # 拡張子ベースでフォールバック
            suffix = file_path.suffix.lower()
            mime_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg', 
                '.png': 'image/png',
                '.tiff': 'image/tiff',
                '.tif': 'image/tiff',
                '.pdf': 'application/pdf'
            }
            mime_type = mime_map.get(suffix, 'application/octet-stream')
        
        return mime_type


class TextExtractor:
    """テキスト抽出クラス"""
    
    @staticmethod
    def extract_full_text(document: documentai.Document) -> str:
        """
        ドキュメント全文テキストを抽出
        
        Args:
            document: Document AI処理結果
            
        Returns:
            str: 全文テキスト
        """
        return document.text if document.text else ""
    
    @staticmethod
    def extract_blocks(document: documentai.Document) -> List[str]:
        """
        ブロック単位でテキストを抽出
        
        Args:
            document: Document AI処理結果
            
        Returns:
            List[str]: ブロック単位のテキストリスト
        """
        full_text = document.text
        blocks = []
        
        for page in document.pages:
            for block in page.blocks:
                block_text_parts = []
                if block.layout and block.layout.text_anchor:
                    for segment in block.layout.text_anchor.text_segments:
                        start_idx = segment.start_index if segment.start_index else 0
                        end_idx = segment.end_index if segment.end_index else len(full_text)
                        text_part = full_text[start_idx:end_idx]
                        block_text_parts.append(text_part)
                
                if block_text_parts:
                    blocks.append("".join(block_text_parts))
        
        return blocks
    
    @staticmethod
    def extract_paragraphs(document: documentai.Document) -> List[str]:
        """
        パラグラフ単位でテキストを抽出
        
        Args:
            document: Document AI処理結果
            
        Returns:
            List[str]: パラグラフ単位のテキストリスト
        """
        full_text = document.text
        paragraphs = []
        
        for page in document.pages:
            for paragraph in page.paragraphs:
                para_text_parts = []
                if paragraph.layout and paragraph.layout.text_anchor:
                    for segment in paragraph.layout.text_anchor.text_segments:
                        start_idx = segment.start_index if segment.start_index else 0
                        end_idx = segment.end_index if segment.end_index else len(full_text)
                        text_part = full_text[start_idx:end_idx]
                        para_text_parts.append(text_part)
                
                if para_text_parts:
                    paragraphs.append("".join(para_text_parts))
        
        return paragraphs
    
    @staticmethod
    def extract_lines(document: documentai.Document) -> List[str]:
        """
        行単位でテキストを抽出
        
        Args:
            document: Document AI処理結果
            
        Returns:
            List[str]: 行単位のテキストリスト
        """
        full_text = document.text
        lines = []
        
        for page in document.pages:
            for line in page.lines:
                line_text_parts = []
                if line.layout and line.layout.text_anchor:
                    for segment in line.layout.text_anchor.text_segments:
                        start_idx = segment.start_index if segment.start_index else 0
                        end_idx = segment.end_index if segment.end_index else len(full_text)
                        text_part = full_text[start_idx:end_idx]
                        line_text_parts.append(text_part)
                
                if line_text_parts:
                    lines.append("".join(line_text_parts))
        
        return lines
    
    @staticmethod
    def get_document_structure_info(document: documentai.Document) -> Dict[str, Any]:
        """
        ドキュメント構造情報を取得
        
        Args:
            document: Document AI処理結果
            
        Returns:
            Dict: 構造情報
        """
        info = {
            'total_pages': len(document.pages),
            'total_blocks': 0,
            'total_paragraphs': 0,
            'total_lines': 0,
            'text_length': len(document.text) if document.text else 0,
            'page_details': []
        }
        
        for i, page in enumerate(document.pages):
            page_info = {
                'page_number': i + 1,
                'blocks': len(page.blocks),
                'paragraphs': len(page.paragraphs),
                'lines': len(page.lines)
            }
            
            info['total_blocks'] += page_info['blocks']
            info['total_paragraphs'] += page_info['paragraphs']  
            info['total_lines'] += page_info['lines']
            info['page_details'].append(page_info)
        
        return info


if __name__ == "__main__":
    print("Document AI処理モジュールのテストを実行")
    print("このモジュールは他のスクリプトからimportして使用してください")