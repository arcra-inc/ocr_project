from pdf2image import convert_from_path
from pathlib import Path

pdf_path = Path(r"C:\Users\NakanoShiryu\Documents\workspace\ocr_project\test_ocr_for_doc2\documents\images\test.pdf")
output_dir = Path(r"C:\Users\NakanoShiryu\Documents\workspace\ocr_project\test_ocr_for_doc2\documents\images")
output_dir.mkdir(parents=True, exist_ok=True)

POPPLER_BIN = r"C:\Users\NakanoShiryu\Downloads\Release-25.12.0-0\poppler-25.12.0\Library\bin" # ←あなたの環境に合わせて変更

images = convert_from_path(
    pdf_path,
    dpi=300,
    fmt="png",
    poppler_path=POPPLER_BIN
)

for i, img in enumerate(images, start=1):
    out_path = output_dir / f"page_{i:03}.png"
    img.save(out_path, "PNG")

print(f"{len(images)} pages converted.")
