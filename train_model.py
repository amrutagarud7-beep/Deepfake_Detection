import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

# create fake dataset
X = np.random.rand(200,16384)
y = np.random.randint(0,2,200)

# train model
model = RandomForestClassifier()

model.fit(X,y)

# create model folder
os.makedirs("model",exist_ok=True)

# save model
joblib.dump(model,"model/deepfake_model.pkl")

print("Model created successfully!")