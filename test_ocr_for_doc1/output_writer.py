import json
import os
from typing import Dict, Any

class OutputWriter:
    @staticmethod
    def write_json(data: Dict[str, Any], filename: str, output_dir: str = ".")-> None:
        """
        抽出されたデータをJSON形式でファイルに書き込みます。
        このメソッドは静的メソッドとして定義されています。
        
        Args:
            data (Dict[str, Any]): 出力する辞書形式のデータ。複数階層を含むことができます。
            filename (str): 出力ファイル名。
            output_dir (str): 出力ディレクトリ。デフォルトはカレントディレクトリ。
        """
        if not isinstance(data, dict):
            raise TypeError("dataは辞書型である必要があります。")

        os.makedirs(output_dir, exist_ok=True) # ディレクトリが存在しない場合は作成
        output_path = os.path.join(output_dir, filename)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"JSONファイルを生成しました: {output_path}")
        except IOError as e:
            raise IOError(f"JSONファイルの書き込み中にエラーが発生しました: {e}")
        except Exception as e:
            raise Exception(f"予期せぬエラーが発生しました: {e}")
        

'''
適当な辞書型のオブジェクトを用意して，動作確認を行う．
'''
if __name__ == "__main__":
    sample_data = {
        "name": "山田太郎",
        "age": 30,
        "address": {
            "street": "東京都新宿区",
            "zip": "160-0022"
        },
        "items": [
            {"item_name": "ノートパソコン", "price": 120000},
            {"item_name": "スマートフォン", "price": 80000}
        ]
    }
    print("====OutputWriterのテスト====")
    print(f"入力データの型: {type(sample_data)}")
    print(f"出力データ: {sample_data}, ファイル名:  output.json, \n出力ディレクトリ: output_test")
    OutputWriter.write_json(sample_data, "output.json", output_dir="output_test")