import pytesseract
import cv2

# Windows環境でTesseractのパスを指定してください
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\NakanoShiryu\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"


class OCRRecognizer:
    def __init__(self):
        """
        Tesseractの実行パスを設定します。
        環境に合わせて、コメントアウトを解除しパスを修正してください。
        """
        # Tesseractの実行パスを設定（環境に応じて変更してください）
        # pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
        pass

    def recognize_text(self, image):
        """
        Tesseractを使用して画像からテキストを認識します。

        Args:
            image (numpy.ndarray): OpenCVで読み込まれた画像。

        Returns:
            str: 認識されたテキスト。
        """
        if image is None:
            raise ValueError("入力画像がNoneです。")

        try:
            # まず日本語で試す
            text = pytesseract.image_to_string(image, lang='jpn')
            return text
        except pytesseract.TesseractError as e:
            # 日本語が利用できない場合は英語で実行
            print(f"日本語言語データエラー: {e}")
            print("英語で処理を続行します。")
            text = pytesseract.image_to_string(image, lang='eng')
            return text
        except Exception as e:
            # その他のエラーも英語で再試行
            print(f"OCR処理中にエラー: {e}")
            print("英語で処理を続行します。")
            text = pytesseract.image_to_string(image, lang='eng')
            return text


def test_tesseract_installation():
    """
    Tesseractのインストール状態を確認します。
    
    Returns:
        bool: 全ての確認項目をパスした場合True、問題がある場合False
    """
    import sys
    import subprocess
    import shutil
    
    print("=" * 60)
    print("Tesseract OCR 環境確認")
    print("=" * 60)
    
    all_ok = True
    
    # 1. pytesseractパッケージのインポート確認
    print("\n[1] pytesseractパッケージの確認...")
    try:
        import pytesseract
        print("✓ pytesseractパッケージがインストールされています")
        print(f"  バージョン: {pytesseract.__version__ if hasattr(pytesseract, '__version__') else '不明'}")
    except ImportError as e:
        print(f"✗ pytesseractパッケージがインストールされていません: {e}")
        print("  インストールコマンド: pip install pytesseract")
        all_ok = False
        return all_ok
    
    # 2. Tesseract実行ファイルの確認
    print("\n[2] Tesseract実行ファイルの確認...")
    tesseract_path = shutil.which('tesseract')
    if tesseract_path:
        print(f"✓ Tesseract実行ファイルが見つかりました")
        print(f"  パス: {tesseract_path}")
    else:
        print("✗ Tesseract実行ファイルが見つかりません")
        print("  macOSの場合: brew install tesseract")
        print("  Linuxの場合: sudo apt-get install tesseract-ocr")
        print("  Windowsの場合: https://github.com/UB-Mannheim/tesseract/wiki からインストール")
        all_ok = False
        return all_ok
    
    # 3. Tesseractのバージョン確認
    print("\n[3] Tesseractバージョンの確認...")
    try:
        version_output = subprocess.check_output(['tesseract', '--version'], 
                                                stderr=subprocess.STDOUT, 
                                                text=True)
        version_line = version_output.split('\n')[0]
        print(f"✓ {version_line}")
    except Exception as e:
        print(f"✗ バージョン取得エラー: {e}")
        all_ok = False
    
    # 4. Tesseract API呼び出しテスト
    print("\n[4] Tesseract API呼び出しテスト...")
    try:
        import numpy as np
        # 簡単なテスト画像を作成（白い背景に黒い文字"TEST"をシミュレート）
        test_image = np.ones((100, 200, 3), dtype=np.uint8) * 255
        result = pytesseract.image_to_string(test_image)
        print("✓ Tesseract APIの呼び出しに成功しました")
    except Exception as e:
        print(f"✗ Tesseract API呼び出しエラー: {e}")
        all_ok = False
    
    # 5. 日本語言語データの確認
    print("\n[5] 日本語言語データの確認...")
    try:
        lang_output = subprocess.check_output(['tesseract', '--list-langs'], 
                                            stderr=subprocess.STDOUT, 
                                            text=True)
        available_langs = lang_output.split('\n')
        if 'jpn' in available_langs:
            print("✓ 日本語(jpn)言語データがインストールされています")
        else:
            print("✗ 日本語(jpn)言語データがインストールされていません")
            print("  macOSの場合: brew install tesseract-lang")
            print(f"  利用可能な言語: {', '.join([l for l in available_langs if l.strip()])}")
            all_ok = False
    except Exception as e:
        print(f"✗ 言語データ確認エラー: {e}")
        all_ok = False
    
    # 6. OpenCV (cv2)の確認
    print("\n[6] OpenCV (cv2)パッケージの確認...")
    try:
        import cv2
        print("✓ OpenCVパッケージがインストールされています")
        print(f"  バージョン: {cv2.__version__}")
    except ImportError as e:
        print(f"✗ OpenCVパッケージがインストールされていません: {e}")
        print("  インストールコマンド: pip install opencv-python")
        all_ok = False
    
    # 結果サマリー
    print("\n" + "=" * 60)
    if all_ok:
        print("✓ 全ての確認項目をパスしました！")
        print("Tesseract OCRを使用する準備ができています。")
    else:
        print("✗ いくつかの問題が見つかりました。")
        print("上記のエラーメッセージを確認して、必要なインストールを行ってください。")
    print("=" * 60)
    
    return all_ok


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # 引数チェック
    if len(sys.argv) > 1 and 'test' in sys.argv[1:]:
        # testモード：環境確認のみ
        test_tesseract_installation()
    else:
        # 通常モード：OCR処理を実行
        print("OCR処理を実行します...")
        from image_loader import ImageLoader
        
        # 現在のファイル位置から相対パスを計算
        current_dir = Path(__file__).parent
        test_imagefile_path = current_dir.parent / "documents" / "images" / "sample" / "sample.png"
        
        print(f"Looking for image at: {test_imagefile_path}")
        print(f"File exists: {test_imagefile_path.exists()}")
        
        loader = ImageLoader()
        img = loader.load_image(str(test_imagefile_path))
        
        # TesseractでOCRを実行
        try:
            text = pytesseract.image_to_string(img, lang='jpn')
            print("日本語でOCR処理を実行しました。")
        except pytesseract.TesseractError as e:
            print(f"日本語言語データエラー: {e}")
            print("英語で処理を続行します。")
            text = pytesseract.image_to_string(img, lang='eng')
        except Exception as e:
            print(f"OCR処理中にエラーが発生: {e}")
            print("英語で処理を続行します。")
            text = pytesseract.image_to_string(img, lang='eng')
        
        print("Recognized Text:")
        print(text)

    '''出力例:
    '''
    