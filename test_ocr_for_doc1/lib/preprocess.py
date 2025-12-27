from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Tuple, Optional, Sequence, runtime_checkable
import numpy as np
import cv2


# ----------------------------
# 型とデータコンテナ
# ----------------------------
Image = np.ndarray  # BGR image (H, W, 3) or gray (H, W)

@dataclass(frozen=True)
class ThresholdResult:
    threshold: int
    binarized: Image  # single-channel 0/255 image

@dataclass(frozen=True)
class ContourResult:
    contours: Sequence[np.ndarray]  # list of contours
    chosen_contour: Optional[np.ndarray]  # selected contour (e.g. largest) or None

@dataclass(frozen=True)
class TransformResult:
    transformed: Image
    matrix: Optional[np.ndarray]  # 3x3 perspective matrix or None
    dst_size: Optional[Tuple[int, int]]


# ----------------------------
# Strategy interfaces
# ----------------------------
@runtime_checkable
class ThresholdStrategy(Protocol):
    def compute(self, gray: Image) -> ThresholdResult:
        """グレースケール画像 -> ThresholdResult"""

@runtime_checkable
class ContourStrategy(Protocol):
    def find(self, bin_img: Image) -> ContourResult:
        """二値化画像 -> 輪郭情報"""

@runtime_checkable
class PerspectiveTransformStrategy(Protocol):
    def compute(self, src_contour: np.ndarray, src_img: Image) -> TransformResult:
        """選択した輪郭と元画像 -> 射影変換結果"""


# ----------------------------
# デフォルト実装（現状の実装を整理）
# ----------------------------
class DefaultLuminanceThreshold:
    """
    ユーザ提示の luminance_threshold の整理版。
    入力はグレースケール画像、出力は二値化画像。
    """

    def __init__(self, luminance_percentage: float = 0.2, min_th: int = 100, max_th: int = 200):
        assert 0.0 < luminance_percentage <= 1.0
        self.luminance_percentage = luminance_percentage
        self.min_th = min_th
        self.max_th = max_th

    def compute(self, gray: Image) -> ThresholdResult:
        if gray is None:
            raise ValueError("gray image is None")

        flat = gray.flatten()
        number_threshold = flat.size * self.luminance_percentage

        # 探索は max_th から min_th まで下げる
        found = self.min_th
        for diff in range(self.max_th - self.min_th + 1):
            th = self.max_th - diff
            if np.count_nonzero(flat > th) >= number_threshold:
                found = th
                break

        _, bin_img = cv2.threshold(gray, found, 255, cv2.THRESH_BINARY)
        return ThresholdResult(threshold=found, binarized=bin_img)


class LargestContourSelector:
    """二値化画像から輪郭を抽出し、面積最大の輪郭を選ぶ実装。"""

    def __init__(self, retrieval=cv2.RETR_TREE, approximation=cv2.CHAIN_APPROX_SIMPLE):
        self.retrieval = retrieval
        self.approximation = approximation

    def find(self, bin_img: Image) -> ContourResult:
        if bin_img is None:
            raise ValueError("bin_img is None")
        contours, hierarchy = cv2.findContours(bin_img.copy(), self.retrieval, self.approximation)
        if not contours:
            return ContourResult(contours=(), chosen_contour=None)
        # 選択: 面積最大
        chosen = max(contours, key=cv2.contourArea)
        return ContourResult(contours=contours, chosen_contour=chosen)


