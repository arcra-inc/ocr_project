from __future__ import annotations

import re
from pathlib import Path
from typing import List

from google.cloud import vision

from lib.declare_key import call_for_client


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


def main(images_dir: Path, output_txt_dir: Path, exts: set = None):
    """
    Google Vision APIを使用してOCR処理を実行
    
    Args:
        images_dir: 画像ファイルが格納されているディレクトリ
        output_txt_dir: OCR結果のテキストファイルを保存するディレクトリ
        exts: 対象とする画像の拡張子セット（デフォルト: {".png", ".jpg", ".jpeg", ".tif", ".tiff"}）
    """
    if exts is None:
        exts = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    
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
            out_txt.write_text(text, encoding="utf-8")

            print(f"[OK] {img_path.name} -> {out_txt.name} ({len(text)} chars)")
            ok += 1
        except Exception as e:
            print(f"[NG] {img_path.name} -> {e}")
            ng += 1

    print(f"Done. OK={ok}, NG={ng}, total={len(image_paths)}")


if __name__ == "__main__":

    current_dir = Path(__file__).parent
    images_dir = current_dir / "documents" / "images" / "sample" 
    output_txt_dir = current_dir / "documents" / "output_txt" / "sample" 
    
    # 帳票画像に適用したい場合は以下
    #images_dir = current_dir / "documents" / "images" / "test" 
    #output_txt_dir = current_dir / "documents" / "output_txt" / "test" 
    
    # 対象とする拡張子
    # このスクリプトは指定したディレクトリ以下にある指定拡張子のファイルをすべて処理します
    exts = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    # ===== 設定ここまで =====
    
    print(f"画像ディレクトリ: {images_dir}")
    print(f"出力ディレクトリ: {output_txt_dir}")
    print(f"画像ディレクトリ存在確認: {images_dir.exists()}")
    
    main(images_dir, output_txt_dir, exts)
