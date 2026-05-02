# SentimentX: Real-Time Twitter Sentiment Analysis Dashboard

SentimentX is an end-to-end AI system that leverages a fine-tuned **DistilBERT** transformer model to classify social media sentiment with high accuracy and low latency. Built for the modern web, it features a dark-themed dashboard that provides real-time single-tweet inference and mass-analysis capabilities for large datasets.

## 🔗 Model Repository
The fine-tuned weights for this project are hosted on Hugging Face:
**[Hugging Face Model ](https://huggingface.co/mr-checker/distilbert-sentimentx-twitter)**

## 🚀 Key Features

* **Transformer-based Inference:** Utilizes a custom fine-tuned `distilbert-base-uncased` model.
* **Real-Time Predictor:** Instant sentiment classification (Positive/Negative) of user-inputted text.
* **Batch Analysis:** Process full `.csv` or `.tsv` datasets through the web UI using the "Batch Analysis" feature.
* **High Throughput:** Optimized for inference rates of **1,400+ samples/second** using GPU acceleration.
* **Modern UI:** Dark-mode dashboard built with Tailwind CSS and Chart.js for visualizing sentiment volatility.

## 🏗️ Architecture

The project follows a **Hybrid Cloud-Edge** workflow:
1.  **Cloud Training:** Model fine-tuning was performed on the **Sentiment140** (1.6M tweets) dataset using Kaggle's NVIDIA GPUs.
2.  **Local Deployment:** The system is served via a **FastAPI** backend, allowing the model to run locally on your hardware for privacy and speed.

## 📊 Model Performance

| Metric | Score |
| :--- | :--- |
| **Accuracy** | 82.44% |
| **F1-Score** | 82.50% |
| **Precision** | 83.01% |
| **Recall** | 81.99% |

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Kalyan9639/IIT-Delhi-AI-Projects/tree/main/Machine%20Learning/Social%20Media%20Sentiment%20Analysis.git
cd "IIT-Delhi-AI-Projects/tree/main/Machine%20Learning/Social%20Media%20Sentiment%20Analysis"
```

### 2. Install Dependencies
```bash
pip install fastapi uvicorn torch transformers pandas scikit-learn
```

### 3. Model Setup
The backend is configured to load the model from a local directory or directly from Hugging Face. To run locally, ensure your model files are in a folder named `social_sentiment_model`.

### 4. Launch the Dashboard
Start the FastAPI backend:
```bash
python main.py
```
Then, open `index.html` in your browser.

## 📂 Project Structure
```text
├── social_sentiment_model/   # Fine-tuned model weights
├── main.py                   # FastAPI backend logic
├── index.html                # Frontend Dashboard UI
├── YT-100K.csv               # Sample corpus for testing
└── README.md                 # Project Documentation
```

## 📜 License
Licensed under the **Apache 2.0 License**.

---
**Developed by AIpreneur** | [Hugging Face Profile](https://huggingface.co/mr-checker)
