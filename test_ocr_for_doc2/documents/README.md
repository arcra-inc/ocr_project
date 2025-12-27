# Test OCR for Doc2

Google Cloud Vision APIを活用した高精度帳票OCRシステムの実装です。クラウドベースのAI OCRエンジンを使用して、高品質な文字認識を実現します。

## 考え方・設計指針

このテストは、Google Cloud Vision OCR（`DOCUMENT_TEXT_DETECTION`）を用いて、文書画像から高精度にテキストを抽出できるかを検証します。

設計上の狙いは以下です。

- 低品質なスキャンや複雑なレイアウトでも、精度と頑健性を優先する
- まずはページ単位で「全文テキスト」を確実に取得し、構造化（項目抽出）は必要に応じて後段で行う
- 認証情報の扱いを集中管理し、キーファイルをリポジトリにコミットしない

## 処理フロー

1. **APIクライアント初期化** (`lib/declare_key.py`)
2. **画像バッチ読み込み** (`main.py`)
3. **Google Vision OCR実行** (DOCUMENT_TEXT_DETECTION)
4. **テキストファイル出力** (UTF-8形式)

## モジュール構成

本テストでは、APIキー管理などのモジュールを`lib/`ディレクトリに配置し、メイン実行ファイル(`main.py`)から読み込む構成としています。

```
test_ocr_for_doc2/
├── main.py                 # メイン実行ファイル
├── lib/                    # ライブラリモジュール
│   ├── declare_key.py      # API認証設定
│   └── sample.py           # サンプルスクリプト
└── documents/              # ドキュメント・画像格納
    ├── images/
    │   └── pdf_pages/
    └── ocr_txt/
```

## モジュール詳細

### システム構成図

![](misc/system.svg)

### 処理フロー図

![](misc/process.svg)

### A. APIキー管理モジュール (`lib/declare_key.py`)
- Google Cloud Vision APIの認証情報管理
- サービスアカウントキーファイルの読み込み
- APIクライアントインスタンスの生成

### B. メイン処理モジュール (`main.py`)
- 画像ファイルの自動検出・ソート
- バッチ処理による効率的なOCR実行
- エラーハンドリングと処理結果の統計出力

### C. サンプルコード (`lib/sample.py`)
  - 単体画像処理のサンプル実装
  - API使用方法のリファレンス

## 環境要件

- Python 3.11
- Google Cloud Vision API (`google-cloud-vision`)
- Google Cloud サービスアカウント
- 有効なGoogle Cloud プロジェクト

## セットアップ手順

### 1. Google Cloud プロジェクトの準備
1. [Google Cloud Console](https://console.cloud.google.com/)でプロジェクトを作成
2. Vision APIを有効化
3. 請求先アカウントの設定（API使用料金）

### 2. サービスアカウントの作成
1. IAMと管理 → サービスアカウントを選択
2. 新しいサービスアカウントを作成
3. 役割: `Cloud Vision API User` を付与
4. キーを作成してJSONファイルをダウンロード

### 3. APIキーファイルの配置
`declare_key.py`内のパスを実際のキーファイル場所に変更：
```python
def call_for_client():
    client = vision.ImageAnnotatorClient.from_service_account_file(
        r"C:\path\to\your\service-account-key.json"  # ←実際のパス
    )
    return client
```

### 4. パッケージインストール
```bash
# プロジェクトルートで実行
.\ocr_env\Scripts\activate
pip install google-cloud-vision
```

## 使用方法

### 1. PDFファイルの準備と変換

PDFファイルをPNG画像に変換してからOCR処理を行います：

```bash
# プロジェクトルートに移動
cd ..\..

# PDF→PNG変換スクリプト実行
python util\convert_pdf_to_png.py
```

このスクリプトは以下の機能を提供します：
- PDFファイルの各ページをPNG画像に変換
- 高解像度（300 DPI）でのOCR最適化
- 処理対象ディレクトリの自動検出
- エラーハンドリングと詳細な進捗表示

変換された画像ファイルは`documents/images/pdf_pages/`ディレクトリに保存されます。

### 2. 画像の準備
画像を`documents/images/pdf_pages/`フォルダに配置：
```
documents/
├── images/
│   └── pdf_pages/
│       ├── page_001.png
│       ├── page_002.png
│       └── ...
└── ocr_txt/  # 出力先（自動作成）
```

### 3. バッチOCR実行
```bash
cd test_ocr_for_doc2
python main.py
```

### 4. ディレクトリパスの設定
必要に応じて`main.py`内のパスを変更：
```python
images_dir = Path(r"C:\path\to\your\images")
output_txt_dir = Path(r"C:\path\to\output\directory")
```

## 処理結果

### 実行ログ例
```
[OK] page_001.png -> page_001.txt (1234 chars)
[OK] page_002.png -> page_002.txt (987 chars)
[NG] page_003.png -> API quota exceeded
Done. OK=2, NG=1, total=3
```

### 出力ファイル構成
```
documents/
└── ocr_txt/
    ├── page_001.txt
    ├── page_002.txt
    └── page_003.txt
```

### テキスト出力例（page_001.txt）
```
請求書

株式会社サンプル
〒123-4567 東京都渋谷区サンプル1-2-3
TEL: 03-1234-5678

請求先：
株式会社〇〇〇様

請求日：2024年12月20日
支払期限：2025年1月20日

商品名          数量    単価      金額
サービスA        10    5,000   50,000
サービスB         5   10,000   50,000
                          -------
                  合計  100,000円
```

