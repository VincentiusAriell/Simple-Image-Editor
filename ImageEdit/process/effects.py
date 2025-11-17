import cv2
import numpy as np

# Implementation mirrors single-file version but modularized

def clamp_arr(a: np.ndarray):
    np.clip(a, 0, 255, out=a)
    return a.astype(np.uint8)

def apply_effects_cv2(cv2_img,
                      brightness=0.0,
                      contrast=0.0,
                      highlights=0.0,
                      shadows=0.0,
                      saturation=0.0,
                      tint=0.0,
                      temperature=0.0,
                      sharpness=0.0):
    # cv2_img is BGR
    arr = cv2_img.astype(np.float32)

    bright_offset = (brightness/100.0)*255.0
    if abs(bright_offset) > 1e-6:
        arr += bright_offset

    c = np.clip(contrast, -99.0, 99.0)
    if abs(c) > 1e-6:
        factor = (259.0*(c+255.0))/(255.0*(259.0-c))
        arr = factor*(arr-128.0)+128.0

    hl = highlights/100.0
    sh = shadows/100.0
    if abs(hl) > 1e-6 or abs(sh) > 1e-6:
        # Convert to HSV for luminance
        hsv = cv2.cvtColor(arr.astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
        lum = hsv[:,:,2]
        mask_hi = lum > 128.0
        mask_lo = ~mask_hi
        hsv[mask_hi, 2] = hsv[mask_hi, 2] + (hsv[mask_hi, 2] - 128.0)*hl
        hsv[mask_lo, 2] = hsv[mask_lo, 2] + (128.0 - hsv[mask_lo, 2]) * sh * -1.0
        arr = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)

    temp = temperature/100.0
    t_adj = temp * 30.0
    arr[:,:,2] += t_adj  # R
    arr[:,:,0] -= t_adj  # B

    tint_adj = tint/100.0
    arr[:,:,1] += tint_adj*20.0  # G
    arr[:,:,2] -= tint_adj*6.0   # R
    arr[:,:,0] -= tint_adj*6.0   # B

    sat_factor = 1.0 + saturation/100.0
    if abs(sat_factor - 1.0) > 1e-6:
        hsv = cv2.cvtColor(arr.astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:,:,1] *= sat_factor
        arr = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)

    arr = clamp_arr(arr.astype(np.float32))

    if abs(sharpness) > 1e-6:
        s = max(-1.0, min(2.0, sharpness/100.0))
        radius = 1.0 + abs(s)*2.0
        amount = s * 1.5
        blurred = cv2.GaussianBlur(arr.astype(np.uint8), (0, 0), radius)
        blurred = blurred.astype(np.float32)
        result = arr + (arr - blurred) * amount
        result = clamp_arr(result)
        arr = result

    return arr.astype(np.uint8)

def apply_effects(cv2_img, effects_list):
    """Apply a list of effects to an image."""
    result = cv2_img.copy()
    for effect in effects_list:
        if isinstance(effect, dict):
            result = apply_effects_cv2(result, **effect)
        else:
            result = apply_effects_cv2(result, **effect)
    return result