class ApproxPolyPerspectiveTransform:
    """
    輪郭を凸多角形近似して4点を取り、透視変換する実装（ユーザの既存ロジックに基づく）。
    - src_contour: 単一 contour (Nx1x2)
    - src_img: 元 BGR 画像
    """
    def __init__(self, dst_width: int = 2400, card_ratio: float = 5.4 / 8.56, epsilon_coef: float = 0.1):
        self.dst_width = dst_width
        self.card_ratio = card_ratio
        self.epsilon_coef = epsilon_coef

    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        # pts: (4,2) float32, order -> tl, bl, br, tr  (user used a different order; choose canonical)
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]  # top-left
        rect[2] = pts[np.argmax(s)]  # bottom-right
        diff = np.diff(pts, axis=1).reshape(-1)
        rect[1] = pts[np.argmin(diff)]  # top-right
        rect[3] = pts[np.argmax(diff)]  # bottom-left
        return rect

    def compute(self, src_contour: np.ndarray, src_img: Image) -> TransformResult:
        if src_contour is None:
            return TransformResult(transformed=src_img, matrix=None, dst_size=None)

        epsilon = self.epsilon_coef * cv2.arcLength(src_contour, True)
        approx = cv2.approxPolyDP(src_contour, epsilon, True)

        # 4 点に近似できない場合、返す（拡張戦略で別処理）
        if approx.shape[0] < 4:
            # そのまま返却（あるいは凸包を使うなどの拡張）
            return TransformResult(transformed=src_img, matrix=None, dst_size=None)

        # もし近似点が >4 なら凸包して 4 点を挑戦的に取る
        pts = np.array([p[0] for p in approx], dtype="float32")
        if pts.shape[0] > 4:
            hull = cv2.convexHull(pts)
            pts = np.array([p[0] for p in hull], dtype="float32")
            # 再度取る（簡単化: ここでは最初の4点を取る実装）
            if pts.shape[0] > 4:
                pts = pts[:4]

        # order
        if pts.shape[0] != 4:
            # フォールバック
            return TransformResult(transformed=src_img, matrix=None, dst_size=None)

        rect = self._order_points(pts)
        dst_h = self.dst_width
        dst_w = int(round(self.dst_width * self.card_ratio))
        dst = np.array([[0, 0], [dst_w - 1, 0], [dst_w - 1, dst_h - 1], [0, dst_h - 1]], dtype="float32")

        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(src_img, M, (dst_w, dst_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return TransformResult(transformed=warped, matrix=M, dst_size=(dst_w, dst_h))


# ----------------------------
# 高レベル Preprocessor（Strategy 組み合わせ可能）
# ----------------------------
class Preprocessor:
    def __init__(
        self,
        threshold_strategy: ThresholdStrategy | None = None,
        contour_strategy: ContourStrategy | None = None,
        transform_strategy: PerspectiveTransformStrategy | None = None,
    ):
        self.threshold_strategy = threshold_strategy or DefaultLuminanceThreshold()
        self.contour_strategy = contour_strategy or LargestContourSelector()
        self.transform_strategy = transform_strategy or ApproxPolyPerspectiveTransform()

    # 公開 API: 1枚処理して最終的に透視変換画像を返す
    def process_one(self, bgr_img: Image) -> TransformResult:
        """
        入力: BGR image (np.ndarray)
        出力: TransformResult (transformed image + matrix + dst_size)
        """
        if bgr_img is None:
            raise ValueError("input image is None")

        # 1) グレースケール化
        gray = self._to_gray(bgr_img)

        # 2) 二値化（閾値算出）
        thr_res = self.threshold_strategy.compute(gray)

        # 3) 輪郭抽出・選択
        cnt_res = self.contour_strategy.find(thr_res.binarized)

        # 4) 透視変換
        trans_res = self.transform_strategy.compute(cnt_res.chosen_contour, bgr_img)

        return trans_res

    # ステップ単位 API：各ステップの入出力を明示的に呼べる
    @staticmethod
    def _to_gray(bgr: Image) -> Image:
        if bgr.ndim == 3 and bgr.shape[2] == 3:
            return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        elif bgr.ndim == 2:
            return bgr
        else:
            raise ValueError("invalid image shape")

    def compute_threshold(self, bgr: Image) -> ThresholdResult:
        gray = self._to_gray(bgr)
        return self.threshold_strategy.compute(gray)

    def find_contours(self, bin_img: Image) -> ContourResult:
        return self.contour_strategy.find(bin_img)

    def compute_transform(self, contour: np.ndarray, bgr: Image) -> TransformResult:
        return self.transform_strategy.compute(contour, bgr)


# ----------------------------
# 簡単な使用例（テスト）
# ----------------------------
if __name__ == "__main__":
    import sys
    from pathlib import Path
    from image_loader import ImageLoader  # ユーザのモジュールを想定

    # 現在のファイル位置から相対パスを計算
    current_dir = Path(__file__).parent
    test_imagefile_path = current_dir.parent / "documents" / "images" / "sample" / "sample.png"
    
    print(f"Looking for image at: {test_imagefile_path}")
    print(f"File exists: {test_imagefile_path.exists()}")

    loader = ImageLoader()
    img = loader.load_image(str(test_imagefile_path))
    if img is None:
        print("image load failed")
        sys.exit(1)
    
    cv2.imshow("Input Image", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    pre = Preprocessor()
    res = pre.process_one(img)

    print("Matrix:", None if res.matrix is None else res.matrix.shape)
    print("Dst size:", res.dst_size)

    # 確認: 保存して目視（macOS の imshow が不安定なときに便利）
    #cv2.imwrite("transformed_out.png", res.transformed)
    #print("Saved transformed_out.png")
    cv2.imshow("Transformed", res.transformed)
    cv2.waitKey(0)
    cv2.destroyAllWindows()