"""
帳票フィールド抽出・構造化モジュール

Document AIのJSONレスポンスから帳票のフィールドを抽出し、
構造化されたJSONとして出力する機能を提供します。
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import re
from datetime import datetime


class FormFieldExtractor:
    """帳票フィールド抽出器"""
    
    def __init__(self, field_definitions: Optional[Dict] = None):
        """
        初期化
        
        Args:
            field_definitions: フィールド定義辞書（座標ベースまたはキーワードベース）
        """
        self.field_definitions = field_definitions or self._get_default_field_definitions()
        self.page_width = None
        self.page_height = None
    
    def _get_default_field_definitions(self) -> Dict:
        """
        デフォルトのフィールド定義を取得
        
        Returns:
            Dict: フィールド定義辞書
        """
        return {
            # 座標ベースのフィールド定義（正規化座標 0-1）
            "coordinate_fields": {
                "header_area": {"x_min": 0.0, "y_min": 0.0, "x_max": 1.0, "y_max": 0.3},
                "body_area": {"x_min": 0.0, "y_min": 0.3, "x_max": 1.0, "y_max": 0.8},
                "footer_area": {"x_min": 0.0, "y_min": 0.8, "x_max": 1.0, "y_max": 1.0}
            },
            
            # 具体的な帳票フィールド定義
            "form_fields": {
                "氏名": {
                    "keywords": ["氏名", "名前", "姓名", "申請者名", "担当者名", "お名前"],
                    "context_keywords": ["様", "殿", "氏"],
                    "field_type": "person_name"
                },
                "金額": {
                    "keywords": ["金額", "料金", "価格", "合計", "小計", "税込", "税抜"],
                    "context_keywords": ["円", "￥", "¥", "万円", "千円"],
                    "field_type": "amount"
                },
                "住所": {
                    "keywords": ["住所", "所在地", "居住地", "連絡先", "郵便番号"],
                    "context_keywords": ["県", "市", "町", "村", "丁目", "番地", "号"],
                    "field_type": "address"
                },
                "電話番号": {
                    "keywords": ["電話番号", "TEL", "Tel", "携帯", "連絡先"],
                    "context_keywords": ["-", "－", "（", "）"],
                    "field_type": "phone"
                },
                "日付": {
                    "keywords": ["日付", "年月日", "作成日", "申請日", "提出日"],
                    "context_keywords": ["令和", "平成", "年", "月", "日"],
                    "field_type": "date"
                },
                "会社名": {
                    "keywords": ["会社名", "法人名", "団体名", "組織名", "所属"],
                    "context_keywords": ["株式会社", "有限会社", "合同会社", "㈱", "㈲", "法人"],
                    "field_type": "company"
                },
                "部署": {
                    "keywords": ["部署", "部門", "課", "部", "係", "室", "グループ"],
                    "context_keywords": ["所属", "担当"],
                    "field_type": "department"
                },
                "メールアドレス": {
                    "keywords": ["メール", "email", "E-mail", "電子メール"],
                    "context_keywords": ["@", ".com", ".jp", ".net"],
                    "field_type": "email"
                }
            }
        }
    
    def process_document_json(self, json_data: Dict) -> Dict[str, Any]:
        """
        Document AIのJSONから構造化フィールドを抽出
        
        Args:
            json_data: Document AIのレスponseJSON
            
        Returns:
            Dict: 構造化されたフィールド情報
        """
        document = json_data.get("document", {})
        pages = document.get("pages", [])
        
        if not pages:
            return {"error": "No pages found in document"}
        
        # 最初のページを処理（複数ページ対応は後で拡張）
        page = pages[0]
        self.page_width = page.get("dimension", {}).get("width", 1.0)
        self.page_height = page.get("dimension", {}).get("height", 1.0)
        
        result = {
            "document_info": {
                "page_count": len(pages),
                "page_dimensions": {
                    "width": self.page_width,
                    "height": self.page_height,
                    "unit": page.get("dimension", {}).get("unit", "pixels")
                },
                "detected_languages": page.get("detectedLanguages", []),
                "processed_at": datetime.now().isoformat()
            },
            "extracted_fields": {},
            "raw_text_elements": []
        }
        
        # 全文テキストを取得
        full_text = document.get("text", "")
        
        # トークンレベルの詳細情報を抽出
        tokens = self._extract_tokens(page, full_text)
        result["raw_text_elements"] = tokens
        
        # フィールドを抽出
        result["extracted_fields"] = self._extract_fields(tokens, full_text)
        
        return result
    
    def _extract_tokens(self, page: Dict, full_text: str) -> List[Dict]:
        """
        ページからトークン情報を抽出
        
        Args:
            page: ページ情報
            full_text: 全文テキスト
            
        Returns:
            List[Dict]: トークン情報のリスト
        """
        tokens = []
        
        for token_idx, token in enumerate(page.get("tokens", [])):
            layout = token.get("layout", {})
            text_anchor = layout.get("textAnchor", {})
            segments = text_anchor.get("textSegments", [])
            
            if segments:
                segment = segments[0]
                start_idx = int(segment.get("startIndex", 0))
                end_idx = int(segment.get("endIndex", start_idx))
                text = full_text[start_idx:end_idx]
                
                # バウンディングボックスを正規化
                bounding_poly = layout.get("boundingPoly", {})
                normalized_coords = self._get_normalized_coordinates(bounding_poly)
                
                token_info = {
                    "token_id": token_idx,
                    "text": text,
                    "confidence": layout.get("confidence", 0.0),
                    "coordinates": normalized_coords,
                    "text_indices": {"start": start_idx, "end": end_idx},
                    "detected_break": token.get("detectedBreak", {}),
                    "detected_languages": token.get("detectedLanguages", [])
                }
                
                tokens.append(token_info)
        
        return tokens
    
    def _get_normalized_coordinates(self, bounding_poly: Dict) -> Dict:
        """
        バウンディングボックスの座標を正規化
        
        Args:
            bounding_poly: Document AIのバウンディングポリゴン
            
        Returns:
            Dict: 正規化された座標情報
        """
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
            "center_y": sum(y_coords) / len(y_coords),
            "vertices": normalized_vertices
        }
    
    def _extract_fields(self, tokens: List[Dict], full_text: str) -> Dict[str, Any]:
        """
        トークンからフィールド情報を抽出
        
        Args:
            tokens: トークン情報のリスト
            full_text: 全文テキスト
            
        Returns:
            Dict: 抽出されたフィールド情報
        """
        fields = {}
        
        # 座標ベースのフィールド抽出
        coordinate_fields = self._extract_coordinate_based_fields(tokens)
        fields.update(coordinate_fields)
        
        # 新しい構造化フォームフィールド抽出
        form_fields = self._extract_structured_form_fields(tokens, full_text)
        fields.update(form_fields)
        
        # パターンベースのフィールド抽出
        pattern_fields = self._extract_pattern_based_fields(tokens, full_text)
        fields.update(pattern_fields)
        
        return fields
    
    def _extract_coordinate_based_fields(self, tokens: List[Dict]) -> Dict[str, List[Dict]]:
        """
        座標ベースでフィールドを抽出
        """
        coordinate_fields = self.field_definitions.get("coordinate_fields", {})
        result = {}
        
        for field_name, area in coordinate_fields.items():
            field_tokens = []
            
            for token in tokens:
                coords = token.get("coordinates", {})
                if not coords:
                    continue
                
                # トークンが指定エリア内にあるかチェック
                if (area["x_min"] <= coords.get("center_x", 0) <= area["x_max"] and
                    area["y_min"] <= coords.get("center_y", 0) <= area["y_max"]):
                    field_tokens.append({
                        "text": token["text"],
                        "confidence": token["confidence"],
                        "coordinates": coords
                    })
            
            if field_tokens:
                result[field_name] = {
                    "tokens": field_tokens,
                    "combined_text": "".join([t["text"] for t in field_tokens]),
                    "area_definition": area
                }
        
        return result

    def _extract_structured_form_fields(self, tokens: List[Dict], full_text: str) -> Dict[str, Any]:
        """
        構造化されたフォームフィールドを抽出（氏名、金額など）
        
        Args:
            tokens: トークン情報のリスト
            full_text: 全文テキスト
            
        Returns:
            Dict: 構造化されたフィールド情報
        """
        form_fields = self.field_definitions.get("form_fields", {})
        structured_result = {}
        
        for field_name, definition in form_fields.items():
            field_info = self._extract_single_field(field_name, definition, tokens, full_text)
            if field_info:
                structured_result[field_name] = field_info
        
        return {"structured_fields": structured_result}

    def _extract_single_field(self, field_name: str, definition: Dict, tokens: List[Dict], full_text: str) -> Optional[Dict]:
        """
        単一フィールドの抽出
        
        Args:
            field_name: フィールド名
            definition: フィールド定義
            tokens: トークン情報
            full_text: 全文テキスト
            
        Returns:
            Optional[Dict]: 抽出されたフィールド情報
        """
        keywords = definition.get("keywords", [])
        context_keywords = definition.get("context_keywords", [])
        field_type = definition.get("field_type", "unknown")
        
        found_values = []
        
        # キーワードを含むトークンとその周辺を検索
        for i, token in enumerate(tokens):
            token_text = token["text"]
            
            # メインキーワードのマッチング
            for keyword in keywords:
                if keyword in token_text:
                    # 周辺トークンから値を抽出
                    field_value = self._extract_field_value_from_context(
                        tokens, i, field_type, context_keywords
                    )
                    if field_value:
                        found_values.append({
                            "value": field_value["text"],
                            "confidence": field_value["confidence"],
                            "coordinates": field_value.get("coordinates", {}),
                            "keyword_matched": keyword,
                            "extraction_method": field_value["method"]
                        })
        
        # 文脈キーワードによる追加検索
        for context_keyword in context_keywords:
            for i, token in enumerate(tokens):
                if context_keyword in token["text"]:
                    field_value = self._extract_field_value_from_context(
                        tokens, i, field_type, [], reverse_search=True
                    )
                    if field_value:
                        # 重複チェック
                        if not any(v["value"] == field_value["text"] for v in found_values):
                            found_values.append({
                                "value": field_value["text"],
                                "confidence": field_value["confidence"],
                                "coordinates": field_value.get("coordinates", {}),
                                "context_keyword_matched": context_keyword,
                                "extraction_method": field_value["method"]
                            })
        
        if found_values:
            return {
                "field_type": field_type,
                "found_count": len(found_values),
                "values": found_values,
                "best_match": max(found_values, key=lambda x: x["confidence"]) if found_values else None
            }
        
        return None

    def _extract_field_value_from_context(self, tokens: List[Dict], keyword_idx: int, field_type: str, 
                                        context_keywords: List[str], reverse_search: bool = False) -> Optional[Dict]:
        """
        キーワード周辺から実際のフィールド値を抽出
        
        Args:
            tokens: トークン情報
            keyword_idx: キーワードトークンのインデックス
            field_type: フィールドタイプ
            context_keywords: 文脈キーワード
            reverse_search: 逆方向検索（文脈キーワードの前を検索）
            
        Returns:
            Optional[Dict]: 抽出された値情報
        """
        search_range = 5  # 検索範囲
        
        if reverse_search:
            # 文脈キーワードの前を検索
            start_idx = max(0, keyword_idx - search_range)
            end_idx = keyword_idx
            search_tokens = tokens[start_idx:end_idx]
        else:
            # キーワードの後を検索
            start_idx = keyword_idx + 1
            end_idx = min(len(tokens), keyword_idx + search_range)
            search_tokens = tokens[start_idx:end_idx]
        
        for token in search_tokens:
            token_text = token["text"].strip()
            if not token_text or len(token_text) < 1:
                continue
            
            # フィールドタイプに応じた値の判定
            if self._is_valid_field_value(token_text, field_type, context_keywords):
                return {
                    "text": token_text,
                    "confidence": token["confidence"],
                    "coordinates": token.get("coordinates", {}),
                    "method": f"{field_type}_pattern_match"
                }
        
        return None

    def _is_valid_field_value(self, text: str, field_type: str, context_keywords: List[str]) -> bool:
        """
        フィールドタイプに基づいて値が有効かどうかを判定
        
        Args:
            text: 検証するテキスト
            field_type: フィールドタイプ
            context_keywords: 文脈キーワード
            
        Returns:
            bool: 有効な値かどうか
        """
        text = text.strip()
        
        if field_type == "person_name":
            # 人名：ひらがな、カタカナ、漢字、英字を含む2文字以上
            return bool(re.search(r'[ひ-ゞァ-ヾ一-龯a-zA-Z]{2,}', text))
        
        elif field_type == "amount":
            # 金額：数字と通貨記号を含む
            return bool(re.search(r'[\d,\.,，．]+', text)) and len(text) >= 1
        
        elif field_type == "address":
            # 住所：都道府県、市区町村、番地を示すキーワードを含む
            return bool(re.search(r'[都道府県市区町村丁目番地号]', text)) or len(text) >= 4
        
        elif field_type == "phone":
            # 電話番号：数字とハイフンを含む
            return bool(re.search(r'[\d\-－（）()]+', text)) and len(text) >= 8
        
        elif field_type == "date":
            # 日付：年月日の形式
            return bool(re.search(r'[\d年月日令和平成]', text))
        
        elif field_type == "company":
            # 会社名：会社を示すキーワードまたは長めのテキスト
            return bool(re.search(r'[株式会社有限会社㈱㈲法人]', text)) or len(text) >= 3
        
        elif field_type == "department":
            # 部署名：部署を示すキーワードを含む
            return bool(re.search(r'[部課係室グループ]', text)) or len(text) >= 2
        
        elif field_type == "email":
            # メールアドレス：@マークを含む
            return '@' in text and '.' in text
        
        return len(text) >= 2  # デフォルト：2文字以上
    
    def _extract_pattern_based_fields(self, tokens: List[Dict], full_text: str) -> Dict[str, List[Dict]]:
        """
        パターンベースでフィールドを抽出（数字、日付など）
        """
        result = {
            "dates": [],
            "numbers": [],
            "phone_numbers": []
        }
        
        # 日付パターン
        date_patterns = [
            r'令和\s*\d+\s*年\s*\d+\s*月\s*\d+\s*日',
            r'\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日'
        ]
        
        # 電話番号パターン  
        phone_patterns = [
            r'\d{2,5}[-\s]?\d{2,4}[-\s]?\d{2,4}',
            r'\d{2,5}'
        ]
        
        # 数字パターン
        number_patterns = [
            r'\d+\s*本',
            r'\d+\s*枚',
            r'\d+\.?\d*'
        ]
        
        for token in tokens:
            text = token["text"]
            
            # 日付検出
            for pattern in date_patterns:
                if re.search(pattern, text):
                    result["dates"].append({
                        "text": text,
                        "coordinates": token["coordinates"],
                        "confidence": token["confidence"],
                        "pattern": pattern
                    })
            
            # 電話番号検出
            for pattern in phone_patterns:
                match = re.search(pattern, text)
                if match and len(match.group()) >= 4:  # 最低4桁
                    result["phone_numbers"].append({
                        "text": text,
                        "matched_value": match.group(),
                        "coordinates": token["coordinates"],
                        "confidence": token["confidence"]
                    })
            
            # 数字検出
            for pattern in number_patterns:
                match = re.search(pattern, text)
                if match:
                    result["numbers"].append({
                        "text": text,
                        "matched_value": match.group(),
                        "coordinates": token["coordinates"],
                        "confidence": token["confidence"],
                        "pattern_type": pattern
                    })
        
        return result
    
    def _get_context_tokens(self, tokens: List[Dict], center_idx: int, radius: int = 2) -> List[Dict]:
        """
        指定されたトークンの周辺トークンを取得
        """
        start_idx = max(0, center_idx - radius)
        end_idx = min(len(tokens), center_idx + radius + 1)
        return tokens[start_idx:end_idx]

    def generate_final_structured_json(self, extracted_result: Dict) -> Dict[str, Any]:
        """
        最終的な構造化JSONを生成
        
        Args:
            extracted_result: 抽出結果
            
        Returns:
            Dict: 構造化されたフィールド情報のJSONフォーマット
        """
        structured_fields = extracted_result.get("extracted_fields", {}).get("structured_fields", {})
        
        # フィールド名と値をクリーンアップして整理
        final_fields = {}
        
        for field_name, field_info in structured_fields.items():
            if field_info and field_info.get("best_match"):
                best_match = field_info["best_match"]
                final_fields[field_name] = {
                    "値": best_match["value"],
                    "信頼度": round(best_match["confidence"], 3),
                    "フィールドタイプ": field_info["field_type"],
                    "検出方法": best_match.get("extraction_method", "unknown"),
                    "座標": best_match.get("coordinates", {}),
                    "候補数": field_info["found_count"]
                }
                
                # 複数の候補がある場合は全て含める
                if field_info["found_count"] > 1:
                    final_fields[field_name]["その他の候補"] = [
                        {
                            "値": v["value"],
                            "信頼度": round(v["confidence"], 3)
                        }
                        for v in field_info["values"]
                        if v != best_match
                    ]
        
        # 日付、数字、電話番号などのパターンベース抽出結果も含める
        pattern_fields = {}
        for key in ["dates", "numbers", "phone_numbers"]:
            pattern_data = extracted_result.get("extracted_fields", {}).get(key, [])
            if pattern_data:
                pattern_fields[key] = [
                    {
                        "値": item.get("matched_value", item.get("text", "")),
                        "信頼度": round(item["confidence"], 3),
                        "座標": item.get("coordinates", {})
                    }
                    for item in pattern_data[:5]  # 上位5件
                ]
        
        return {
            "文書情報": {
                "処理日時": extracted_result.get("document_info", {}).get("processed_at", ""),
                "ページ数": extracted_result.get("document_info", {}).get("page_count", 0),
                "ページサイズ": extracted_result.get("document_info", {}).get("page_dimensions", {})
            },
            "抽出されたフィールド": final_fields,
            "パターン抽出結果": pattern_fields,
            "抽出統計": {
                "構造化フィールド数": len(final_fields),
                "日付数": len(pattern_fields.get("dates", [])),
                "数字数": len(pattern_fields.get("numbers", [])),
                "電話番号数": len(pattern_fields.get("phone_numbers", []))
            }
        }


def process_document_ai_json(json_file_path: Path, output_path: Optional[Path] = None) -> Dict:
    """
    Document AIのJSONファイルを処理して構造化フィールドを抽出
    
    Args:
        json_file_path: Document AIのJSONファイルパス
        output_path: 結果の出力先（省略時は自動生成）
        
    Returns:
        Dict: 処理結果
    """
    # JSONファイルを読み込み
    with open(json_file_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    
    # フィールド抽出器を初期化
    extractor = FormFieldExtractor()
    
    # フィールドを抽出
    result = extractor.process_document_json(json_data)
    
    # 結果を保存
    if output_path is None:
        output_path = json_file_path.parent / f"{json_file_path.stem}_structured.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"構造化フィールド抽出完了: {output_path}")
    print(f"抽出されたフィールド数: {len(result.get('extracted_fields', {}))}")
    
    return result


if __name__ == "__main__":
    # テスト実行
    test_json_path = Path(__file__).parent.parent / "documents" / "ocr_results" / "one_file" / "page_001_raw_response.json"
    if test_json_path.exists():
        result = process_document_ai_json(test_json_path)
        print("フィールド抽出テスト完了")
    else:
        print(f"テストファイルが見つかりません: {test_json_path}")