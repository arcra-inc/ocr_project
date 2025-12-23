import cv2
from image_loader import ImageLoader
loader = ImageLoader()
img = loader.load_image('./temptest/image3.png')
cv2.imshow("Loaded Image", img)
cv2.waitKey(0)
cv2.destroyAllWindows()

# グレイスケール化
gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
cv2.imshow("Gray Image", gray_img)
cv2.waitKey(0)

cv2.destroyAllWindows()

import numpy as np
# nanacoは0.2くらいが良さそう。免許証の場合はまたチューニングが必要かも
card_luminance_percentage = 0.2

# TODO: パフォーマンス度外視
def luminance_threshold(gray_img):
    """
    グレースケールでの値(輝度と呼ぶ)が `x` 以上のポイントの数が20%を超えるような最大のxを計算する
    ただし、 `100 <= x <= 200` とする
    """
    number_threshold = gray_img.size * card_luminance_percentage
    flat = gray_img.flatten()
    # 200 -> 100 
    for diff_luminance in range(100):
        if np.count_nonzero(flat > 200 - diff_luminance) >= number_threshold:
            return 200 - diff_luminance
    return 100

threshold = luminance_threshold(gray_img)
print(f'threshold: {threshold}')


# 二値化
_, binarized = cv2.threshold(gray_img, threshold, 255, cv2.THRESH_BINARY)
cv2.imshow("Binalized Image",cv2.cvtColor(binarized, cv2.COLOR_BGR2RGB))
cv2.waitKey(0)
cv2.destroyAllWindows() 

# 輪郭抽出(Contour extraction)
contours, _ = cv2.findContours(binarized, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

# 面積最大のものを選択
card_cnt = max(contours, key=cv2.contourArea)

# 画像に輪郭を描画
line_color = (0, 255, 0)
thickness = 30
cv2.drawContours(img, [card_cnt], -1, line_color, thickness)
cv2.imshow("Contour extraction",cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
cv2.waitKey(0)
cv2.destroyAllWindows()


# 輪郭を凸形で近似
# 輪郭の全長に固定値で 0.1 の係数をかけるので十分
# ある程度まともにカードを写す前提では係数のチューニングはほぼ不要と思われる(OCRの調整では必要かも)
epsilon = 0.1 * cv2.arcLength(card_cnt, True)
approx = cv2.approxPolyDP(card_cnt, epsilon, True)

# カードの横幅(画像がカードが縦になっているので、射影変換の際にはwidthとheightが逆になっている)
card_img_width = 2400 # 適当な値
card_img_height = round(card_img_width * (5.4 / 8.56)) # 免許証のration(=nanacoのratio)で割って産出

src = np.float32(list(map(lambda x: x[0], approx)))
dst = np.float32([[0,0],[0,card_img_width],[card_img_height,card_img_width],[card_img_height,0]])

projectMatrix = cv2.getPerspectiveTransform(src, dst)

# 先ほどで線が上書きされたので再度画像を取得
img = cv2.imread('./temptest/image3.png')
transformed = cv2.warpPerspective(img, projectMatrix, (card_img_height, card_img_width))
cv2.imshow("rolled",cv2.cvtColor(transformed, cv2.COLOR_BGR2RGB))
cv2.waitKey(0)
cv2.destroyAllWindows()


# ひとまずこれで仮実装終了
'''
TODO: テストのimage3でもわかるように背景の色合いによって輪郭検出がうまくいかない場合がある．
他の手法でエッジ検出を行い，そのエッジによって傾き補正を行う方法を実装する必要がある．

この部分は手法がたくさんあるのでstrategyパターンで実装するのが良さそう．
'''