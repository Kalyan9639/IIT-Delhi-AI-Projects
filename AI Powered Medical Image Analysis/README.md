# NexusMed AI: Advanced Pulmonary Diagnostics & Visualization

![Python Badge](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![TensorFlow Badge](https://img.shields.io/badge/TensorFlow-2.21-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)
![FastAPI Badge](https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)

NexusMed AI is an industry-grade, end-to-end artificial intelligence application designed to detect Pneumonia from chest X-ray radiographs. The exact decision-making process of the model is fully transparent through **Grad-CAM Attention Maps**, making it a highly reliable and explainable medical tool. 

Coupled with a beautifully designed user interface, NexusMed AI seamlessly bridges complex deep learning models with accessible medical diagnostics.

---

## 🌟 Key Features

*   **Deep Learning Diagnostics**: Utilizes a highly optimized `MobileNetV3Small` backbone to accurately classify radiographs into NORMAL or PNEUMONIA. 
*   **Explainable AI (XAI) via Grad-CAM**: Automatically highlights the specific pulmonary regions that influenced the overarching neural network's pathogenic assessment, allowing doctors and users to verify model logic.
*   **Intelligent Imbalance Handling**: Built-in comprehensive dataset balancing implementations (`oversample`, `undersample`, `class_weights`) to gracefully prevent dominant class overfitting.
*   **Premium Web Application Dashboard**: 
    *   **Interactive tsParticles background** replicating a dynamic, moving neural network.
    *   **Glassmorphism styling**, smooth transition micro-animations, and animated loading scanners.
    *   **Asynchronous Dual-Fetching**: Extracts both high-confidence predictions and diagnostic heatmaps simultaneously via native JavaScript.
    *   Fully served by the native **FastAPI backend** asynchronously. 

---

## 🚀 Technology Stack

**Backend System:**
*   **Python 3.12**
*   **TensorFlow & Keras 3** (Modeling & Inference)
*   **FastAPI / Uvicorn** (REST Architecture)
*   **Scikit-Learn** (Calculates trustworthy evaluation metrics including custom F1, Precision, and Recall scores)

**Visual & Interface System:**
*   **HTML5, Vanilla JS, Pure CSS3**
*   **OpenCV** (Heatmap generation and blending)
*   **tsParticles** (Hardware accelerated 3D canvas backgrounds)

---

## 💻 Installation & Setup

### Prerequisites
Make sure you have Python 3.10+ installed and preferably a virtual environment active. 

### 1. Clone the Source
```bash
git clone https://github.com/your-username/NexusMed-AI.git
cd NexusMed-AI
```

### 2. Install Requirements
```bash
pip install -r requirements.txt
```

### 3. Model Training
If you do not have a pre-trained `.keras` model artifact, you must train the model using your chest X-ray dataset directory. Place the directory in the project root containing `train`, `test`, `val` folders. 
```bash
python train.py --method oversample --epochs 20 --batch_size 32 --data_dir chest_xray
```
*(Check `artifacts/metrics.json` after completion for industry-standard evaluation profiles!)*

### 4. Boot up the NexusMed App
```bash
uvicorn app:app --reload
```
Navigate to **http://localhost:8000/** in your web browser. 

---

## 🎥 App Usage

1. **Upload**: Drag and drop a chest radiograph (`.jpg` or `.png`) directly into the specialized scanner zone. 
2. **Scan**: Click "Initiate Diagnostic Scan". 
3. **Analyze**: The backend instantly routes the image internally to TensorFlow, runs predict logs, and calculates the Grad-CAM representation. 
4. **Results**: A sleek glass dashboard reveals the overall Neural Impression alongside the calculated heatmap!

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

Enjoy scaling automated medical diagnostics ⚡
