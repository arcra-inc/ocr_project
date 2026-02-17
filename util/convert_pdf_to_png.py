from pdf2image import convert_from_path
from pathlib import Path

pdf_path = Path(r"C:\Users\NakanoShiryu\Documents\workspace\ocr_project\test.pdf")
output_dir = Path(r"C:\Users\NakanoShiryu\Documents\workspace\ocr_project\test_ocr_for_doc2\documents\images\test")
output_dir2 = Path(r"C:\Users\NakanoShiryu\Documents\workspace\ocr_project\test_document_ai\documents\images\test")
output_dir.mkdir(parents=True, exist_ok=True)
output_dir2.mkdir(parents=True, exist_ok=True)


POPPLER_BIN = r"C:\Users\NakanoShiryu\Downloads\Release-25.12.0-0\poppler-25.12.0\Library\bin" # ←環境に合わせて変更

images = convert_from_path(
    pdf_path,
    dpi=300,
    fmt="png",
    poppler_path=POPPLER_BIN
)

for i, img in enumerate(images, start=1):
    print(f"Saving page {i}...")    
    out_path = output_dir / f"page_{i:03}.png"
    out_path2 = output_dir2 / f"page_{i:03}.png"
    img.save(out_path, "PNG")
    img.save(out_path2, "PNG")  

print(f"{len(images)} pages converted.")
