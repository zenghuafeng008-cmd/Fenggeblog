# -*- coding: utf-8 -*-
"""去水印模块 - OpenCV + PIL"""
import os, numpy as np
from PIL import Image

def remove_watermark_opencv(image_path, output_path=None, region=None):
    """
    使用OpenCV去水印 - 基于区域填充
    region: (x1, y1, x2, y2) 水印区域
    """
    if output_path is None:
        output_path = image_path.replace(".jpg", "_nowatermark.jpg")
    
    img = cv2.imread(image_path)
    if img is None:
        return None
    
    if region:
        x1, y1, x2, y2 = region
        # 使用周围像素填充
        mask = np.zeros(img.shape[:2], dtype=np.uint8)
        mask[y1:y2, x1:x2] = 255
        
        # 检查是否是彩色图像
        if len(img.shape) == 3:
            result = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
        else:
            result = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
    else:
        result = img
    
    cv2.imwrite(output_path, result)
    return output_path

def detect_and_remove_watermark(image_path, output_path=None):
    """
    自动检测并去除水印 - 假设水印在角落
    """
    import cv2
    
    if output_path is None:
        output_path = image_path.replace(".jpg", "_clean.jpg")
    
    img = cv2.imread(image_path)
    if img is None:
        return None
    
    h, w = img.shape[:2]
    
    # 常见水印位置：右下角、右上角、左下角
    regions = [
        (w - 200, h - 80, w, h),      # 右下
        (w - 200, 0, w, 80),          # 右上
        (0, h - 80, 200, h),          # 左下
        (0, 0, 200, 80),              # 左上
    ]
    
    for region in regions:
        x1, y1, x2, y2 = region
        roi = img[y1:y2, x1:x2]
        
        # 检测是否可能是水印（浅色区域）
        if roi.size > 0:
            mean_val = np.mean(roi)
            if mean_val > 200 or mean_val < 50:  # 可能是水印
                mask = np.zeros(img.shape[:2], dtype=np.uint8)
                mask[y1:y2, x1:x2] = 255
                img = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
                break
    
    cv2.imwrite(output_path, img)
    return output_path

def remove_text_watermark_pil(image_path, output_path=None):
    """
    使用PIL去水印 - 基于颜色处理
    适用于文字水印
    """
    if output_path is None:
        output_path = image_path.replace(".jpg", "_text_removed.jpg")
    
    img = Image.open(image_path)
    img = img.convert("RGBA")
    
    # 获取像素数据
    pixels = np.array(img)
    
    # 检测接近白色的像素（水印通常是白色半透明）
    white_mask = (
        (pixels[:, :, 0] > 200) & 
        (pixels[:, :, 1] > 200) & 
        (pixels[:, :, 2] > 200) &
        (pixels[:, :, 3] > 50) &
        (pixels[:, :, 3] < 200)
    )
    
    # 将检测到的水印像素设为透明
    pixels[white_mask] = [255, 255, 255, 0]
    
    # 保存
    result = Image.fromarray(pixels)
    result.save(output_path)
    return output_path

def batch_remove_watermark(input_dir, output_dir=None, method="auto"):
    """
    批量去水印
    """
    import cv2
    
    if output_dir is None:
        output_dir = input_dir + "_clean"
    os.makedirs(output_dir, exist_ok=True)
    
    results = []
    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
        
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        
        if method == "auto":
            result = detect_and_remove_watermark(input_path, output_path)
        elif method == "text":
            result = remove_text_watermark_pil(input_path, output_path)
        else:
            result = remove_watermark_opencv(input_path, output_path)
        
        if result:
            results.append(result)
    
    return results
