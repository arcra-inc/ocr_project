from __future__ import annotations

import re
from pathlib import Path
from typing import List

from google.cloud import vision

from declare_key import call_for_client


def natural_key(path: Path):
    """
    page_001.png, page_002.png ... のようなファイルを自然順で並べるためのキー
    """
    return [int(s) if s.isdigit() else s.lower() for s in re.split(r"(\d+)", path.name)]


def ocr_image_to_text(client: vision.ImageAnnotatorClient, image_path: Path) -> str:
    """
    Google Vision OCR (DOCUMENT_TEXT_DETECTION) で画像から全文テキストを取得
    """
    content = image_path.read_bytes()
    image = vision.Image(content=content)

    # 文書向け（帳票など）では DOCUMENT_TEXT_DETECTION が基本
    response = client.document_text_detection(image=image)

    if response.error.message:
        raise RuntimeError(f"Vision API error: {response.error.message}")

    ann = response.full_text_annotation
    return ann.text if ann and ann.text else ""


def main():
    # ===== 設定ここから =====
    images_dir = Path(
        r"C:\Users\NakanoShiryu\Documents\workspace\ocr_project\test_ocr_for_doc2\documents\images\pdf_pages"
    )
    output_txt_dir = Path(
        r"C:\Users\NakanoShiryu\Documents\workspace\ocr_project\test_ocr_for_doc2\documents\ocr_txt"
    )

    # 対象拡張子（必要なら追加）
    exts = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    # ===== 設定ここまで =====

    if not images_dir.exists():
        raise FileNotFoundError(f"images_dir not found: {images_dir}")

    output_txt_dir.mkdir(parents=True, exist_ok=True)

    image_paths: List[Path] = sorted(
        [p for p in images_dir.iterdir() if p.is_file() and p.suffix.lower() in exts],
        key=natural_key,
    )

    if not image_paths:
        print(f"No images found in: {images_dir}")
        return

    #client = vision.ImageAnnotatorClient()
    client = call_for_client()  # Use the imported function to get the client, this way the key file path is centralized

    ok = 0
    ng = 0

    for img_path in image_paths:
        try:
            text = ocr_image_to_text(client, img_path)

            out_txt = output_txt_dir / f"{img_path.stem}.txt"
            # UTF-8で保存（日本語OK）。Windowsメモ帳互換なら 'utf-8-sig' も可
            out_txt.write_text(text, encoding="utf-8")

            print(f"[OK] {img_path.name} -> {out_txt.name} ({len(text)} chars)")
            ok += 1
        except Exception as e:
            print(f"[NG] {img_path.name} -> {e}")
            ng += 1

    print(f"Done. OK={ok}, NG={ng}, total={len(image_paths)}")


if __name__ == "__main__":
    main()
