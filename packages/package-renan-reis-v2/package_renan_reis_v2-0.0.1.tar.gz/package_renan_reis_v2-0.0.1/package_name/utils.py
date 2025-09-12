import cv2
import matplotlib as plt

def load_image(path):
    """Carrega a imagem a partir de um caminho"""
    return cv2.imread(path)

def show_image(image, cmap=None):
    """Mostra a imagem na tela"""
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB), cmap=cmap)
    plt.axis("off")
    plt.show()
