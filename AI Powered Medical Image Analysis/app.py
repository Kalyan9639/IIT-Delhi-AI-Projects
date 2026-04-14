import os
import glob
import uuid
import shutil
import numpy as np
import tensorflow as tf
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from gradcam import make_gradcam_heatmap, save_and_display_gradcam
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Chest X-Ray Pneumonia Detection AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = None
OUTPUT_DIR = "output_images"

# Create static directory if it doesn't exist
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_frontend():
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend not found. Please create static/index.html"}

@app.on_event("startup")
def load_ml_model():
    global model
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Check for any .keras model in the artifacts mapping
    model_paths = glob.glob("artifacts/*.keras")
    
    if model_paths:
        # Prefer oversample if multiple are present, or pick the first one
        model_path = next((m for m in model_paths if "oversample" in m), model_paths[0])
        logger.info(f"Loading model from {model_path}...")
        model = tf.keras.models.load_model(model_path)
        logger.info("Model loaded successfully.")
    else:
        logger.warning("No model found in artifacts/. Please run training first.")

def preprocess_image(file_path):
    img = tf.io.read_file(file_path)
    # Ensure it's decoded as RGB (3 channels) even if grayscale input
    img = tf.image.decode_jpeg(img, channels=3)
    img = tf.image.resize(img, [224, 224])
    return np.expand_dims(img.numpy(), axis=0)

@app.post("/predict")
async def predict_xray(file: UploadFile = File(...)):
    if not model:
        raise HTTPException(status_code=500, detail="Machine learning model is not loaded.")
        
    temp_path = f"temp_{uuid.uuid4()}.jpg"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        img_array = preprocess_image(temp_path)
        # MobileNetV3 small uses [-1, 1] input range. If rescaling is needed, it's done internally
        pred = model.predict(img_array)[0][0]
        
        # Classification thresholds
        label = "PNEUMONIA" if pred >= 0.5 else "NORMAL"
        confidence = float(pred if pred >= 0.5 else 1.0 - pred)
        
        return JSONResponse(content={
            "prediction": label,
            "confidence": confidence
        })
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/gradcam")
async def generate_gradcam(file: UploadFile = File(...)):
    if not model:
        raise HTTPException(status_code=500, detail="Machine learning model is not loaded.")
        
    temp_path = f"temp_{uuid.uuid4()}.jpg"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        img_array = preprocess_image(temp_path)
        heatmap = make_gradcam_heatmap(img_array, model)
        
        output_filename = f"gradcam_{uuid.uuid4()}.jpg"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        save_and_display_gradcam(temp_path, heatmap, cam_path=output_path)
        
        return FileResponse(output_path, media_type="image/jpeg", filename=output_filename)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
