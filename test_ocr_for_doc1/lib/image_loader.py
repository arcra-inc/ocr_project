import cv2
from pathlib import Path

class ImageLoader:
    def load_image(self, image_path)->cv2.Mat:
        """
        指定されたパスから画像を読み込みます。
        """
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"画像ファイルが見つかりません: {image_path}")
        return image

if __name__ == "__main__":
    # image_loader.pyのテストコード
    # 現在のファイル位置から相対パスを計算
    current_dir = Path(__file__).parent
    test_imagefile_path = current_dir.parent / "documents" / "images" / "sample" / "sample.png"
    
    print(f"Looking for image at: {test_imagefile_path}")
    print(f"File exists: {test_imagefile_path.exists()}")

    loader = ImageLoader()
    img = loader.load_image(str(test_imagefile_path))
    cv2.imshow("Loaded Image", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
