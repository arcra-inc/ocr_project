# 出力ファイル制御の使用例

main.pyの出力フラグ設定を変更することで、必要なファイルのみを出力できます。

## 設定例

### 1. 全ファイル出力（デフォルト）
```python
output_text = True            # テキストファイル(.txt)出力
output_raw_json = True        # 生JSONファイル(.json)出力  
output_structured_json = True # 構造化JSONファイル(.json)出力
```

### 2. 構造化JSONのみ出力
```python
output_text = False           # テキストファイル出力しない
output_raw_json = False       # 生JSON出力しない
output_structured_json = True # 構造化JSONのみ出力
```

### 3. テキストと構造化JSONのみ出力
```python
output_text = True            # テキストファイル出力
output_raw_json = False       # 生JSON出力しない
output_structured_json = True # 構造化JSON出力
```

### 4. 生JSONのみ出力（デバッグ用）
```python
output_text = False           # テキストファイル出力しない
output_raw_json = True        # 生JSONのみ出力
output_structured_json = False# 構造化JSON出力しない
```

## 出力ファイル
- **テキストファイル**: `{ファイル名}_text.txt` - 全文テキスト
- **生JSONファイル**: `{ファイル名}_raw_response.json` - Document AIの未処理レスポンス
- **構造化JSONファイル**: `{ファイル名}_structured_fields.json` - フィールドと値のみの簡素化データ

フラグを変更してpython main.pyを実行すると、設定に応じたファイルのみが生成されます。