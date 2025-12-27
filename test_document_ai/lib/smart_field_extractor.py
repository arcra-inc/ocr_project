"""
スマートフィールド抽出器

Document AIのOCRレスポンスから、事前定義に依存しない
インテリジェントなフィールド抽出を行います。
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path


class SmartFieldExtractor:
    """スマートフィールド抽出器 - Document AIのレスポンスを解析してフィールドを自動検出"""
    
    def __init__(self):
        """初期化"""
        self.field_patterns = self._initialize_patterns()
        
    def _initialize_patterns(self) -> Dict[str, Dict]:
        """フィールド検出パターンを初期化"""
        return {
            "日付": {
                "patterns": [
                    r'令和\s*\d+\s*年\s*\d+\s*月\s*\d+\s*日',
                    r'平成\s*\d+\s*年\s*\d+\s*月\s*\d+\s*日',
                    r'\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日',
                    r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',
                    r'\d{1,2}[-/]\d{1,2}[-/]\d{4}'
                ],
                "context_clues": ["日付", "年月日", "作成日", "提出日", "申請日"]
            },
            "金額": {
                "patterns": [
                    r'[￥¥]\s*[\d,，]+',
                    r'[\d,，]+\s*円',
                    r'[\d,，]+\s*万円',
                    r'金額\s*[:：]\s*[\d,，]+',
                    r'合計\s*[:：]\s*[\d,，]+'
                ],
                "context_clues": ["金額", "料金", "価格", "合計", "小計", "税込", "税抜", "￥", "¥", "円"]
            },
            "氏名": {
                "patterns": [
                    r'[一-龯]{2,4}\s+[一-龯]{1,3}',  # 漢字の姓名
                    r'[ァ-ヾ]{2,8}',  # カタカナ
                    r'[あ-ん]{2,8}',  # ひらがな
                    r'[A-Za-z]+\s+[A-Za-z]+'  # 英字名
                ],
                "context_clues": ["氏名", "名前", "姓名", "申請者", "担当者", "様", "殿", "氏"]
            },
            "住所": {
                "patterns": [
                    r'[都道府県]{1}[^都道府県]*[市区町村]{1}',
                    r'〒\d{3}-\d{4}',
                    r'\d{3}-\d{4}.*[都道府県市区町村]',
                    r'[一-龯]{2,}[都道府県市区町村丁目番地号]+[\d一-龯]*'
                ],
                "context_clues": ["住所", "所在地", "郵便番号", "〒", "都", "道", "府", "県", "市", "区", "町", "村"]
            },
            "電話番号": {
                "patterns": [
                    r'\d{2,5}[-−]\d{2,4}[-−]\d{2,4}',
                    r'\(\d{2,5}\)\s*\d{2,4}[-−]\d{2,4}',
                    r'\d{10,11}',
                    r'TEL\s*[:：]\s*[\d\-−\(\)]+',
                    r'電話\s*[:：]\s*[\d\-−\(\)]+'
                ],
                "context_clues": ["電話", "TEL", "Tel", "携帯", "連絡先", "番号"]
            },
            "メールアドレス": {
                "patterns": [
                    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                    r'[a-zA-Z0-9._%+-]+＠[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                ],
                "context_clues": ["メール", "email", "E-mail", "@", "＠"]
            },
            "会社名": {
                "patterns": [
                    r'[一-龯]+株式会社',
                    r'株式会社[一-龯]+',
                    r'[一-龯]+有限会社',
                    r'有限会社[一-龯]+',
                    r'[一-龯]+㈱',
                    r'㈱[一-龯]+',
                    r'[一-龯]+法人'
                ],
                "context_clues": ["会社", "法人", "団体", "組織", "株式会社", "㈱", "㈲", "合同会社"]
            }
        }
    
    def extract_smart_fields(self, document_ai_response: Dict) -> Dict[str, Any]:
        """
        Document AIレスポンスからスマートフィールド抽出を実行
        
        Args:
            document_ai_response: Document AIのJSONレスポンス
            
        Returns:
            Dict: 抽出されたフィールド情報
        """
        document = document_ai_response.get("document", {})
        pages = document.get("pages", [])
        
        if not pages:
            return {"error": "No pages found"}
        
        # テキスト情報を取得
        full_text = document.get("text", "")
        
        # トークン情報を解析
        page = pages[0]
        tokens = self._extract_token_info(page, full_text)
        
        # 各フィールドタイプを抽出
        extracted_fields = {}
        
        for field_name, field_config in self.field_patterns.items():
            field_results = self._extract_field_by_patterns(
                field_name, field_config, tokens, full_text
            )
            if field_results:
                extracted_fields[field_name] = field_results
        
        # 結果をまとめる
        result = {
            "文書情報": {
                "処理日時": datetime.now().isoformat(),
                "ページ数": len(pages),
                "全文字数": len(full_text),
                "トークン数": len(tokens)
            },
            "抽出されたフィールド": extracted_fields,
            "統計情報": {
                "検出フィールド数": len(extracted_fields),
                "フィールドタイプ": list(extracted_fields.keys())
            }
        }
        
        return result
    
    def _extract_token_info(self, page: Dict, full_text: str) -> List[Dict]:
        """トークン情報を抽出してリスト化"""
        tokens = []
        
        for idx, token in enumerate(page.get("tokens", [])):
            layout = token.get("layout", {})
            text_anchor = layout.get("textAnchor", {})
            segments = text_anchor.get("textSegments", [])
            
            if segments:
                segment = segments[0]
                start_idx = int(segment.get("startIndex", 0))
                end_idx = int(segment.get("endIndex", start_idx))
                text = full_text[start_idx:end_idx]
                
                # 座標情報
                bounding_poly = layout.get("boundingPoly", {})
                normalized_coords = self._get_normalized_coordinates(bounding_poly)
                
                tokens.append({
                    "index": idx,
                    "text": text,
                    "confidence": layout.get("confidence", 0.0),
                    "start_pos": start_idx,
                    "end_pos": end_idx,
                    "coordinates": normalized_coords
                })
        
        return tokens
    
    def _get_normalized_coordinates(self, bounding_poly: Dict) -> Dict:
        """座標情報を正規化"""
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
    
    def _extract_field_by_patterns(self, field_name: str, field_config: Dict, 
                                 tokens: List[Dict], full_text: str) -> Optional[Dict]:
        """パターンとコンテキストクルーを使ってフィールドを抽出"""
        patterns = field_config["patterns"]
        context_clues = field_config["context_clues"]
        
        found_values = []
        
        # パターンマッチングでの抽出
        for pattern in patterns:
            matches = re.finditer(pattern, full_text, re.IGNORECASE)
            for match in matches:
                # マッチしたテキストの座標を取得
                match_coords = self._find_coordinates_for_text_span(
                    tokens, match.start(), match.end()
                )
                
                found_values.append({
                    "値": match.group().strip(),
                    "信頼度": self._calculate_pattern_confidence(match.group(), pattern),
                    "抽出方法": "パターンマッチング",
                    "座標": match_coords,
                    "パターン": pattern
                })
        
        # コンテキストクルーでの抽出
        for clue in context_clues:
            clue_matches = self._find_context_based_values(tokens, clue, field_name)
            found_values.extend(clue_matches)
        
        # 重複除去と信頼度順ソート
        unique_values = self._deduplicate_values(found_values)
        unique_values.sort(key=lambda x: x["信頼度"], reverse=True)
        
        if unique_values:
            return {
                "検出数": len(unique_values),
                "最高信頼度": unique_values[0] if unique_values else None,
                "全候補": unique_values[:5],  # 上位5件
                "フィールドタイプ": field_name
            }
        
        return None
    
    def _find_coordinates_for_text_span(self, tokens: List[Dict], start: int, end: int) -> Dict:
        """テキストスパンに対応する座標を検索"""
        matching_tokens = []
        
        for token in tokens:
            # トークンがテキストスパン内にあるかチェック
            if (token["start_pos"] >= start and token["end_pos"] <= end) or \
               (token["start_pos"] <= start and token["end_pos"] >= end) or \
               (start <= token["start_pos"] <= end) or \
               (start <= token["end_pos"] <= end):
                matching_tokens.append(token)
        
        if not matching_tokens:
            return {}
        
        # 全トークンの座標を統合
        all_coords = [t["coordinates"] for t in matching_tokens if t["coordinates"]]
        if not all_coords:
            return {}
        
        x_mins = [c["x_min"] for c in all_coords]
        y_mins = [c["y_min"] for c in all_coords]
        x_maxs = [c["x_max"] for c in all_coords]
        y_maxs = [c["y_max"] for c in all_coords]
        
        return {
            "x_min": min(x_mins),
            "y_min": min(y_mins),
            "x_max": max(x_maxs),
            "y_max": max(y_maxs),
            "center_x": (min(x_mins) + max(x_maxs)) / 2,
            "center_y": (min(y_mins) + max(y_maxs)) / 2
        }
    
    def _find_context_based_values(self, tokens: List[Dict], clue: str, field_type: str) -> List[Dict]:
        """コンテキストクルーを使って値を検索"""
        results = []
        
        for i, token in enumerate(tokens):
            if clue in token["text"]:
                # クルー周辺のトークンを検索
                search_range = 5
                start_idx = max(0, i - search_range)
                end_idx = min(len(tokens), i + search_range + 1)
                
                for j in range(start_idx, end_idx):
                    if j != i:  # クルートークン自体は除外
                        candidate = tokens[j]
                        if self._is_valid_field_value(candidate["text"], field_type):
                            results.append({
                                "値": candidate["text"].strip(),
                                "信頼度": candidate["confidence"] * 0.8,  # コンテキスト抽出は少し信頼度を下げる
                                "抽出方法": f"コンテキスト({clue})",
                                "座標": candidate["coordinates"],
                                "コンテキストクルー": clue
                            })
        
        return results
    
    def _is_valid_field_value(self, text: str, field_type: str) -> bool:
        """フィールドタイプに基づいて値が妥当かを判定"""
        text = text.strip()
        if len(text) < 1:
            return False
        
        if field_type == "氏名":
            return bool(re.search(r'[一-龯ひ-ゞァ-ヾa-zA-Z]{2,}', text))
        elif field_type == "金額":
            return bool(re.search(r'[\d,，]+', text))
        elif field_type == "住所":
            return len(text) >= 3 and bool(re.search(r'[一-龯]', text))
        elif field_type == "電話番号":
            return bool(re.search(r'[\d\-−\(\)]{8,}', text))
        elif field_type == "日付":
            return bool(re.search(r'[\d年月日令和平成]', text))
        elif field_type == "メールアドレス":
            return '@' in text or '＠' in text
        elif field_type == "会社名":
            return len(text) >= 2
        
        return True
    
    def _calculate_pattern_confidence(self, text: str, pattern: str) -> float:
        """パターンマッチの信頼度を計算"""
        base_confidence = 0.9
        
        # テキストの長さに基づく調整
        if len(text) >= 10:
            base_confidence += 0.05
        elif len(text) <= 2:
            base_confidence -= 0.2
        
        # パターンの複雑さに基づく調整
        if r'\d{' in pattern:  # 具体的な桁数指定
            base_confidence += 0.05
        if '[' in pattern:  # 文字クラス使用
            base_confidence += 0.03
        
        return min(1.0, max(0.1, base_confidence))
    
    def _deduplicate_values(self, values: List[Dict]) -> List[Dict]:
        """重複する値を除去"""
        seen_values = set()
        unique_values = []
        
        for value in values:
            value_text = value["値"]
            if value_text not in seen_values:
                seen_values.add(value_text)
                unique_values.append(value)
        
        return unique_values


def process_with_smart_extractor(json_file_path: Path, output_path: Optional[Path] = None) -> Dict:
    """スマートフィールド抽出器を使用してDocument AIレスポンスを処理"""
    
    # JSONファイルを読み込み
    with open(json_file_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    
    # スマート抽出器を初期化して実行
    extractor = SmartFieldExtractor()
    result = extractor.extract_smart_fields(json_data)
    
    # 結果を保存
    if output_path is None:
        output_path = json_file_path.parent / f"{json_file_path.stem}_smart_fields.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"スマートフィールド抽出完了: {output_path}")
    
    # 統計を表示
    extracted_fields = result.get("抽出されたフィールド", {})
    for field_name, field_data in extracted_fields.items():
        print(f"  {field_name}: {field_data['検出数']}個検出")
    
    return result


if __name__ == "__main__":
    # テスト実行
    test_json_path = Path(__file__).parent.parent / "documents" / "ocr_results" / "one_file" / "page_001_raw_response.json"
    if test_json_path.exists():
        result = process_with_smart_extractor(test_json_path)
        print("\nスマートフィールド抽出テスト完了")
    else:
        print(f"テストファイルが見つかりません: {test_json_path}")