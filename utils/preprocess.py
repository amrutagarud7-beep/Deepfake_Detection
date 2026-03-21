import cv2
import numpy as np

def preprocess_image(path):

    img = cv2.imread(path)

    img = cv2.resize(img, (128,128))

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    features = gray.flatten().reshape(1,-1)

    return features