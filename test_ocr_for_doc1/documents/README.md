# Test OCR for Doc1 - オープンソースOCRシステム

TesseractとOpenCVを使用した帳票OCRシステムの実装です。AIを使わず、オープンソース技術のみで帳票画像からテキスト抽出とフィールド分割を行います。

## 概要

本システムは以下の4つのステップで帳票処理を行います：

1. **画像読み込み** (`image_loader.py`)
2. **前処理・傾き補正** (`preprocess.py`) 
3. **OCR文字認識** (`ocr_recognizer.py`)
4. **フィールド分割・JSON出力** (`data_parser.py`, `output_writer.py`)

## モジュール構成

### システム構成図

![](system.svg)

### 処理フロー図
![](process.svg)


### モジュール詳細

### A. 画像読み込みモジュール (`image_loader.py`)
- 帳票画像ファイルの読み込み
- 対応フォーマット: PNG, JPG, TIFF等

### B. 前処理モジュール (`preprocess.py`)
- OpenCVを使用した画像前処理
- 傾き補正（スキュー補正）
- ノイズ除去・コントラスト調整
- 輪郭検出による文書領域抽出

### C. OCR認識モジュール (`ocr_recognizer.py`) 
- Tesseractエンジンによる日本語OCR
- 文字認識精度の最適化
- 縦書き・横書き混在対応

### D. データ解析モジュール (`data_parser.py`)
- 正規表現によるフィールド抽出
- 帳票項目の自動分類
- 金額・日付・住所等の構造化

### E. 出力モジュール (`output_writer.py`)
- JSON形式での結果出力
- 抽出データの構造化
- エラーハンドリング

## 環境要件

- Python 3.11
- OpenCV (`opencv-python`)
- Tesseract OCR 
- pytesseract
- NumPy
- Pillow

## セットアップ手順

### 1. 仮想環境の準備
```bash
# プロジェクトルートで実行
.\ocr_env\Scripts\activate
```

### 2. Tesseractのインストール
1. [Tesseract-OCR for Windows](https://github.com/UB-Mannheim/tesseract/wiki)をダウンロード
2. インストール時に「Japanese (jpn)」言語パックを選択
3. インストールパス（通常 `C:\Program Files\Tesseract-OCR\`）を確認

### 3. パス設定の確認
`ocr_recognizer.py`内のTesseractパスが正しく設定されていることを確認：
```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

## 実行方法

### 1. 画像の準備
- 帳票画像を`documents/images/`フォルダに配置
- 推奨フォーマット: PNG（300DPI以上）

### 2. メイン処理の実行
```bash
cd test_ocr_for_doc1
python main.py
```

### 3. 実行時の設定
`main.py`の最下部で画像パスを指定：
```python
sample_image_path = os.path.join(os.path.dirname(__file__), 'documents', 'images', 'sample_invoice.png')
main(sample_image_path)
```

## 出力結果

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

## トラブルシューティング

### Tesseractエラー
- `TesseractNotFoundError`: Tesseractのインストールパスを確認
- 日本語認識不良: 言語パック（jpn）のインストールを確認

### OpenCVエラー  
- 画像読み込み失敗: ファイルパスと画像形式を確認
- メモリエラー: 画像サイズを縮小

### 認識精度改善のヒント
- 画像解像度を300DPI以上に設定
- コントラストの調整
- ノイズ除去処理の追加
- 傾き補正パラメータの調整

## カスタマイズ

- **正規表現パターン**: `data_parser.py`でフィールド抽出ルールを調整
- **前処理パラメータ**: `preprocess.py`で画像処理パラメータを調整  
- **OCR設定**: `ocr_recognizer.py`でTesseractのオプションを調整

## 制限事項

- 帳票レイアウトが大きく異なる場合は正規表現パターンの調整が必要
- 手書き文字の認識精度は限定的
- 複雑な表構造の解析は追加実装が必要