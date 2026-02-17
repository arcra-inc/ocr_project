from pdf2image import convert_from_path
from pathlib import Path
import shutil

# 画像変換
## 変換するPDFのファイルパス
pdf_path = Path(r"/Users/arcra/dev-arcra/ocr_project/test_ocr_for_doc2/documents/pdf/材料表３.pdf")
## 変更先の画像フォルダ
output_dir = Path(r"/Users/arcra/dev-arcra/ocr_project/test_ocr_for_doc2/documents/images/test")
output_dir.mkdir(parents=True, exist_ok=True)
# output_dir2 = Path(r"/Users/arcra/dev-arcra/ocr_project/test_ocr_for_doc2/documents/images/test")
# output_dir2.mkdir(parents=True, exist_ok=True)


# Mac版
# pdftoppm_path = shutil.which("pdftoppm")
# POPPLER_BIN = str(Path(pdftoppm_path).parent) if pdftoppm_path else None
# Windows版
POPPLER_BIN = r"C:\Users\-----\Downloads\Release-25.12.0-0\poppler-25.12.0\Library\bin" 

images = convert_from_path(
    pdf_path,
    dpi=300,
    fmt="png",
    poppler_path=POPPLER_BIN
)

for i, img in enumerate(images, start=1):
    print(f"Saving page {i}...")    
    out_path = output_dir / f"page_{i:03}.png"
    # out_path2 = output_dir2 / f"page_{i:03}.png"
    img.save(out_path, "PNG")
    # img.save(out_path2, "PNG")  

print(f"{len(images)} pages converted.")
