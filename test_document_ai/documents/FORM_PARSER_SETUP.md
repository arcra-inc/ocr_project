# Form Parser Processor 設定手順

Document AIのモデル側で構造抽出を行うには、**Form Parser Processor**を作成する必要があります。

## 1. Google Cloud Console での設定

### Step 1: Form Parser プロセッサを作成
1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. **Document AI** → **プロセッサギャラリー**
3. **「Form Parser」** を選択（**Document OCR**ではなく）
4. プロセッサ名を設定して作成
5. 新しいプロセッサIDを控える

### Step 2: Form Parser の特徴
- 🎯 **自動フォームフィールド検出**: ラベル-値のペアを自動認識
- 🎯 **エンティティ抽出**: 日付、金額、人名などを自動分類
- 🎯 **テーブル抽出**: 表構造も自動認識
- 🎯 **座標情報**: 各フィールドの位置も取得

### Step 3: レスポンス構造の違い

**Generic OCR (現在)**:
```json
{
  "document": {
    "text": "全文テキスト",
    "pages": [{"tokens": [...]}]
  }
}
```

**Form Parser**:
```json
{
  "document": {
    "text": "全文テキスト", 
    "pages": [
      {
        "formFields": [
          {
            "fieldName": {"textAnchor": ...},
            "fieldValue": {"textAnchor": ...}
          }
        ]
      }
    ],
    "entities": [
      {
        "type": "person_name",
        "mentionText": "田中太郎",
        "confidence": 0.95
      }
    ]
  }
}
```

## 2. プロセッサIDの変更方法

### main.py の設定を変更:

```python
# Generic OCR プロセッサ (現在)
processor_id = "1d1c870c661d0805"  # 現在のOCRプロセッサ
use_form_parser = False

# Form Parser プロセッサ (新規作成後)
processor_id = "新しいForm ParserのプロセッサID"  # 作成後に取得
use_form_parser = True
```

## 3. 処理モードの違い

### Generic OCR + パターンマッチング (現在):
- Document AI: テキスト抽出のみ
- クライアント: 正規表現でフィールド推測
- 精度: キーワード依存、不安定

### Form Parser (推奨):
- Document AI: モデル側でフィールド自動抽出
- クライアント: 抽出結果の整理のみ
- 精度: 機械学習ベース、高精度

## 4. 次のステップ

1. Google Cloud Console で Form Parser プロセッサを作成
2. 新しいプロセッサIDを取得
3. main.py の設定を変更:
   ```python
   processor_id = "新しいプロセッサID"
   use_form_parser = True
   ```
4. 処理を実行して結果を比較

## 5. 期待される改善

- ✅ フィールド抽出精度の向上
- ✅ 日付、金額、人名などの自動分類
- ✅ ラベル-値ペアの自動関連付け
- ✅ 事前パターン定義不要