from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Protocol, List, Dict, Optional, Tuple
from abc import ABC, abstractmethod


# ----------------------------
# データ構造定義
# ----------------------------
@dataclass
class Field:
    """
    解析対象のフィールド定義
    
    Attributes:
        key: フィールド名（例: "氏名", "件名"）
        patterns: キーを認識するための正規表現パターンのリスト
        required: 必須フィールドかどうか
        multiline: 複数行にわたる値を許容するか
    """
    key: str
    patterns: List[str]
    required: bool = True
    multiline: bool = False


@dataclass
class ParseResult:
    """
    解析結果
    
    Attributes:
        data: 抽出されたフィールドと値の辞書
        missing_fields: 必須だが見つからなかったフィールドのリスト
        warnings: 解析中の警告メッセージ
    """
    data: Dict[str, str]
    missing_fields: List[str]
    warnings: List[str]


# ----------------------------
# 解析戦略インターフェース
# ----------------------------
@dataclass
class ParsingStrategy(Protocol):
    """解析戦略のプロトコル"""
    
    def parse(self, text: str, fields: List[Field]) -> ParseResult:
        """
        テキストを解析してフィールドを抽出
        
        Args:
            text: OCRで認識されたテキスト
            fields: 抽出するフィールドの定義リスト
            
        Returns:
            ParseResult: 解析結果
        """
        ...


