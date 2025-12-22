
次やること
- [x] ライブラリのインストール
- [x] macで開発したコードを移植して，動くかどうかを確認すること
  - [x] tesseract (test for1) confirmation
- [X] ~~*test for 2 construction*~~ [2025-12-16]
  - [X] ~~*まず環境構築する．*~~ [2025-12-16]
  - [ ] 構成の整理
  - [ ] 

---

# Ref.
- Requirements
  - https://www.notion.so/251011_-2893cbda9cbd804082c8e1ef68881c81

- Tesseract
  - https://qiita.com/takeru-hirai/items/4fbe6593d42f9a844b1c#%E6%89%8B%E9%A0%862git%E3%81%AE%E3%82%A4%E3%83%B3%E3%82%B9%E3%83%88%E3%83%BC%E3%83%AB
  - https://qiita.com/t_koba/items/2e8f9eafbdd7644cff20
  - [画像から文字を瞬時に読み取る！Tesseractとpytesseractの驚異の力【Python】 #Python3 - Qiita](https://qiita.com/ryome/items/16fc42854fe93de78a23)
    - 環境変数
      ```
      import sys
      import pytesseract
      from PIL import Image
      # ★ ここを追加 ★
      pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
      ```

--- 
- Google Vision OCR
  - https://nikkie-ftnext.hatenablog.com/entry/ocr-with-google-vision-api-python-first-step
  - 

- めも
  - キーを作成
  - キーのパスを powerShellで環境変数として設定
  - ``pip install --upgrade google-cloud-vision``
  - 