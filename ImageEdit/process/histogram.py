import cv2
import numpy as np

def histogram_image_from_cv2(cv2_img, width=512, height=120):
    if cv2_img is None:
        # Create a blank image
        img = np.full((height, width, 4), (250, 250, 250, 255), dtype=np.uint8)
        return img
    # cv2_img is BGR
    b, g, r = cv2.split(cv2_img)
    hr = cv2.calcHist([r], [0], None, [256], [0, 256]).flatten()
    hg = cv2.calcHist([g], [0], None, [256], [0, 256]).flatten()
    hb = cv2.calcHist([b], [0], None, [256], [0, 256]).flatten()
    maxi = max(hr.max(), hg.max(), hb.max(), 1)
    img = np.full((height, width, 4), (250, 250, 250, 255), dtype=np.uint8)
    bw = width / 256.0
    for i in range(256):
        x = int(i * bw)
        hrn = int((hr[i] / maxi) * (height - 4))
        hgn = int((hg[i] / maxi) * (height - 4))
        hbn = int((hb[i] / maxi) * (height - 4))
        for y in range(hrn):
            xi = x
            yi = height - 1 - y
            if 0 <= xi < width and 0 <= yi < height:
                img[yi, xi] = (255, 0, 0, 255)
        for y in range(hgn):
            xi = x + 1
            yi = height - 1 - y
            if 0 <= xi < width and 0 <= yi < height:
                img[yi, xi] = (0, 160, 0, 255)
        for y in range(hbn):
            xi = x + 2
            yi = height - 1 - y
            if 0 <= xi < width and 0 <= yi < height:
                img[yi, xi] = (0, 0, 255, 255)
    return img
