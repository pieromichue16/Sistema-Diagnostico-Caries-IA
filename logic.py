import os
# Configurar entorno antes de importar Keras
os.environ["SM_FRAMEWORK"] = "tf.keras"

import tensorflow as tf
from tensorflow import keras
import numpy as np
import cv2
import segmentation_models as sm

MODELO_PATH = "modelo_unet_caries_HD.h5"
IMG_SIZE = 512

# Parche de compatibilidad (Obligatorio para que no falle en tu PC)
try:
    if not hasattr(keras.utils, "generic_utils"):
        keras.utils.generic_utils = keras.utils
except: pass

def cargar_modelo_ia():
    if not os.path.exists(MODELO_PATH): return None
    return tf.keras.models.load_model(MODELO_PATH, compile=False)

# Inicializar preprocesador
preprocess_input = sm.get_preprocessing('resnet50')

def procesar_y_predecir(model, img_array):
    """
    Recibe la imagen en array RGB.
    Devuelve: (Máscara binaria procesada, Contornos encontrados, Cantidad de lesiones)
    """
    orig_h, orig_w = img_array.shape[:2]
    
    # 1. Preprocesamiento
    img_r = cv2.resize(img_array, (IMG_SIZE, IMG_SIZE))
    img_in = np.expand_dims(img_r, axis=0).astype(np.float32)
    img_in = preprocess_input(img_in)
    
    # 2. Inferencia
    pred = model.predict(img_in, verbose=0)[0]
    
    # 3. Post-procesamiento
    mask = (pred > 0.5).astype(np.uint8)
    mask = cv2.resize(mask, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)
    
    # 4. Encontrar contornos
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    return contours, len(contours)