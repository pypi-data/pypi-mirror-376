from package_name import filters
from PIL import Image

filters.my_function()

import cv2

def apply_grayscale(image):
    """Converte a imagem para tons de cinza"""
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

def apply_blur(image, ksize=(5,5)):
    """Aplica um desfoque (blur) na imagem"""
    return cv2.GaussianBlur(image, ksize, 0)
