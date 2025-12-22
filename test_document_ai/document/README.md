# Test Document AI

Google Cloud Document AIを使用した帳票処理システムの実装です。Document AI Processorを活用して、より高度な文書解析を行います。

## 考え方・設計指針

Document AI は Google Cloud 上の文書理解サービスです。単純なOCR（文字の読み取り）だけでなく、文書構造の理解やエンティティ抽出など、より上位の解析が可能です。

設計上の狙いは以下です。

- Vision OCRで取得した「生テキスト」だけでは不足するケースに対する上位選択肢として扱う
- Vision OCRと比較して、コスト、レイテンシ、プライバシー制約などのトレードオフを評価する
- どのデータをクラウドへ送るか、ローカルに残すかの境界を明確にする

## Vision API との比較

| 項目 | Vision API | Document AI |
|------|------------|-------------|
| OCR | 可能 | 可能 |
| 文書構造の理解 | 限定的 | 可能 |
| エンティティ抽出 | 解析実装が必要 | 可能 |
| 帳票特化処理 | なし | あり |
| カスタムモデル | なし | あり |

## プロセッサ情報

### 基本設定
- **名前**: test
- **プロセッサID**: 1d1c870c661d0805
- **タイプ**: Document OCR
- **リージョン**: us
- **作成日**: 2025/12/16 15:46:40

### エンドポイント
```
https://us-documentai.googleapis.com/v1/projects/468362817242/locations/us/processors/1d1c870c661d0805:process
```

## セットアップ手順

### 1. Google Cloud Document AIの有効化
1. Google Cloud Consoleでプロジェクトを選択
2. Document AIを有効化
3. プロセッサを作成（Document OCR）

### 2. 認証設定
Vision APIと同様のサービスアカウント設定を使用

### 3. パッケージインストール
```bash
pip install google-cloud-documentai
```

## 使用方法

### 基本的なDocument AI呼び出し
```python
from google.cloud import documentai

# クライアント初期化
client = documentai.DocumentProcessorServiceClient()

# プロセッサパス
processor_name = "projects/468362817242/locations/us/processors/1d1c870c661d0805"

# 文書処理リクエスト
request = documentai.ProcessRequest(
    name=processor_name,
    raw_document=documentai.RawDocument(
        content=document_content,
        mime_type="image/png"
    )
)

# 処理実行
result = client.process_document(request=request)
```

## Document AIの優位性

### 高度な構造解析
- 表の行・列構造の自動認識
- ヘッダー・フッターの識別
- 段落・リストの階層構造

### エンティティ抽出
- 日付・金額の自動識別
- 会社名・住所の抽出
- カスタムエンティティの学習

### 帳票特化機能
- 請求書・領収書の専用プロセッサ
- フォーム項目の自動マッピング
- 信頼度スコアによる品質管理

## 実装予定

このディレクトリは将来の拡張用に予約されています：

1. **Document AI Processor実装**
   - 高度な文書構造解析
   - エンティティ抽出機能
   - カスタムモデル学習

2. **比較分析システム**
   - Vision API vs Document AI精度比較
   - コストパフォーマンス分析
   - 用途別推奨システム

3. **ハイブリッド処理**
   - 文書タイプによる自動振り分け
   - フォールバック機構
   - 処理結果の統合

## 制限事項・注意点

- Document AIはVision APIより高コスト
- 処理時間がやや長い
- より複雑な設定が必要
- 文書タイプに特化したチューニングが推奨

## 参考リンク

- [Google Cloud Document AI](https://cloud.google.com/document-ai)
- [Document AI Processors](https://cloud.google.com/document-ai/docs/processors-list)
- [Document AI Pricing](https://cloud.google.com/document-ai/pricing)