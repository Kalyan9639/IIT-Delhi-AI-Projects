# AI-Powered Cybersecurity Threat Detection

This project builds a machine learning system for detecting cyber threats from network flow data using the UNSW-NB15 Kaggle dataset.

## Project Goal

Detect suspicious activity such as malicious traffic, attacks, and unauthorized access using a trained ML pipeline and expose predictions through:

- a command-line script
- a FastAPI service
- a Streamlit dashboard

## Dataset

The project uses the UNSW-NB15 datasets placed in:

- `data/UNSW_train.csv`
- `data/UNSW_test.csv`

These files should contain the standard UNSW-NB15 columns, including:

- numeric traffic-flow features
- categorical fields like `proto`, `service`, and `state`
- target column `label`
- attack category column `attack_cat`

## What The Model Does

The model pipeline:

- loads the raw dataset
- engineers useful traffic features
- imputes missing values
- scales numeric features
- one-hot encodes categorical features
- trains an `ExtraTreesClassifier`
- predicts whether a row is normal or malicious
- generates alert metadata for suspicious traffic

## Project Structure

- `main.py` - command-line entry point for scoring the test set
- `src/config.py` - central paths and column definitions
- `src/preprocess.py` - loading, cleaning, and feature engineering
- `src/model.py` - model pipeline definition
- `src/train.py` - training script
- `src/evaluate.py` - evaluation script
- `src/predict.py` - reusable prediction helpers
- `src/alerts.py` - threat alert generation
- `src/visualize.py` - confusion matrix plotting
- `src/api.py` - FastAPI application
- `dashboard/app.py` - Streamlit app
- `test_api.py` - API test client using Requests

## Setup

Install the dependencies:

```bash
pip install -r requirements.txt
```

If you are using the bundled virtual environment, activate it first and then install:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

## Train The Model

Run:

```bash
python -m src.train
```

This will:

- train the ML pipeline
- save the model to `models/cyber_threat_model.joblib`
- save metrics to `models/metrics.json`

## Evaluate The Model

Run:

```bash
python -m src.evaluate
```

This will:

- evaluate the saved model on `data/UNSW_test.csv`
- print classification metrics
- save a confusion matrix image to `artifacts/confusion_matrix.png`

## Run The Command-Line Demo

Run:

```bash
python main.py
```

This loads the test set, scores it, and prints sample alerts.

## Run The API

Start the FastAPI server:

```bash
uvicorn src.api:app --reload
```

Health check:

```bash
GET /health
```

Prediction endpoint:

```bash
POST /predict
```

Example request body:

```json
{
  "records": [
    {
      "dur": 0.121478,
      "proto": "tcp",
      "service": "-",
      "state": "FIN"
    }
  ]
}
```

The API expects UNSW-NB15-style records with the same feature names as the dataset.

## Test The API

Run:

```bash
python test_api.py
```

This script sends a small sample payload to the API and prints the JSON response.

## Run The Dashboard

Launch the Streamlit app:

```bash
streamlit run dashboard/app.py
```

The dashboard lets you upload a CSV file and view predictions, threat scores, and generated alerts.

## Current Artifacts

After training and evaluation, the project generates:

- `models/cyber_threat_model.joblib`
- `models/metrics.json`
- `artifacts/confusion_matrix.png`

## Notes

- The repository now uses a single preprocessing and prediction path so training and inference stay aligned.
- The model is based on the binary `label` column, while `attack_cat` is used for context in alerts when available.
- The API and dashboard expect the same UNSW-NB15 column structure used during training.

