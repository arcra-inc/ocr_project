import os
import json
import re
from pathlib import Path
from typing import List
from lib.image_loader import ImageLoader
from lib.preprocess import Preprocessor
from lib.ocr_recognizer import OCRRecognizer
from lib.data_parser import DataParser
from lib.output_writer import OutputWriter


def natural_key(path: Path):
    """
    page_001.png, page_002.png ... のようなファイルを自然順で並べるためのキー
    """
    return [int(s) if s.isdigit() else s.lower() for s in re.split(r"(\d+)", path.name)]


def process_single_image(image_path: Path, output_dir: Path, use_preprocessing: bool = True):
    """
    単一画像のOCR処理
    
    Args:
        image_path: 画像ファイルのパス
        output_dir: 出力ディレクトリ
        use_preprocessing: 前処理（射影変換）を使用するかどうか
    """
    try:
        # 0. 画像の読み込み
        image_loader = ImageLoader()
        original_image = image_loader.load_image(str(image_path))
        print(f"画像を読み込みました: {image_path.name}")

        # 1. OpenCVによる前処理（傾き補正・射影変換）
        if use_preprocessing:
            preprocessor = Preprocessor()
            preprocess_result = preprocessor.process_one(original_image)
            
            # 前処理の結果を確認：射影変換が失敗した場合は元画像を使用
            if preprocess_result.matrix is None:
                print("射影変換が適用されませんでした。元画像を使用します。")
                corrected_image = original_image
            else:
                print("射影変換を適用しました。")
                corrected_image = preprocess_result.transformed
            
            print("前処理（傾き補正・射影変換）を完了しました。")
        else:
            print("前処理をスキップし、元画像を直接使用します。")
            corrected_image = original_image
        
        # 2. TesseractによるOCR文字認識
        ocr_recognizer = OCRRecognizer()
        ocr_text = ocr_recognizer.recognize_text(corrected_image)
        print("OCR文字認識を完了しました。")
        print("OCR認識結果の一部:")
        print(ocr_text[:200] + "..." if len(ocr_text) > 200 else ocr_text)
        
        # 3. 正規表現でフィールド分割
        data_parser = DataParser()
        extracted_data = data_parser.parse_fields(ocr_text)
        print("正規表現によるフィールド分割を完了しました。")
        print("フィールド分割結果の一部:")
        print(json.dumps(extracted_data, ensure_ascii=False, indent=2)[:200] + "..." if len(json.dumps(extracted_data, ensure_ascii=False, indent=2)) > 200 else json.dumps(extracted_data, ensure_ascii=False, indent=2))
        
        # 4. 出力ファイル生成
        output_writer = OutputWriter()
        base_filename = image_path.stem
        
        # 4-1. OCR認識テキストをtxtファイルに保存
        txt_filename = base_filename + "_ocr_text.txt"
        txt_filepath = output_dir / txt_filename
        with open(txt_filepath, 'w', encoding='utf-8') as f:
            f.write(ocr_text)
        print(f"OCRテキストファイルを生成しました: {txt_filepath}")
        
        # 4-2. 構造化データをJSONファイルに保存
        json_filename = base_filename + "_structured_data.json"
        output_writer.write_json(extracted_data, json_filename, str(output_dir))
        print(f"構造化JSONファイルを生成しました: {output_dir / json_filename}")
        
        return True
        
    except FileNotFoundError as e:
        print(f"エラー: {e}")
        return False
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
        return False


def main(images_dir: Path, output_dir: Path, exts: set = None, use_preprocessing: bool = True):
    """
    複数画像のOCR処理を実行
    
    Args:
        images_dir: 画像ファイルが格納されているディレクトリ
        output_dir: OCR結果を保存するディレクトリ
        exts: 対象とする画像の拡張子セット（デフォルト: {".png", ".jpg", ".jpeg", ".tif", ".tiff"}）
        use_preprocessing: 前処理（射影変換）を使用するかどうか
    """
    if exts is None:
        exts = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    
    if not images_dir.exists():
        raise FileNotFoundError(f"images_dir not found: {images_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    image_paths: List[Path] = sorted(
        [p for p in images_dir.iterdir() if p.is_file() and p.suffix.lower() in exts],
        key=natural_key,
    )

    if not image_paths:
        print(f"No images found in: {images_dir}")
        return

    ok = 0
    ng = 0

    for img_path in image_paths:
        print(f"\n処理中: {img_path.name}")
        success = process_single_image(img_path, output_dir, use_preprocessing)
        
        if success:
            print(f"[OK] {img_path.name} -> 処理完了")
            ok += 1
        else:
            print(f"[NG] {img_path.name} -> 処理失敗")
            ng += 1

    print(f"\n処理完了. 成功={ok}, 失敗={ng}, 合計={len(image_paths)}")


if __name__ == "__main__":
    # 現在のファイルを基準とした相対パスを使用
    current_dir = Path(__file__).parent
    images_dir = current_dir / "documents" / "images" / "sample"
    output_dir = current_dir / "documents" / "output_txt"
    
    # 対象とする拡張子
    # このスクリプトは指定したディレクトリ以下にある指定拡張子のファイルをすべて処理します
    exts = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    
    # ===== OCR処理設定 =====
    use_preprocessing = False  # 前処理（射影変換）を使用するかどうか（False=元画像を直接使用）
    # ===== 設定ここまで =====
    
    print(f"画像ディレクトリ: {images_dir}")
    print(f"出力ディレクトリ: {output_dir}")
    print(f"前処理使用: {use_preprocessing}")
    print(f"画像ディレクトリ存在確認: {images_dir.exists()}")
    
    main(images_dir, output_dir, exts, use_preprocessing)