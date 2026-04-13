# PredictGuard AI

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Production%20API-009688?logo=fastapi&logoColor=white)
![scikit--learn](https://img.shields.io/badge/scikit--learn-Machine%20Learning-F7931E?logo=scikitlearn&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Engineering-150458?logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-Numerical%20Computing-013243?logo=numpy&logoColor=white)
![License](https://img.shields.io/badge/License-Internal%20Project-lightgrey)

PredictGuard AI is an end-to-end predictive maintenance platform for industrial IoT telemetry. It trains on the AI4I 2020 dataset, serves real-time and batch predictions through FastAPI, logs every inference, and exposes a production-style dashboard for operational monitoring.

## Why this project matters

Predictive maintenance systems need more than a model. They need reliable data handling, defensible thresholds, explainable outputs, logging, and a UI that operations teams can actually use.

PredictGuard AI brings those pieces together in one workflow:

- train and evaluate a maintenance-risk model on sensor telemetry
- serve predictions through a FastAPI backend
- persist prediction history for auditability
- visualize health, risk, and model performance in a dashboard

## Highlights

- leakage-safe feature selection for inference-time realism
- engineered sensor features and threshold tuning
- single-sample and batch prediction APIs
- structured logging to CSV for traceability
- production-style dashboard with charts and live controls
- model bundle and metrics stored for repeatable deployment

## Screenshots

### Home Page

![Home Page](Output%20Images/Home%20Page.jpeg)

### Prediction Flow

![Making Prediction](Output%20Images/Making%20Prediction.jpeg)

### Latest Metrics

![Latest Metrics](Output%20Images/Latest%20Metrics.jpeg)

## Architecture

The project is organized into three main layers:

- data and model training in `src/`
- inference and logging in `backend/main.py`
- interactive monitoring in `dashboard/`

### Workflow

1. Load and normalize the AI4I CSV dataset
2. Build sensor-derived features that are safe to use at inference time
3. Split data into train, validation, and test sets
4. Train and compare candidate models
5. Tune the decision threshold
6. Save the best model bundle and metrics
7. Serve predictions through FastAPI
8. Log every request to CSV for traceability

## Features

- CSV ingestion and schema normalization
- engineered sensor features
- model comparison and threshold tuning
- saved model bundle for inference
- single prediction endpoint
- batch prediction endpoint
- prediction logging to CSV
- animated dashboard with multiple visualizations

## Dataset

The project uses the AI4I 2020 predictive maintenance dataset stored at:

`data/ai4i2020.csv`

Important note:

- `TWF`, `HDF`, `PWF`, `OSF`, and `RNF` are failure-cause flags
- these are excluded from the feature set to avoid leakage
- the model is trained only on inputs that are available at inference time

## Tech Stack

- Python
- FastAPI
- Pandas
- NumPy
- scikit-learn
- Joblib
- Chart.js
- HTML, CSS, JavaScript

## Project Structure

```text
predictguard-ai/
|-- backend/
|   `-- main.py
|-- dashboard/
|   |-- app.js
|   |-- index.html
|   `-- styles.css
|-- data/
|   `-- ai4i2020.csv
|-- logs/
|   `-- predictions_log.csv
|-- models/
|   |-- predictguard_phase1.joblib
|   `-- training_metrics.json
|-- Output Images/
|   |-- Home Page.jpeg
|   |-- Latest Metrics.jpeg
|   `-- Making Prediction.jpeg
|-- src/
|   |-- analytics.py
|   |-- config.py
|   |-- data.py
|   |-- modeling.py
|   |-- predict.py
|   `-- train.py
|-- requirements.txt
`-- README.md
```

## Quick Start

Install dependencies:

```bash
pip install -r requirements.txt
```

Train the model:

```bash
python -m src.train
```

Optional XGBoost candidate:

```bash
python -m src.train --include-xgboost
```

Start the FastAPI server:

```bash
uvicorn backend.main:app --reload
```

Open the application:

- `/`
- `/dashboard`

## API Endpoints

### Health

`GET /health`

Response:

```json
{
  "status": "healthy"
}
```

### Single Prediction

`POST /predict`

Example request:

```json
{
  "type": "M",
  "air_temperature": 298.1,
  "process_temperature": 308.6,
  "rotational_speed": 1551,
  "torque": 42.8,
  "tool_wear": 10
}
```

Example response:

```json
{
  "failure_prediction": 0,
  "risk_probability": 0.14,
  "risk_level": "LOW",
  "action": "No immediate maintenance required"
}
```

### Batch Prediction

`POST /predict/batch`

Request body:

```json
{
  "samples": [
    {
      "type": "M",
      "air_temperature": 298.1,
      "process_temperature": 308.6,
      "rotational_speed": 1551,
      "torque": 42.8,
      "tool_wear": 10
    },
    {
      "type": "H",
      "air_temperature": 310.5,
      "process_temperature": 325.0,
      "rotational_speed": 1900,
      "torque": 55.2,
      "tool_wear": 220
    }
  ]
}
```

Response:

```json
{
  "count": 2,
  "predictions": [
    {
      "failure_prediction": 0,
      "risk_probability": 0.14,
      "risk_level": "LOW",
      "action": "No immediate maintenance required"
    }
  ]
}
```

### Model Info

`GET /model-info`

Returns the selected model name, saved threshold, and validation/test metrics.

### Dashboard Data

`GET /api/dashboard-data`

Returns the structured metrics and chart payload used by the dashboard UI.

## Dashboard

The dashboard is designed to feel like a production control center.

Included sections:

- hero summary with animated risk meter
- prediction form
- recent prediction history in the browser
- dataset balance chart
- machine type distribution chart
- validation vs test metric chart
- healthy vs failure sensor profile chart
- air temperature vs torque scatter chart
- feature importance bars

The dashboard pulls data from the same FastAPI backend, so there is no separate frontend service to manage.

## Prediction Logging

Every prediction is appended to:

`logs/predictions_log.csv`

Logged fields include:

- prediction timestamp
- input sensor values
- binary prediction
- risk probability
- risk level
- action
- decision threshold
- model name

Batch prediction requests are logged one row per sample, with a shared batch id.

## Configuration

Shared paths and constants are defined in:

`src/config.py`

Notable values:

- `MODEL_BUNDLE_PATH`
- `TRAINING_METRICS_PATH`
- `PREDICTIONS_LOG_PATH`
- `DECISION_THRESHOLD`

## Notes on Thresholds

The model can have two different threshold concepts:

- the model selection threshold learned during validation
- the final operational decision threshold used by the API

The response labels are mapped from probability bands:

- `LOW` if probability is below `0.20`
- `MEDIUM` if probability is below `0.50`
- `HIGH` otherwise

## Development Tips

- use a clean virtual environment if local Python packages are mismatched
- retrain the model after changing threshold logic
- if you update the dashboard, keep the API response schema in sync
- if you want offline assets, vendor Chart.js and fonts locally

## Future Enhancements

- authentication for the API
- log table and filters in the dashboard
- offline asset bundling
- Docker support
- database-backed prediction history
- live stream ingestion for real-time IoT telemetry
