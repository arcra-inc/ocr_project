# Test OCR for Doc2

Google Cloud Vision APIを活用した高精度帳票OCRシステムの実装です。クラウドベースのAI OCRエンジンを使用して、高品質な文字認識を実現します。

## 考え方・設計指針

このテストは、Google Cloud Vision OCR（`DOCUMENT_TEXT_DETECTION`）を用いて、文書画像から高精度にテキストを抽出できるかを検証します。

設計上の狙いは以下です。

- 低品質なスキャンや複雑なレイアウトでも、精度と頑健性を優先する
- まずはページ単位で「全文テキスト」を確実に取得し、構造化（項目抽出）は必要に応じて後段で行う
- 認証情報の扱いを集中管理し、キーファイルをリポジトリにコミットしない

## 処理フロー

1. **APIクライアント初期化** (`declare_key.py`)
2. **画像バッチ読み込み** (`main.py`)
3. **Google Vision OCR実行** (DOCUMENT_TEXT_DETECTION)
4. **テキストファイル出力** (UTF-8形式)

## モジュール構成

### システム構成図

![](system.svg)

### 処理フロー図

![](process.svg)

### モジュール詳細

### A. APIキー管理モジュール (`declare_key.py`)
- Google Cloud Vision APIの認証情報管理
- サービスアカウントキーファイルの読み込み
- APIクライアントインスタンスの生成

### B. メイン処理モジュール (`main.py`)
- 画像ファイルの自動検出・ソート
- バッチ処理による効率的なOCR実行
- エラーハンドリングと処理結果の統計出力

### C. サンプルコード (`sample.py`)
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

### 1. 画像の準備
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

### 2. バッチOCR実行
```bash
cd test_ocr_for_doc2
python main.py
```

### 3. ディレクトリパスの設定
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

## Google Vision APIの特長

### 高精度認識
- 手書き文字の高精度認識
- 複雑なレイアウト・表構造の解析
- 多言語対応（日本語・英語混在）

### 豊富な情報抽出
- テキスト座標情報
- 信頼度スコア
- 文書構造の階層解析

### 自動前処理
- 傾き補正の自動実行
- ノイズ除去・コントラスト調整
- 画像品質最適化

## コスト管理

### 料金体系（2024年12月時点）
- 1,000リクエスト/月まで無料
- それ以降：$1.50/1,000リクエスト
- 詳細は[公式料金ページ](https://cloud.google.com/vision/pricing)を参照

### 使用量監視
Google Cloud Consoleの「APIs & Services」→「Quotas」で使用状況を監視可能

## セキュリティ注意事項

### 機密データの取り扱い
- 画像データはGoogleクラウドに一時的に送信されます
- 機密性の高い帳票の処理時は事前に利用規約を確認
- 必要に応じてデータマスキング処理を実装

### APIキーの保護
- サービスアカウントキー（`.json`）はGitにコミットしない
- 本番環境では環境変数やSecret Managerを使用
- キーファイルの適切なアクセス権限設定

## トラブルシューティング

### 認証エラー
```
google.auth.exceptions.DefaultCredentialsError
```
- サービスアカウントキーファイルのパスを確認
- APIが有効化されていることを確認

### クォータ超過エラー
```
Resource exhausted: Quota exceeded
```
- Google Cloud Consoleでクォータ使用状況を確認  
- 必要に応じてクォータの引き上げを申請

### 画像形式エラー
- 対応形式: PNG, JPEG, GIF, BMP, WebP, RAW, ICO, PDF, TIFF
- ファイルサイズ上限: 20MB
- 解像度推奨: 300DPI以上

## カスタマイズ・拡張

### 他のVision API機能との連携
- `TEXT_DETECTION`: シンプルなテキスト抽出
- `DOCUMENT_TEXT_DETECTION`: 文書構造解析（推奨）
- `HANDWRITING_DETECTION`: 手書き文字特化

### 後処理の実装
抽出されたテキストに対して：
- 正規表現による構造化
- 住所・金額の正規化  
- 信頼度による品質フィルタリング

### バッチ処理の最適化
- 非同期処理による高速化
- リトライロジックの実装
- 進捗表示・ログ強化

## 制限事項

- インターネット接続が必要
- API使用料金が発生
- Googleの利用規約に準拠する必要
- 大量処理時のレート制限