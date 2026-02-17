# Test Document AI

Google Cloud Document AIを使用したOCR処理システムです。Document AI Processorを活用して、高度な文書解析を行います。

## 概要

Document AIはGoogleの機械学習技術を活用した文書処理サービスです。単純なOCR（文字認識）だけでなく、文書構造の理解やエンティティ抽出など、より上位の解析が可能です。

## Vision API との比較

| 項目 | Vision API | Document AI |
|------|------------|-------------|
| OCR | 可能 | 可能 |
| 文書構造の理解 | 困難 | 可能 |
| エンティティ抽出 | 解析実装が必要 | 可能 |
| 帳票特化処理 | なし | あり |
| カスタムモデル | なし | あり |
| コスト | 低 | 高 |
| 処理時間 | 短 | やや長 |

## 前提条件

1. Google Cloudアカウントとプロジェクトの作成
2. Document AIサービスの有効化
3. Document AIプロセッサの作成
4. 認証情報の設定

## セットアップと実行手順

### Step 1: Google Cloud Document AIプロセッサの作成

1. [Google Cloud Console](https://console.cloud.google.com/)にログイン
2. Document AIサービスを有効化
3. Document AI > プロセッサギャラリーで「Document OCR」プロセッサを作成
4. プロセッサIDとリージョンを控える

**参考: https://codelabs.developers.google.com/codelabs/docai-ocr-python?hl=ja#0** 基本こちらの通りに設定すればよいです．帳票画像をOCRで読み取り、区分けしたフィールドごとにJSONとして出力する。

### Step 2: 環境準備

```bash
# プロジェクトディレクトリに移動
cd test_document_ai

# 仮想環境をアクティベート（Windows PowerShell）
..\ocr_env\Scripts\Activate.ps1

# 依存関係のインストール
pip install -r requirements.txt
```

### Step 3: 認証設定

以下のいずれかの方法で認証を設定：

**方法A: Application Default Credentials（推奨）**
```bash
gcloud auth application-default login
```

**方法B: サービスアカウントキーファイル**
1. Google Cloud Console > IAM > サービスアカウントでサービスアカウントを作成
2. 必要な権限を付与（Document AI API User）
3. キーファイル（JSON形式）をダウンロード
4. `main.py`内の`service_account_key_path`にファイルパスを設定

### Step 4: プロセッサ設定

`main.py`ファイル内の設定を実際の値に変更：

```python
# Document AIプロセッサ設定
processor_id = "YOUR_PROCESSOR_ID_HERE"  # 実際のプロセッサIDに変更
location = "us"  # プロセッサのリージョン

# 認証設定（どちらか選択）
service_account_key_path = None  # ADCを使用
# service_account_key_path = r"C:\path\to\service-account-key.json"  # キーファイルを使用
```

### Step 5: 設定テスト

設定確認とテストを実行する方法は2つあります：

**方法A: main.py経由（推奨）**
```bash
# セットアップテスト実行
python main.py setup_test
```

**方法B: 直接実行**
```bash
# 設定確認とテスト実行
python lib\setup_test.py
```

成功時の出力例：
```
✓ 認証成功: プロジェクトID = your-project-id
✓ Document AIクライアントを作成: your-project-id
✓ プロセッサセットアップ成功
✓ 全てのテストが成功しました！
```

### Step 6: OCR処理実行

```bash
# Document AI OCR処理を実行
python main.py
```

- **処理対象**: `documents/images/test/` 内の画像・PDFファイル
- **出力先**: `documents/ocr_results/`

## 出力形式

各画像ファイルに対して以下のファイルが生成されます：
- `{元ファイル名}_full.txt`: Document AIで認識された全文テキスト
- `{元ファイル名}_blocks.txt`: ブロック単位に分割されたテキスト

## サポートされるファイル形式

- PNG (.png)
- JPEG (.jpg, .jpeg)
- TIFF (.tif, .tiff)
- PDF (.pdf)

## PDFファイルの準備

PDFファイルをPNG画像に変換する場合は、プロジェクトルートの`util/convert_pdf_to_png.py`を使用してください：

```bash
# プロジェクトルートに移動
cd ..

# PDF→PNG変換スクリプト実行
python util\convert_pdf_to_png.py
```

詳細は`util/README.md`を参照してください。

## トラブルシューティング

### 認証エラー
```
Document AIクライアントの初期化に失敗
```

**解決方法:**
1. `gcloud auth application-default login`を実行
2. またはサービスアカウントキーファイルのパスを確認
3. Google Cloud SDKが正しくインストールされているか確認

### プロセッサIDエラー
```
プロセッサIDが設定されていません
```

**解決方法:**
1. Google Cloud ConsoleでDocument AIプロセッサを作成
2. プロセッサIDを`main.py`の`processor_id`変数に設定

### ディレクトリエラー
```
documents/images/test ディレクトリが見つかりません
```

**解決方法:**
1. `documents/images/test`ディレクトリを作成
2. 処理対象の画像ファイルを配置

## 制限事項・注意点

- Document AIはVision APIより高コスト
- 処理時間がやや長い（高精度のため）
- より複雑な設定が必要
- 文書タイプに特化したチューニングが推奨

## 参考リンク

- [Document AI公式ドキュメント](https://cloud.google.com/document-ai/docs)
- [Document AI料金](https://cloud.google.com/document-ai/pricing)
- [Google Cloud認証について](https://cloud.google.com/docs/authentication)