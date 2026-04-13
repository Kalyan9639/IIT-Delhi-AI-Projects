# PredictGuard AI

PredictGuard AI is a predictive maintenance platform for industrial IoT telemetry.
It trains on the AI4I 2020 dataset, serves predictions through FastAPI, logs every
prediction event, and exposes a production-style dashboard for model monitoring.

## Overview

The project is organized around three core layers:

- machine learning training on the AI4I 2020 dataset
- FastAPI inference and logging
- a browser dashboard with charts, metrics, and live prediction controls

Phase 1 focuses on offline training, model persistence, inference, logging, and a
single deployable web app.

## Features

- CSV ingestion and schema normalization
- leakage-safe feature selection
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
- they are excluded from the feature set to avoid leakage
- the model trains on the sensor inputs that are available at inference time

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

## Tech Stack

- Python
- FastAPI
- Pandas
- NumPy
- scikit-learn
- Joblib
- Chart.js
- HTML, CSS, JavaScript

## Model Workflow

1. Load and normalize the AI4I CSV
2. Build training and inference-safe features
3. Split the data into train, validation, and test sets
4. Train candidate models
5. Tune the classification threshold
6. Save the best model bundle
7. Serve predictions through FastAPI
8. Log every inference to CSV

## Training

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

Training outputs:

- model bundle: `models/predictguard_phase1.joblib`
- training metrics: `models/training_metrics.json`

## Run the Application

Start the FastAPI server:

```bash
uvicorn backend.main:app --reload
```

Open in the browser:

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

The dashboard is built to look and feel like a production control center.

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

- Use a clean virtual environment if your local Python packages are mismatched
- Retrain the model after changing threshold logic
- If you update the dashboard, keep the API response schema in sync
- If you want offline assets, vendor Chart.js and fonts locally

## Future Enhancements

- authentication for the API
- log table and filters in the dashboard
- offline asset bundling
- Docker support
- database-backed prediction history
- live stream ingestion for real-time IoT telemetry
