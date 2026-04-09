# AI-Powered Cybersecurity Threat Detection

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/FastAPI-API-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/scikit--learn-ML-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white" alt="scikit-learn">
</p>

<p align="center">
  A production-style machine learning system for detecting suspicious network traffic from UNSW-NB15 flow records, with a polished Streamlit dashboard, FastAPI inference service, and reusable training pipeline.
</p>

---

## Overview

This project detects malicious or suspicious network flows using a trained `ExtraTreesClassifier` pipeline built on the UNSW-NB15 dataset.

It includes:

- a clean Streamlit security dashboard
- a FastAPI prediction service
- a command-line demo for batch scoring
- reusable preprocessing, prediction, and alert generation helpers

---

## Key Features

- Threat detection on UNSW-NB15-style traffic data
- Feature engineering for flow-level security signals
- Missing-value handling and categorical encoding
- Confidence scoring with alert generation
- Streamlit UI with progress states and result summaries
- FastAPI endpoint for programmatic inference
- Model evaluation and confusion-matrix output

---

## Tech Stack

- Python
- Pandas
- NumPy
- scikit-learn
- Streamlit
- FastAPI
- Uvicorn
- Requests
- Joblib

---

## Project Structure

```text
.
|-- app.py                  # Main Streamlit dashboard
|-- dashboard/app.py        # Streamlit launcher wrapper
|-- main.py                 # Command-line scoring demo
|-- test_api.py             # Simple API client
|-- data/
|   |-- UNSW_train.csv
|   `-- UNSW_test.csv
|-- models/
|   |-- cyber_threat_model.joblib
|   `-- metrics.json
|-- artifacts/
|   `-- confusion_matrix.png
`-- src/
    |-- api.py
    |-- alerts.py
    |-- config.py
    |-- evaluate.py
    |-- model.py
    |-- predict.py
    |-- preprocess.py
    |-- train.py
    `-- visualize.py
```

---

## Dataset

The project expects the UNSW-NB15 CSV files in `data/`:

- `data/UNSW_train.csv`
- `data/UNSW_test.csv`

The model uses:

- numeric flow features
- categorical fields: `proto`, `service`, `state`
- target label: `label`
- optional attack category context: `attack_cat`

---

## Model Pipeline

The training and inference pipeline:

1. loads the raw UNSW-NB15 data
2. engineers traffic-derived features
3. imputes missing values
4. scales numeric features
5. one-hot encodes categorical columns
6. trains an `ExtraTreesClassifier`
7. predicts normal vs malicious traffic
8. generates alert metadata for suspicious rows

---

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

If you are using the bundled virtual environment:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

---

## Train The Model

```bash
python -m src.train
```

This will:

- train the model pipeline
- save the artifact to `models/cyber_threat_model.joblib`
- save metrics to `models/metrics.json`

---

## Evaluate The Model

```bash
python -m src.evaluate
```

This will:

- evaluate the saved model on `data/UNSW_test.csv`
- print classification metrics
- generate `artifacts/confusion_matrix.png`

---

## Run The Dashboard

Start the Streamlit dashboard:

```bash
streamlit run app.py
```

If you prefer the wrapper entrypoint:

```bash
streamlit run dashboard/app.py
```

What you get:

- upload and preview the CSV
- visible scanning progress while inference runs
- threat summary cards
- alert tables and confidence charts
- scored CSV download

---

## Run The API

Start the FastAPI server:

```bash
uvicorn src.api:app --reload
```

Health check:

```http
GET /health
```

Prediction endpoint:

```http
POST /predict
```

### Example Request

The API expects UNSW-NB15-style records with the same feature names used during training. For best results, send the full row schema from the dataset.

```json
{
  "records": [
    {
      "dur": 0.121478,
      "proto": "tcp",
      "service": "-",
      "state": "FIN",
      "spkts": 6,
      "dpkts": 4,
      "sbytes": 258,
      "dbytes": 172,
      "rate": 74.08749,
      "sttl": 252,
      "dttl": 254,
      "sload": 14158.94238,
      "dload": 8495.365234,
      "sloss": 0,
      "dloss": 0,
      "sinpkt": 24.2956,
      "dinpkt": 8.375,
      "sjit": 30.177547,
      "djit": 11.830604,
      "swin": 255,
      "stcpb": 621772692,
      "dtcpb": 2202533631,
      "dwin": 255,
      "tcprtt": 0.0,
      "synack": 0.0,
      "ackdat": 0.0,
      "smean": 43,
      "dmean": 43,
      "trans_depth": 0,
      "response_body_len": 0,
      "ct_srv_src": 1,
      "ct_state_ttl": 0,
      "ct_dst_ltm": 1,
      "ct_src_dport_ltm": 1,
      "ct_dst_sport_ltm": 1,
      "ct_dst_src_ltm": 1,
      "is_ftp_login": 0,
      "ct_ftp_cmd": 0,
      "ct_flw_http_mthd": 0,
      "ct_src_ltm": 1,
      "ct_srv_dst": 1,
      "is_sm_ips_ports": 0
    }
  ]
}
```

---

## Test The API

Run the local API client:

```bash
python test_api.py
```

This sends a sample payload to the server and prints the JSON response.

---

## Command-Line Demo

```bash
python main.py
```

This loads the test set, scores it, and prints a sample of the results.

---

## Outputs

After training and evaluation, the project generates:

- `models/cyber_threat_model.joblib`
- `models/metrics.json`
- `artifacts/confusion_matrix.png`

---

## Notes

- Training and inference use the same preprocessing path to keep predictions consistent.
- The model is trained on the binary `label` column.
- `attack_cat` is used only as contextual information in alerts when present.
- The dashboard is optimized for UNSW-NB15 CSV uploads and expects the same feature structure used during training.

