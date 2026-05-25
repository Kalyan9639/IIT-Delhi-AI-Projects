# HireForge Pro

[![Production Ready](https://img.shields.io/badge/ready-for%20production-22c55e?style=for-the-badge)](https://github.com/Kalyan9639/IIT-Delhi-AI-Projects/tree/main/Full%20Stack%20Development/AI%20Powered%20Talent%20Intelligence%20and%20Hiring%20Automation%20Platform)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-059669?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Svelte](https://img.shields.io/badge/Svelte-Frontend-ff3e00?style=for-the-badge&logo=svelte&logoColor=white)](https://svelte.dev/)
[![Vite](https://img.shields.io/badge/Vite-Dev%20Server-646cff?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-2563eb?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

AI-powered talent intelligence and hiring automation platform built with FastAPI + Svelte.
This system is intended for recruiters and hiring teams.

## Overview

HireForge Pro helps recruiters create jobs, upload resumes, and run a multi-phase screening pipeline:

- `Phase 1`: Neural skill extraction from job description
- `Phase 2`: Resume processing and ranking
- `Phase 3`: AI verification verdicts backed by backend logic

The app includes recruiter authentication, job CRUD, a dashboard of created jobs, and a per-job screening workspace.

## Core Features

- Google sign-in for recruiter access
- Job management with full CRUD
- Dashboard listing all created jobs
- Click any job to open its screening workspace
- Resume upload (multi-file) per job
- Skill extraction + candidate ranking + AI verdict pipeline
- SQLite persistence for users, jobs, and workflow records

## Tech Stack

- Backend: `FastAPI`, `Python`, `SQLite`
- Frontend: `Svelte` (Vite)
- AI pipeline: custom modules for JD skill extraction, resume parsing, NLP verification

## Monorepo Structure

```text
.
|-- main.py
|-- auth.py
|-- database.py
|-- models.py
|-- routes/
|   `-- jobs.py
|-- jd_skill_extraction.py
|-- resume_parsing.py
|-- nlp_logic.py
|-- backend_web.html
|-- frontend/
|   |-- src/
|   |-- public/
|   |-- package.json
|   `-- vite.config.js
|-- requirements.txt
|-- .env.example
`-- README.md
```

## Install From GitHub

### 1. Clone the repository

```bash
git clone https://github.com/Kalyan9639/IIT-Delhi-AI-Projects.git
cd "IIT-Delhi-AI-Projects/Full Stack Development/AI Powered Talent Intelligence and Hiring Automation Platform"
```

### 2. Create your environment file

Use the template already included in the repo:

```bash
cp .env.example .env
```

Edit `.env` and add your Google OAuth credentials:

```env
CLIENT_ID=your_google_client_id
CLIENT_SECRET=your_google_client_secret
VITE_GOOGLE_CLIENT_ID=your_google_client_id
```

### 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 4. Install frontend dependencies

```bash
cd frontend
npm install
```

## Local Setup

### 1. Prerequisites

- Python `3.10+`
- Node.js `18+`
- npm `9+`

### 2. Run Backend

From project root:

```bash
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend URLs:

- API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

### 3. Run Frontend

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

- `http://localhost:5173`

## API Surface

Auth:

- `POST /auth/google/verify`
- `GET /auth/me`

Jobs:

- `POST /jobs/`
- `GET /jobs/`
- `GET /jobs/{job_id}`
- `PUT /jobs/{job_id}`
- `DELETE /jobs/{job_id}`

Screening:

- `POST /extract-skills`
- `POST /process-single`
- `POST /process-multiple`

## Deployment Notes

- Build frontend with `cd frontend && npm run build`
- Serve `frontend/dist` behind Nginx, a CDN, or another static host
- Deploy FastAPI with Uvicorn or Gunicorn in production
- Keep the backend and frontend environment variables configured for your deployment target

## Troubleshooting

- `Failed to fetch` on sign-in:
  - Ensure backend is running at `http://localhost:8000`
  - Ensure frontend is running at `http://localhost:5173`
  - Check browser console and backend logs for CORS or network errors

- Empty extracted skills:
  - Verify the job description contains enough detail
  - Check backend pipeline logs for parser or model errors

- Resume uploaded but ranking missing:
  - Confirm `Phase 1` completed before engaging verification
  - Verify upload endpoint and `process-multiple` response payload
