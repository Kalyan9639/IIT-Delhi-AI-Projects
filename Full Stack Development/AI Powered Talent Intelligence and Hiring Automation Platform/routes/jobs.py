"""
Job management endpoints for HireForge Pro.
Provides CRUD operations for job postings.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging
import os

from database import (
    create_job, create_candidate, get_job_by_id, get_jobs_by_user, update_job, delete_job,
    get_candidates_by_job, get_candidates_by_user, get_candidate_by_id, update_candidate_status,
    get_candidate_status
)
from auth import get_authenticated_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["Jobs"])

# ============= Request Models =============


class CreateJobRequest(BaseModel):
    title: str
    description: str
    company_name: str
    location: Optional[str] = None
    job_type: Optional[str] = None
    salary_range: Optional[str] = None


class UpdateJobRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    salary_range: Optional[str] = None


class CreateCandidateRequest(BaseModel):
    full_name: str
    email: str
    phone: Optional[str] = None
    resume_filename: Optional[str] = None
    resume_text: Optional[str] = None


class JobResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: str
    company_name: str
    location: Optional[str] = None
    job_type: Optional[str] = None
    salary_range: Optional[str] = None
    created_at: str
    updated_at: str
    candidate_count: int = 0


class JobDetailResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: str
    company_name: str
    location: Optional[str] = None
    job_type: Optional[str] = None
    salary_range: Optional[str] = None
    created_at: str
    updated_at: str
    candidates: List[dict] = []


class CandidateResponse(BaseModel):
    id: int
    user_id: int
    job_id: int
    full_name: str
    email: str
    phone: Optional[str] = None
    resume_filename: Optional[str] = None
    resume_text: Optional[str] = None
    current_status: Optional[str] = None
    status_notes: Optional[str] = None
    job_title: Optional[str] = None
    created_at: str


# ============= Helper Functions =============


# ============= Job Endpoints =============


@router.post("/", response_model=JobResponse)
async def create_new_job(request: Request, job: CreateJobRequest, current_user: dict = Depends(get_authenticated_user)):
    """
    Create a new job posting.
    Requires authentication (user must be logged in via Google).
    """
    user_id = current_user["id"]
    job_id = create_job(
        user_id=user_id,
        title=job.title,
        description=job.description,
        company_name=job.company_name,
        location=job.location,
        job_type=job.job_type,
        salary_range=job.salary_range
    )
    return get_job_by_id(job_id)


@router.get("/", response_model=List[JobResponse])
async def get_user_jobs(request: Request, current_user: dict = Depends(get_authenticated_user)):
    """
    Get all jobs created by the current user.
    """
    user_id = current_user["id"]
    jobs = get_jobs_by_user(user_id)

    # Get candidate counts
    result = []
    for job in jobs:
        result.append({
            **job,
            "candidate_count": len(get_candidates_by_job(user_id, job["id"]))
        })
    return result


@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job_details(request: Request, job_id: int, current_user: dict = Depends(get_authenticated_user)):
    """
    Get detailed job information including candidates.
    """
    user_id = current_user["id"]
    job = get_job_by_id(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get candidates for this job
    candidates = get_candidates_by_job(user_id, job_id)
    return {
        **job,
        "candidates": candidates
    }


@router.put("/{job_id}", response_model=JobResponse)
async def update_existing_job(request: Request, job_id: int, job: UpdateJobRequest, current_user: dict = Depends(get_authenticated_user)):
    """
    Update an existing job posting.
    Only the job owner can update.
    """
    user_id = current_user["id"]
    existing_job = get_job_by_id(job_id)

    if not existing_job:
        raise HTTPException(status_code=404, detail="Job not found")

    if existing_job["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    update_data = job.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    success = update_job(job_id, **update_data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update job")

    return get_job_by_id(job_id)


@router.delete("/{job_id}")
async def delete_existing_job(request: Request, job_id: int, current_user: dict = Depends(get_authenticated_user)):
    """
    Delete a job posting and all associated candidates.
    Only the job owner can delete.
    """
    user_id = current_user["id"]
    job = get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    deleted = delete_job(job_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete job")

    return {"message": "Job deleted successfully"}


@router.get("/candidates", response_model=List[CandidateResponse])
async def get_all_user_candidates(request: Request, current_user: dict = Depends(get_authenticated_user)):
    """
    Get all candidates across all jobs created by the current user.
    """
    user_id = current_user["id"]
    return get_candidates_by_user(user_id)


@router.post("/{job_id}/candidates", response_model=CandidateResponse)
async def create_candidate_for_job(
    request: Request,
    job_id: int,
    candidate: CreateCandidateRequest,
    current_user: dict = Depends(get_authenticated_user)
):
    """
    Add a candidate to a job posting.
    """
    user_id = current_user["id"]
    job = get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    candidate_id = create_candidate(
        user_id=user_id,
        job_id=job_id,
        full_name=candidate.full_name,
        email=candidate.email,
        phone=candidate.phone,
        resume_filename=candidate.resume_filename,
        resume_text=candidate.resume_text
    )

    created_candidate = get_candidate_by_id(candidate_id)
    if not created_candidate:
        raise HTTPException(status_code=500, detail="Failed to create candidate")

    status = get_candidate_status(candidate_id) or {}
    return {
        **created_candidate,
        "current_status": status.get("status"),
        "status_notes": status.get("notes")
    }


# ============= Candidate Status Endpoints =============


@router.post("/{job_id}/candidates/{candidate_id}/status")
async def update_candidate_status_endpoint(
    request: Request,
    job_id: int,
    candidate_id: int,
    status_update: dict
):
    """
    Update candidate status (e.g., 'screened', 'interviewing', 'offered', 'hired', 'rejected').
    """
    current_user = get_authenticated_user(request)
    user_id = current_user["id"]

    # Verify job ownership
    job = get_job_by_id(job_id)
    if not job or job["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Job not found or access denied")

    # Verify candidate belongs to job
    candidate = get_candidate_by_id(candidate_id)
    if not candidate or candidate["job_id"] != job_id:
        raise HTTPException(status_code=404, detail="Candidate not found")

    status = status_update.get("status", "new")
    notes = status_update.get("notes", "")

    update_candidate_status(candidate_id, status, notes)

    return {"message": f"Candidate status updated to '{status}'"}
