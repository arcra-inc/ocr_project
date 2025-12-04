import pytesseract
import cv2
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

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

        # 画像から日本語テキストを抽出
        text = pytesseract.image_to_string(image, lang='jpn')
        return text


if __name__ == "__main__":
    '''
    # OCRRecognizerのテストコード
    from image_loader import ImageLoader  # ユーザのモジュールを想定

    loader = ImageLoader()
    img = loader.load_image('./temptest/image.png')

    recognizer = OCRRecognizer()
    recognized_text = recognizer.recognize_text(img)
    print("Recognized Text:")
    print(recognized_text)
    '''


    import sys
    import pytesseract
    #from PIL import Image
    
    # 画像を読み込む
    #img = Image.open(image_path)
    from image_loader import ImageLoader
    loader = ImageLoader()
    img = loader.load_image('./temptest/forTesseract.png')
    

    # TesseractでOCRを実行
    text = pytesseract.image_to_string(img, lang='jpn')
    print("Recognized Text:")
    print(text)

    '''出力例:
    (orc_test1) nkn4ryu@nakanoshisatsus-MacBook-Pro test_ocr_for_doc1 % python ocr_recognizer.py
    Recognized Text:
    この記事で紹介するのは、過去に科目合格者100人以上を見てきた経験から、平均を取った方法です。
    アクチュアリーの試験勉強には、人によって流派がいろいろあります。その中で、本当に良いやり方を学ぶのは案外難しいもの。
    このページでは、 過去に100人以上の合格者を見てきた経験をもとにして、情報をまとめています。 
    「ビピッグデータの平均はこういった勉強法になる] という情報として、活用していただければ幸いです。
    '''
    