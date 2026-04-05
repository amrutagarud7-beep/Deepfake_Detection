import tensorflow as tf
from tensorflow.keras.applications import EfficientNetB4
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping
import os

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR  = "dataset/real_vs_fake/real-vs-fake"
TRAIN_DIR = os.path.join(BASE_DIR, "train")
VALID_DIR = os.path.join(BASE_DIR, "valid")
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

# ── Settings ───────────────────────────────────────────────────────────
IMG_SIZE   = 224
BATCH_SIZE = 32
EPOCHS     = 5          # reduced from 10
TRAIN_SAMPLES = 5000    # only 5000 images instead of 100,000
VALID_SAMPLES = 1000

# ── Data loaders ───────────────────────────────────────────────────────
train_gen = ImageDataGenerator(
    rescale=1./255,
    horizontal_flip=True,
    rotation_range=10,
    zoom_range=0.1
)
valid_gen = ImageDataGenerator(rescale=1./255)

train_data = train_gen.flow_from_directory(
    TRAIN_DIR, target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE, class_mode="binary",
    subset=None
)
valid_data = valid_gen.flow_from_directory(
    VALID_DIR, target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE, class_mode="binary"
)

# ── Limit samples ──────────────────────────────────────────────────────
import math
train_steps = math.ceil(TRAIN_SAMPLES / BATCH_SIZE)
valid_steps = math.ceil(VALID_SAMPLES / BATCH_SIZE)

# ── Build model ────────────────────────────────────────────────────────
base = EfficientNetB4(weights="imagenet", include_top=False,
                      input_shape=(IMG_SIZE, IMG_SIZE, 3))
base.trainable = False

x = GlobalAveragePooling2D()(base.output)
x = Dropout(0.3)(x)
out = Dense(1, activation="sigmoid")(x)
model = Model(base.input, out)

model.compile(optimizer="adam", loss="binary_crossentropy",
              metrics=["accuracy"])

# ── Callbacks ──────────────────────────────────────────────────────────
callbacks = [
    ModelCheckpoint(
        os.path.join(MODEL_DIR, "deepfake_model.h5"),
        save_best_only=True, monitor="val_accuracy", verbose=1
    ),
    EarlyStopping(patience=3, monitor="val_accuracy",
                  restore_best_weights=True, verbose=1)
]

# ── Train ──────────────────────────────────────────────────────────────
print("\n Starting training (fast mode)...\n")
model.fit(
    train_data,
    steps_per_epoch=train_steps,
    validation_data=valid_data,
    validation_steps=valid_steps,
    epochs=EPOCHS,
    callbacks=callbacks
)
print("\n Training complete! Model saved to models/deepfake_model.h5")