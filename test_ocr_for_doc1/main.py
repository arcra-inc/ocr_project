import os
import json
from image_loader import ImageLoader
from preprocess import Preprocessor
from ocr_recognizer import OCRRecognizer
from data_parser import DataParser
from output_writer import OutputWriter

def main(image_path):
    """
    OCR処理のメイン関数
    """
    try:
        # 0. 画像の読み込み
        image_loader = ImageLoader()
        original_image = image_loader.load_image(image_path)
        print(f"画像を読み込みました: {image_path}")

        # 1. OpenCVによる傾き補正
        preprocessor = Preprocessor()
        corrected_image = preprocessor.correct_skew(original_image)
        print("傾き補正処理を完了しました。")
        
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
        
        # 4. JSON形式で出力
        output_writer = OutputWriter()
        output_filename = os.path.splitext(os.path.basename(image_path))[0] + ".json"
        output_dir = os.path.dirname(image_path) # 画像と同じディレクトリに出力
        output_writer.write_json(extracted_data, output_filename, output_dir)
        print(f"JSONファイルを生成しました: {os.path.join(output_dir, output_filename)}")
        
    except FileNotFoundError as e:
        print(f"エラー: {e}")
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")

if __name__ == "__main__":
    # ここにテスト用の画像パスを指定します。
    # 例: sample_invoice.png
    # os.path.join() を使用して、相対パスで指定すると便利です。
    
    # サンプル画像がないため、ここではダミーのパスを指定します。
    # 実際の実行時には、documents/images/ の下に画像を配置し、
    # そのパスを指定してください。
    
    # 例:
    # sample_image_path = os.path.join(os.path.dirname(__file__), 'documents', 'images', 'sample_invoice.png')
    # main(sample_image_path)
    
    print("実行には画像ファイルのパスが必要です。`main()`関数の呼び出し部分を修正してください。")
