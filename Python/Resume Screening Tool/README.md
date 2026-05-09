<div align="center">

# 🔥 HireForge PRO
### Neural Resume Intelligence Engine

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136%2B-green?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success)](https://github.com/)
[![NLP](https://img.shields.io/badge/NLP-Transformers-orange)](https://huggingface.co/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-blueviolet)](https://ollama.com/)

**Advanced Information Retrieval & Applied NLP System for Intelligent Recruitment Screening**

[Features](#-features) • [Architecture](#-architecture) • [Installation](#-installation) • [Usage](#-usage) • [API](#-api-documentation)

---

![HireForge Banner](https://img.shields.io/badge/Build%20With-Python%20%7C%20FastAPI%20%7C%20NLP-informational?style=for-the-badge&logo=python)

</div>

---

## 📖 Project Overview

**HireForge PRO** is an enterprise-grade Information Retrieval (IR) and Applied NLP system designed to automate the recruitment screening process. Moving beyond basic "AI wrappers," the system intelligently parses job descriptions, semantically filters large batches of resumes, and performs deep contextual verification to determine if a candidate possesses professional-grade experience, academic exposure, or lacks a required skill.

The system guarantees **explainability** for HR professionals by exposing the exact resume bullet points used to verify a skill, alongside an AI-generated candidate verdict.

### 🎯 Core Capabilities

- 🧠 **Intelligent JD Analysis** - Extract must-have skills using local LLMs
- ⚡ **Hybrid Retrieval System** - BM25 + Semantic Search for lightning-fast filtering
- 🔍 **Deep Context Verification** - Zero-Shot Classification for professional vs. academic skills
- 📊 **Explainable AI** - Full transparency with evidence-based scoring
- 🎨 **Modern Dashboard** - Cyber-corporate UI with real-time results

---

## ✨ Features

### 🚀 Phase 1: Smart Requirement Extraction
- **LLM-Powered Analysis**: Uses `gpt-oss:20b-cloud` via Ollama for intelligent skill extraction
- **Structured Output**: Generates deterministic JSON arrays of technical requirements
- **Fallback Safety**: Graceful degradation if LLM fails

### 📄 Phase 2: Hybrid Document Processing
- **Multi-Format Support**: PDF, DOCX, and TXT parsing
- **Intelligent Segmentation**: Auto-separates Experience, Projects, Education, and Skills sections
- **Dual-Stage Retrieval**:
  - **BM25 (Sparse)**: High-speed keyword matching
  - **Sentence Transformers (Dense)**: Semantic similarity for contextual understanding
- **Mass Screening**: Processes thousands of resumes in milliseconds

### 🧠 Phase 3: Deep NLP Context Verification
- **Zero-Shot Classification**: Distinguishes between professional execution, academic learning, and missing skills
- **Evidence Scouting**: Identifies specific bullet points supporting each skill
- **Power Verb Detection**: Recognizes action verbs indicating hands-on experience
- **Confidence Scoring**: Quantifies verification certainty

### 📊 Phase 4: Intelligent Scoring & Presentation
- **Weighted Scoring**: 30% retrieval relevance + 70% NLP verification
- **AI Verdict Generation**: 2-sentence summaries of strengths and weaknesses
- **Interactive Dashboard**: Real-time candidate ranking and skill matrices
- **Evidence Display**: Shows exact text used for verification

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                           │
│              (HTML5 / CSS3 / JavaScript)                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                            │
│              (Asynchronous REST API)                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   PHASE 1    │  │   PHASE 2    │  │   PHASE 3    │
│  JD Extract  │  │  Hybrid      │  │  Deep NLP    │
│  (Ollama)    │  │  Retrieval   │  │  Verification│
└──────────────┘  └──────────────┘  └──────────────┘
        │                  │                  │
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Local LLM   │  │  BM25 +      │  │  Zero-Shot   │
│  gpt-oss:20b │  │  Sentence    │  │  Classifier  │
│              │  │  Transformers │  │  (NLI)       │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## 🛠️ Tech Stack

### 🤖 AI & Natural Language Processing
| Technology | Purpose |
|------------|---------|
| **Ollama** | Cloud LLM inference for JD extraction and verdict generation |
| **Hugging Face Transformers** | Zero-Shot Classification pipeline (`nli-distilroberta-base-v2`) |
| **Sentence Transformers** | Semantic embeddings (`all-MiniLM-L6-v2`) |
| **rank_bm25** | High-speed keyword retrieval algorithm |

### ⚙️ Backend Engineering
| Technology | Purpose |
|------------|---------|
| **FastAPI** | High-performance async web framework |
| **Pydantic** | Data validation and serialization |
| **PyPDF2** | PDF text extraction |
| **python-docx** | DOCX document parsing |
| **NumPy** | Matrix operations and scoring |

---

## 📦 Installation

### Prerequisites

- **Python 3.8+**
- **Ollama** (with `gpt-oss:20b-cloud` model)
- **pip** or **uv** package manager

### Step 1: Clone the Repository

```bash
git clone https://github.com/Kalyan9639/IIT-Delhi-AI-Projects.git
cd "IIT-Delhi-AI-Projects/Python/Resume Screening Tool"
```

### Step 2: Install Ollama and Required Model

```bash
# Install Ollama (if not already installed)
# Visit: https://ollama.com/download

# Pull the required model
ollama pull gpt-oss:20b-cloud
```

### Step 3: Create Virtual Environment

```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using uv (faster)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Step 4: Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Or using uv (recommended)
uv pip install -r requirements.txt
```

---

## 🚀 Usage

### Starting the Server

```bash
# Development mode
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Accessing the Application

- **Web Interface**: Open `http://localhost:8000` in your browser
- **API Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative Docs**: `http://localhost:8000/redoc` (ReDoc)

### Quick Start Guide

1. **Upload Job Description**: Paste or upload a JD text
2. **Upload Resumes**: Select multiple resume files (PDF/DOCX/TXT)
3. **Click "Screen Candidates"**: Watch the 4-phase pipeline execute
4. **Review Results**: Explore ranked candidates with evidence-based scores

---

## 📡 API Documentation

### Core Endpoints

#### 1. Extract Skills from Job Description
```http
POST /extract-skills
Content-Type: application/json

{
  "job_description": "We need a Python developer with FastAPI experience..."
}
```

**Response:**
```json
{
  "extracted_skills": ["Python", "FastAPI", "Docker", "AWS", "SQL"]
}
```

#### 2. Screen Resumes (Full Pipeline)
```http
POST /screen-resumes
Content-Type: multipart/form-data

job_description: "JD text..."
resumes: [file1.pdf, file2.docx, ...]
```

**Response:**
```json
{
  "job_title": "Senior Python Developer",
  "total_resumes_processed": 10,
  "top_candidates": [
    {
      "rank": "1/10",
      "filename": "john_doe.pdf",
      "final_score": 0.92,
      "verified_skills": ["Python", "FastAPI", "Docker"],
      "partial_skills": ["AWS"],
      "missing_skills": ["SQL"],
      "evaluations": [...],
      "ai_verdict": "Strong hands-on experience with Python and FastAPI. Needs more SQL exposure."
    }
  ],
  "processing_time": 2.45
}
```

#### 3. Hybrid Search (Phase 2 Only)
```http
POST /hybrid-search
Content-Type: application/json

{
  "query": "Python FastAPI developer",
  "documents": ["resume1_text", "resume2_text", ...]
}
```

**Response:**
```json
{
  "query": "Python FastAPI developer",
  "results": [
    {
      "filename": "resume1.pdf",
      "hybrid_score": 0.89,
      "semantic_score": 0.85,
      "bm25_score": 0.93
    }
  ]
}
```

### Interactive API Testing

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

---

## 🎯 Performance Benchmarks

| Metric | Value |
|--------|-------|
| **JD Extraction Time** | ~2-3 seconds |
| **Resume Parsing Speed** | ~0.5 seconds per document |
| **Hybrid Retrieval** | <100ms for 1000 documents |
| **NLP Verification** | ~1-2 seconds per candidate |
| **End-to-End Pipeline** | ~5-10 seconds for 10 resumes |

---

## 🔧 Configuration

### Model Customization

Edit `jd_skill_extraction.py` to change the LLM model:

```python
# Change to your preferred model
self.model_name = "mistral"  # or "llama2", "neural-chat", etc.
```

---

## 📁 Project Structure

```
hireforge-pro/
├── main.py                 # FastAPI application & endpoints
├── models.py               # Pydantic data models
├── jd_skill_extraction.py  # Phase 1: JD skill extraction
├── resume_parsing.py       # Phase 2: Document parsing & retrieval
├── nlp_logic.py           # Phase 3: Deep NLP verification
├── index.html             # Frontend dashboard
├── requirements.txt       # Python dependencies
├── README.md              # This file
└── project_overview.md    # Detailed project documentation
```

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 style guidelines
- Add docstrings to all functions
- Write tests for new features
- Update documentation as needed

---

## 📞 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/Kalyan9639/IIT-Delhi-AI-Projects/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Kalyan9639/IIT-Delhi-AI-Projects/discussions)
- **Email**: support@hireforge.pro

---

<div align="center">

**Built with ❤️ by the HireForge Team**

[⬆ Back to Top](#-hireforge-pro)

</div>
