# Product Requirements Document (PRD): Sentinel-ML Fraud Engine

## 1. Project Overview
Sentinel-ML is an end-to-end machine learning system designed to detect fraudulent credit card transactions in near real-time. The system addresses the "Needle in a Haystack" problem (Extreme Class Imbalance) and provides stakeholders with an actionable dashboard for alert management and model explainability

## 2. Objectives
* **Near Real-Time Detection:** Process and score individual transactions in <200ms.
* **Imbalance Handling:** Achieve high Recall (capturing fraud) without catastrophic Precision loss (annoying customers).
* **Scalable Serving:** Expose a dual-purpose API for single-event streaming and bulk-upload batch processing.
* **Interpretability:** Provide "Why" for every alert to help fraud investigators.

---

## 3. Technical Stack
| Component | Technology |
| :--- | :--- |
| **Data Processing** | Pandas, Scikit-Learn (ColumnTransformers, Pipelines) |
| **ML Modeling** | XGBoost / LightGBM, Imbalanced-Learn (SMOTE/EasyEnsemble) |
| **Backend API** | FastAPI, Pydantic, Uvicorn |
| **Real-time Hook** | Python Dictionary (for feature caching/state) |
| **Frontend** | Next.js 14, Tailwind CSS, Shadcn UI |
| **Visualizations** | Recharts (PR Curves), Lucide-React (Alerts) |

---

## 4. Key Features & Requirements

### 4.1 ML Pipeline (The Engine)
* **Imbalance Strategy:** Implementation of **SMOTE-Tomek** or **Weighted Loss Functions** (Scale_pos_weight) to handle minority class representation.
* **Feature Engineering:** * Temporal: `transaction_hour`, `day_of_week`.
    * Behavioral: `amount_vs_average_city`, `transaction_frequency_1h`.
* **Evaluation Metrics:** Primary focus on **AUPRC (Area Under Precision-Recall Curve)** and **F2-Score** (prioritizing recall over precision).

### 4.2 Scoring API (FastAPI)
* **POST /score/streaming:** Accepts a single transaction JSON; returns a fraud probability and a boolean flag.
* **POST /score/batch:** Accepts a CSV/Parquet file; returns a downloadable list of predictions.
* **Explainability Endpoint:** Returns SHAP values or feature importance for a specific transaction ID.

### 4.3 Dashboard (Next.js)
* **Executive Summary:** Live counter of "Total Transactions" vs "Flagged Fraud."
* **PR Trade-off Slider:** Interactive slider to adjust the classification threshold (e.g., 0.5 to 0.7) and see real-time updates on Precision vs. Recall.
* **Alert Feed:** A "Real-time" scrolling feed of transactions flagged as fraud with high-impact features highlighted.
* **Feature Impact Map:** Bar charts showing which features (e.g., `Distance from Home`) are driving the most alerts.

---

## 5. System Architecture
1.  **Ingestion:** Simulation of transaction stream.
2.  **Validation:** FastAPI/Pydantic validates input schema.
3.  **Enrichment:** System fetches historical user context (from Python Dictionary) to calculate rolling features.
4.  **Inference:** Model Pipeline predicts probability.
5.  **Persistence:** Predictions stored in a csv file.
6.  **Visualization:** Next.js fetches data via WebSockets or Polling for the UI.

---

## 6. Success Metrics
* **Latency:** Inference response time < 150ms.
* **Recall:** > 85% of fraudulent transactions captured in the test set.
* **User Experience:** Precision > 40% (to ensure a manageable volume of false positives).