# ----------------------------
# デフォルト実装：順次キー解析
# ----------------------------
class SequentialKeyParser:
    """
    キーを順次検索して値を抽出する解析戦略
    
    動作:
    1. テキストを前から走査
    2. フィールドのパターンに合致したら、次のキーまでをブロックとして取得
    3. 全てのキーを消費するまで繰り返す
    """
    
    def __init__(self, max_value_lines: int = 10):
        """
        Args:
            max_value_lines: 単一フィールドの最大行数
        """
        self.max_value_lines = max_value_lines
    
    def parse(self, text: str, fields: List[Field]) -> ParseResult:
        """
        テキストを解析してフィールドを抽出
        
        Args:
            text: OCRで認識されたテキスト
            fields: 抽出するフィールドの定義リスト
            
        Returns:
            ParseResult: 解析結果
        """
        if not text:
            return ParseResult(
                data={},
                missing_fields=[f.key for f in fields if f.required],
                warnings=["入力テキストが空です"]
            )
        
        data: Dict[str, str] = {}
        warnings: List[str] = []
        
        # テキストを行に分割
        lines = text.split('\n')
        
        # 各フィールドを検索
        for field in fields:
            value, warning = self._extract_field_value(lines, field, fields)
            
            if value:
                data[field.key] = value
            elif field.required:
                warnings.append(f"必須フィールド '{field.key}' が見つかりませんでした")
            
            if warning:
                warnings.append(warning)
        
        # 見つからなかった必須フィールドを特定
        missing_fields = [f.key for f in fields if f.required and f.key not in data]
        
        return ParseResult(
            data=data,
            missing_fields=missing_fields,
            warnings=warnings
        )
    
    def _extract_field_value(
        self, 
        lines: List[str], 
        field: Field, 
        all_fields: List[Field]
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        特定のフィールドの値を抽出
        
        Args:
            lines: テキストの行リスト
            field: 抽出対象のフィールド
            all_fields: 全フィールド定義（次のキーを判定するため）
            
        Returns:
            (値, 警告メッセージ) のタプル
        """
        # 全てのパターンを試す
        for pattern in field.patterns:
            for i, line in enumerate(lines):
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    # キーの後ろに値がある場合（同じ行）
                    remaining = line[match.end():].strip()
                    
                    # 複数行対応
                    if field.multiline or not remaining:
                        value_lines = [remaining] if remaining else []
                        
                        # 次の行から値を収集
                        for j in range(i + 1, min(i + self.max_value_lines + 1, len(lines))):
                            next_line = lines[j].strip()
                            
                            # 空行で終了
                            if not next_line:
                                break
                            
                            # 他のフィールドのキーに到達したら終了
                            if self._is_field_key(next_line, all_fields):
                                break
                            
                            value_lines.append(next_line)
                        
                        value = ' '.join(value_lines).strip()
                        if value:
                            return value, None
                    else:
                        return remaining, None
        
        return None, None
    
    def _is_field_key(self, line: str, fields: List[Field]) -> bool:
        """
        行が他のフィールドのキーかどうかを判定
        
        Args:
            line: チェックする行
            fields: 全フィールド定義
            
        Returns:
            フィールドキーの場合True
        """
        for field in fields:
            for pattern in field.patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    return True
        return False


# ----------------------------
# 拡張実装：キー・バリュー対解析
# ----------------------------
class KeyValuePairParser:
    """
    「キー: 値」形式のシンプルなパターンを抽出する戦略
    
    簡単な帳票やメタデータ抽出に適している
    """
    
    def parse(self, text: str, fields: List[Field]) -> ParseResult:
        """
        「キー: 値」パターンを抽出
        
        Args:
            text: OCRで認識されたテキスト
            fields: 抽出するフィールドの定義リスト
            
        Returns:
            ParseResult: 解析結果
        """
        if not text:
            return ParseResult(
                data={},
                missing_fields=[f.key for f in fields if f.required],
                warnings=["入力テキストが空です"]
            )
        
        data: Dict[str, str] = {}
        warnings: List[str] = []
        
        # 「キー: 値」または「キー：値」のパターンを抽出
        matches = re.findall(r'([^:\n]+)[：:]\s*([^\n]+)', text)
        
        for key_text, value in matches:
            key_text = key_text.strip()
            value = value.strip()
            
            # フィールド定義と照合
            for field in fields:
                for pattern in field.patterns:
                    if re.search(pattern, key_text, re.IGNORECASE):
                        data[field.key] = value
                        break
        
        # 見つからなかった必須フィールド
        missing_fields = [f.key for f in fields if f.required and f.key not in data]
        
        if missing_fields:
            warnings.append(f"必須フィールドが見つかりません: {', '.join(missing_fields)}")
        
        return ParseResult(
            data=data,
            missing_fields=missing_fields,
            warnings=warnings
        )


# ----------------------------
# 高レベルAPI：DataParser
# ----------------------------
class DataParser:
    """
    OCRテキストからフィールドを抽出する高レベルAPI
    
    戦略パターンを使用して、異なる文書フォーマットに対応可能
    """
    
    def __init__(
        self, 
        strategy: Optional[ParsingStrategy] = None,
        fields: Optional[List[Field]] = None
    ):
        """
        Args:
            strategy: 使用する解析戦略（デフォルト: SequentialKeyParser）
            fields: フィールド定義リスト（デフォルト: サンプルフィールド）
        """
        self.strategy = strategy or SequentialKeyParser()
        self.fields = fields or self._default_fields()
    
    def parse_fields(self, ocr_text: str) -> Dict[str, str]:
        """
        OCRテキストからフィールドを抽出（後方互換性のため）
        
        Args:
            ocr_text: OCRで認識されたテキスト
            
        Returns:
            抽出されたフィールドと値の辞書
        """
        result = self.parse(ocr_text)
        return result.data
    
    def parse(self, ocr_text: str) -> ParseResult:
        """
        OCRテキストからフィールドを抽出（詳細情報付き）
        
        Args:
            ocr_text: OCRで認識されたテキスト
            
        Returns:
            ParseResult: 解析結果（データ、欠落フィールド、警告を含む）
        """
        if not ocr_text:
            return ParseResult(
                data={},
                missing_fields=[f.key for f in self.fields if f.required],
                warnings=["入力テキストが空です"]
            )
        
        return self.strategy.parse(ocr_text, self.fields)
    
    def set_fields(self, fields: List[Field]) -> None:
        """
        フィールド定義を設定
        
        Args:
            fields: 新しいフィールド定義リスト
        """
        self.fields = fields
    
    def set_strategy(self, strategy: ParsingStrategy) -> None:
        """
        解析戦略を変更
        
        Args:
            strategy: 新しい解析戦略
        """
        self.strategy = strategy
    
    @staticmethod
    def _default_fields() -> List[Field]:
        """
        デフォルトのフィールド定義（日本の一般的な帳票を想定）
        
        Returns:
            デフォルトフィールドのリスト
        """
        return [
            Field(
                key="氏名",
                patterns=[r"氏名[：:\s]*", r"名前[：:\s]*", r"お名前[：:\s]*"],
                required=False
            ),
            Field(
                key="件名",
                patterns=[r"件名[：:\s]*", r"タイトル[：:\s]*", r"表題[：:\s]*"],
                required=False
            ),
            Field(
                key="日付",
                patterns=[r"日付[：:\s]*", r"作成日[：:\s]*", r"\d{4}[年/.-]\d{1,2}[月/.-]\d{1,2}"],
                required=False
            ),
            Field(
                key="金額",
                patterns=[r"金額[：:\s]*", r"合計[：:\s]*", r"¥\s*[\d,]+", r"[0-9,]+円"],
                required=False
            ),
            Field(
                key="住所",
                patterns=[r"住所[：:\s]*", r"所在地[：:\s]*"],
                required=False,
                multiline=True
            ),
        ]


# ----------------------------
# 使用例・テスト
# ----------------------------
if __name__ == "__main__":
    # サンプルOCRテキスト
    sample_text = """
    請求書
    
    氏名: 山田太郎
    件名: 2025年11月分 コンサルティング料
    日付: 2025/12/01
    金額: ¥150,000
    住所: 東京都渋谷区
    神南1-2-3
    """
    
    print("=== SequentialKeyParser のテスト ===")
    parser1 = DataParser(strategy=SequentialKeyParser())
    result1 = parser1.parse(sample_text)
    
    print("抽出データ:")
    for key, value in result1.data.items():
        print(f"  {key}: {value}")
    
    if result1.warnings:
        print("\n警告:")
        for warning in result1.warnings:
            print(f"  - {warning}")
    
    print("\n=== KeyValuePairParser のテスト ===")
    parser2 = DataParser(strategy=KeyValuePairParser())
    result2 = parser2.parse(sample_text)
    
    print("抽出データ:")
    for key, value in result2.data.items():
        print(f"  {key}: {value}")
    
    # カスタムフィールドの例
    print("\n=== カスタムフィールド定義のテスト ===")
    custom_fields = [
        Field(key="会社名", patterns=[r"会社名[：:\s]*", r"法人名[：:\s]*"], required=True),
        Field(key="電話番号", patterns=[r"電話[：:\s]*", r"TEL[：:\s]*", r"\d{2,4}-\d{2,4}-\d{4}"], required=False),
    ]
    
    parser3 = DataParser(fields=custom_fields)
    result3 = parser3.parse("会社名: 株式会社サンプル\n電話: 03-1234-5678")
    
    print("抽出データ:")
    for key, value in result3.data.items():
        print(f"  {key}: {value}")
    
    if result3.missing_fields:
        print("\n欠落フィールド:", result3.missing_fields)

