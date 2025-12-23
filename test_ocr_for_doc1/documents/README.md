# Test OCR for Doc1

TesseractとOpenCVを使用した帳票OCRシステムの実装です。AIを使わず、オープンソース技術のみで帳票画像からテキスト抽出とフィールド分割を行います。

## 設計指針

このテストは、クラウドや有料サービスに依存しないローカル完結のOCRパイプラインを検証し、帳票から抽出した情報をJSONとして出力することを目的とします。

設計上の狙いは以下です。

- 処理を説明可能にしてデバッグしやすくする（前処理後の画像、OCRの生テキスト、正規表現抽出結果などを追える）
- end2endの機械学習ではなく、単純で決定論的なルール（画像処理 + 正規表現）を優先する
  - **機械学習技術は用いています**
- 所与の帳票レイアウトに対して、前処理設定や正規表現パターンを手動で与える

以下の流れで上から順番に処理します．

1. **画像読み込み** (`lib/image_loader.py`)
2. **前処理・傾き補正** (`lib/preprocess.py`) 
3. **OCR文字認識** (`lib/ocr_recognizer.py`)
4. **フィールド分割・JSON出力** (`lib/data_parser.py`, `lib/output_writer.py`)

## モジュール構成

本テストでは、モジュールを`lib/`ディレクトリに配置し、メイン実行ファイル(`main.py`)から読み込む構成としています。

```
test_ocr_for_doc1/
├── main.py                 # メイン実行ファイル
├── lib/                    # ライブラリモジュール
│   ├── image_loader.py     # 画像読み込み
│   ├── preprocess.py       # 前処理
│   ├── ocr_recognizer.py   # OCR認識
│   ├── data_parser.py      # データ解析
│   ├── output_writer.py    # 出力
│   └── prepro_test.py      # 前処理テスト
└── documents/              # ドキュメント・画像格納
```

## モジュール概要
**システム構成図**

![](misc/system.svg)

**処理フロー図**
![](misc/process.svg)


**各モジュールごとの役割**

- A. 画像読み込みモジュール (`lib/image_loader.py`)
  - 帳票画像ファイルの読み込み
  - 対応フォーマット: PNG, JPG, TIFF等

- B. 前処理モジュール (`lib/preprocess.py`)
  - OpenCVを使用した画像前処理
  - 傾き補正（スキュー補正）
  - ノイズ除去・コントラスト調整
  - 輪郭検出による文書領域抽出

- C. OCR認識モジュール (`lib/ocr_recognizer.py`) 
  - Tesseractエンジンによる日本語OCR
  - 文字認識精度の最適化
  - 縦書き・横書き混在対応

- D. データ解析モジュール (`lib/data_parser.py`)
  - 正規表現によるフィールド抽出
  - 帳票項目の自動分類
  - 金額・日付・住所等の構造化

- E. 出力モジュール (`lib/output_writer.py`)
  - JSON形式での結果出力
  - 抽出データの構造化
  - エラーハンドリング

## 依存関係

- Python 3.11
- OpenCV (`opencv-python`)
- Tesseract OCR 
- pytesseract
- NumPy

## セットアップ
[README.md](../../README.md)のセットアップが完了している前提です．

**仮想環境の準備**
```bash
# プロジェクトルートで実行
.\ocr_env\Scripts\activate
```

**パス設定の確認**
`lib/ocr_recognizer.py`内のTesseractパスが正しく設定されていることを確認：
```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

**テスト実行**
Tesseract OCRの環境が正しくセットアップされているか確認するため、環境テストを実行します。
```bash
cd test_ocr_for_doc1
python lib/ocr_recognizer.py test
```
このコマンドは以下の項目を確認します：
1. pytesseractパッケージのインストール確認
2. Tesseract実行ファイルの存在確認
3. Tesseractバージョンの確認
4. Tesseract APIの呼び出しテスト
5. 日本語言語データ(jpn)のインストール確認
6. OpenCV (cv2)パッケージのインストール確認

※ 正常な出力例
```
============================================================
Tesseract OCR 環境確認
============================================================

[1] pytesseractパッケージの確認...
✓ pytesseractパッケージがインストールされています

[2] Tesseract実行ファイルの確認...
✓ Tesseract実行ファイルが見つかりました
  パス: /opt/homebrew/bin/tesseract

[3] Tesseractバージョンの確認...
✓ tesseract 5.3.3

[4] Tesseract API呼び出しテスト...
✓ Tesseract APIの呼び出しに成功しました

[5] 日本語言語データの確認...
✓ 日本語(jpn)言語データがインストールされています

[6] OpenCV (cv2)パッケージの確認...
✓ OpenCVパッケージがインストールされています
  バージョン: 4.8.1

============================================================
✓ 全ての確認項目をパスしました！
Tesseract OCRを使用する準備ができています。
============================================================
```


## 実行

### 1. 画像の準備
- 帳票画像を`documents/images/`フォルダに配置
- 推奨フォーマット: PNG（300DPI以上）

### 2. メイン処理の実行
**実行時の設定**
`main.py`の最下部で画像パスを指定：
```python
sample_image_path = os.path.join(os.path.dirname(__file__), 'documents', 'images', 'sample_invoice.png')
main(sample_image_path)
```
実行
```bash
cd test_ocr_for_doc1
python main.py
```


## 出力

### 処理ログ例
```
画像を読み込みました: documents/images/sample_invoice.png
傾き補正処理を完了しました。
OCR文字認識を完了しました。
OCR認識結果の一部:
請求書
株式会社〇〇〇
請求日：2024年12月20日...

正規表現によるフィールド分割を完了しました。
フィールド分割結果の一部:
{
  "document_type": "請求書",
  "company_name": "株式会社〇〇〇",
  "date": "2024年12月20日",
  ...
}

JSONファイルを生成しました: documents/images/sample_invoice.json
```

### JSON出力例
```json
{
  "document_type": "請求書",
  "company_name": "株式会社〇〇〇", 
  "invoice_date": "2024年12月20日",
  "amount": "100,000",
  "items": [
    {
      "description": "商品A",
      "quantity": "10",
      "unit_price": "5,000"
    }
  ],
  "extracted_raw_text": "請求書\n株式会社〇〇〇\n..."
}
```






## 制限事項

- 帳票レイアウトが大きく異なる場合は正規表現パターンの調整が必要
- 手書き文字の認識精度は限定的
- 複雑な表構造の解析は追加実装が必要