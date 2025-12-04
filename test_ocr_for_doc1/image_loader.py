import cv2

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
    test_imagedir_path = "temptest"
    test_imagefile_path = f"{test_imagedir_path}/image.png"

    loader = ImageLoader()
    img = loader.load_image(test_imagefile_path)
    cv2.imshow("Loaded Image", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
