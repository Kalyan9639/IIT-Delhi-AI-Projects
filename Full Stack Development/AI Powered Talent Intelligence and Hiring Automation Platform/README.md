# HireForge Pro

![Status](https://img.shields.io/badge/status-active-22c55e?style=for-the-badge)
![Backend](https://img.shields.io/badge/backend-FastAPI-059669?style=for-the-badge&logo=fastapi&logoColor=white)
![Frontend](https://img.shields.io/badge/frontend-Svelte-ff3e00?style=for-the-badge&logo=svelte&logoColor=white)
![Build](https://img.shields.io/badge/build-vite%20%2B%20uvicorn-0ea5e9?style=for-the-badge&logo=vite&logoColor=white)
![Database](https://img.shields.io/badge/database-SQLite-2563eb?style=for-the-badge&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-informational?style=for-the-badge)

HireForge Pro is an AI-powered talent intelligence and hiring automation platform.
It combines recruiter job management (CRUD) with a resume screening pipeline (JD skill extraction + hybrid retrieval + NLP verification).

## What You Can Do

- Google sign-in for recruiters
- Create, edit, delete job postings (stored in SQLite)
- Dashboard shows all created jobs (title-focused list)
- Click a job to open a screening workspace:
  - Phase 1: extract must-have skills from the job description
  - Engage Verification: upload multiple resumes and get ranked results + evidence

## Tech Stack

- Backend: FastAPI, Python, SQLite
- Frontend: Svelte (Svelte 5) + Vite
- AI pipeline: resume parsing, JD skill extraction, hybrid retrieval, NLP verification

## Environment Setup

This repo does not commit `.env` files.
Use the provided `.env.example` as a template and create your own local `.env` in the project root:

```bash
cp .env.example .env
```

Required variables:

```env
CLIENT_ID=your_google_client_id_here
CLIENT_SECRET=your_google_client_secret_here
VITE_GOOGLE_CLIENT_ID=your_google_client_id_here
```

Notes:
- `CLIENT_ID` and `CLIENT_SECRET` are used by the FastAPI backend.
- `VITE_GOOGLE_CLIENT_ID` is used by the frontend.
- Never hardcode credentials in source code.

## Run Locally

### 1. Backend (FastAPI)

From the project root:

```bash
uv pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend URLs:
- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

### 2. Frontend (Svelte + Vite)

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:
- `http://localhost:5173`

## Database

Local SQLite file:

```text
hireforge_users.db
```

It is created automatically on backend startup.

## API Overview

Auth:
- `POST /auth/google/verify`
- `GET /auth/me`

Jobs:
- `POST /jobs/`
- `GET /jobs/`
- `GET /jobs/{job_id}`
- `PUT /jobs/{job_id}`
- `DELETE /jobs/{job_id}`

Screening pipeline:
- `POST /extract-skills`
- `POST /process-single`
- `POST /process-multiple`

## Project Structure

```text
main.py              # FastAPI app entry point
auth.py              # Google auth endpoints
database.py          # SQLite helpers and tables
routes/jobs.py       # Job CRUD routes
backend_web.html     # Reference UI used to validate pipeline behavior
frontend/            # Svelte app
resume_parsing.py    # Resume parsing and retrieval
jd_skill_extraction.py
nlp_logic.py
models.py
```

## Troubleshooting

- Login shows “Failed to fetch”:
  - Ensure backend is running on `http://localhost:8000`.
  - Check CORS and that the Vite dev server is running on `http://localhost:5173`.
- Screening returns empty skills:
  - Try a more detailed job description.
  - Check backend logs for any model/Ollama errors.
