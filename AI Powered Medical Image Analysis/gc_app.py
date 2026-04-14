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

# Setup logging for Cloud Run logs
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

# CLOUD RUN OPTIMIZATION: Use /tmp for all write operations. 
# The root directory in Cloud Run is read-only.
OUTPUT_DIR = "/tmp/output_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Static files remain in the project folder (read-only is fine for serving)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_frontend():
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend not found. Please ensure static/index.html is in your container."}

@app.on_event("startup")
def load_ml_model():
    global model
    # Look for model in the artifacts directory copied during Docker build
    model_paths = glob.glob("artifacts/*.keras")
    
    if model_paths:
        model_path = next((m for m in model_paths if "oversample" in m), model_paths[0])
        logger.info(f"Loading model from {model_path}...")
        # MobileNetV3 is efficient for Cloud Run's RAM limits
        model = tf.keras.models.load_model(model_path)
        logger.info("Model loaded successfully.")
    else:
        logger.error("No model found in artifacts/. Deployment will fail to predict.")

def preprocess_image(file_path):
    img = tf.io.read_file(file_path)
    img = tf.image.decode_jpeg(img, channels=3)
    img = tf.image.resize(img, [224, 224])
    return np.expand_dims(img.numpy(), axis=0)

@app.post("/predict")
async def predict_xray(file: UploadFile = File(...)):
    if not model:
        raise HTTPException(status_code=500, detail="Model not loaded on server.")
        
    # CLOUD RUN OPTIMIZATION: Write temp file to /tmp
    temp_path = os.path.join("/tmp", f"temp_{uuid.uuid4()}.jpg")
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        img_array = preprocess_image(temp_path)
        pred = model.predict(img_array)[0][0]
        
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
        raise HTTPException(status_code=500, detail="Model not loaded on server.")
        
    # CLOUD RUN OPTIMIZATION: Write temp file to /tmp
    temp_path = os.path.join("/tmp", f"temp_{uuid.uuid4()}.jpg")
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
            # Clean up input temp file; Cloud Run /tmp uses memory, so keep it tidy
            os.remove(temp_path)

if __name__ == "__main__":
    # CLOUD RUN OPTIMIZATION: Use the PORT env variable provided by Google
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
