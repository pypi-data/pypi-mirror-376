import numpy as np
from skimage.color import rgb2gray
from skimage.exposure import match_histograms
from skimage.metrics import structural_similarity


def find_diference(imagem1, imagem2):
    assert imagem1.shape == imagem2.shape, "Specify 2 images with de same shape."
    gray_image1 = rgb2gray(imagem1)
    gray_image2 = rgb2gray(imagem2)
    (score, difference_image) = structural_similarity(gray_image1,gray_image2, full=True)
    print("Similaty of the images: ", score)
    normalized_diferrence_image = (difference_image-np.min(difference_image))/(np.max(difference_image)-np.min(difference_image))
    return normalized_diferrence_image

def tranfer_histogram(image1, image2):
    matched_imagem = match_histograms(image1,image2, multichannel=True)
    return matched_imagem