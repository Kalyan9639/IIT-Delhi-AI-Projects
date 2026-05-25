from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
from typing import List, Optional
import logging
from datetime import datetime
import asyncio
import os

from models import RankingResult, RankedResume, SkillEvaluation, ExtractionResponse, HybridSearchResponse, HybridSearchResult
from jd_skill_extraction import JDExtractor
from resume_parsing import ResumeParser, HybridRetriever
from nlp_logic import NLPEngine
from database import init_database

# Initialize routes
from auth import router as auth_router
from routes.jobs import router as jobs_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HireForge Pro - AI Powered Talent Intelligence")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_database()
    logger.info("Database initialized successfully")


# Initialize components
jd_extractor = JDExtractor()
retriever = HybridRetriever()
parser = ResumeParser()
nlp_engine = NLPEngine()

# ==========================================
# HELPER: Generate AI Verdict using Ollama
# ==========================================
def generate_ai_verdict(job_description: str, verified_skills: List[str], partial_skills: List[str],
                       missing_skills: List[str], all_skills: List[str]) -> str:
    """
    Generate a 2-sentence AI verdict about candidate strengths and weaknesses using Ollama.
    """
    total_skills = len(all_skills)
    matched_skills = len(verified_skills)

    prompt = f"""Based on this job description and skill matching results, provide a brief 2-sentence AI verdict about the candidate's strengths and weaknesses.

Job Description: {job_description[:200]}

Candidate Profile:
- Verified Professional Skills ({matched_skills}): {', '.join(verified_skills) if verified_skills else 'None'}
- Partial/Academic Skills: {', '.join(partial_skills) if partial_skills else 'None'}
- Missing Skills: {', '.join(missing_skills[:3]) if missing_skills else 'None'}

Write exactly 2 sentences. First sentence: Highlight the candidate's strengths (like, unique projects relevant to jd or experience (it can be internship or hackathon)). Second sentence: what he lacks.
Keep it professional and concise (max 15 words per sentence)."""

    try:
        response = jd_extractor.client.generate(
            model=jd_extractor.model_name,
            prompt=prompt,
            stream=False
        )
        verdict = response.get("response", "").strip()
        sentences = verdict.split('.')[:2]
        verdict = '. '.join([s.strip() for s in sentences if s.strip()]) + '.'
        return verdict if verdict != '.' else "Strong technical foundation with room for growth in specialized areas."
    except Exception as e:
        logger.error(f"AI Verdict generation failed: {e}")
        strength = "well-matched technical skills" if matched_skills >= total_skills * 0.7 else "foundation in relevant technologies"
        weakness = "missing advanced certifications" if missing_skills else "opportunity to strengthen edge skills"
        return f"Candidate demonstrates {strength}. {weakness}."


# ==========================================
# AUTHENTICATION ROUTES
# ==========================================
app.include_router(auth_router)


# ==========================================
# JOB MANAGEMENT ROUTES
# ==========================================
app.include_router(jobs_router)


# ==========================================
# BACKEND AI ROUTES (Original Resume Screening)
# ==========================================

@app.get("/")
async def root():
    """Root endpoint - redirect to frontend or docs."""
    return {
        "service": "HireForge Pro API",
        "version": "2.0.0",
        "frontend_available": True,
        "endpoints": {
            "auth": "/auth/google/verify",
            "jobs": "/jobs/",
            "screen_resumes": "/process-multiple",
            "docs": "/docs"
        }
    }


@app.get("/docs")
async def get_docs():
    """Redirect to FastAPI docs."""
    return RedirectResponse(url="/docs")


@app.post("/extract-skills", response_model=ExtractionResponse)
async def extract_skills(job_description: str = Form(...)):
    skills = await asyncio.to_thread(jd_extractor.extract_must_have_skills, job_description)
    return ExtractionResponse(extracted_skills=skills)


@app.post("/hybrid-search", response_model=HybridSearchResponse)
async def hybrid_search(query: str = Form(...), files: List[UploadFile] = File(...)):
    documents = []
    filenames = []

    for file in files:
        content = await file.read()
        text = parser.extract_text(content, file.filename)
        if text:
            sections = parser.segment_into_sections(text)
            hybrid_text = parser.get_hybrid_search_text(sections)
            documents.append(hybrid_text)
            filenames.append(file.filename)

    if not documents:
        raise HTTPException(status_code=400, detail="Could not extract text from files.")

    results = retriever.compute_hybrid_score(query, documents, top_k=len(documents))

    formatted_results = [
        HybridSearchResult(
            filename=filenames[r['index']],
            hybrid_score=round(r['score'], 4),
            semantic_score=round(r['semantic_score'], 4),
            bm25_score=round(r['bm25_score'], 4)
        ) for r in results
    ]
    return HybridSearchResponse(query=query, results=formatted_results)


@app.post("/process-single", response_model=RankingResult)
async def process_single(job_description: str = Form(...), file: UploadFile = File(...)):
    start_time = datetime.now()

    must_have_skills = await asyncio.to_thread(jd_extractor.extract_must_have_skills, job_description)

    content = await file.read()
    text = parser.extract_text(content, file.filename)
    sections = parser.segment_into_sections(text)
    professional_text = (
        sections.get('experience', '') + "\n" +
        sections.get('projects', '') + "\n" +
        sections.get('skills', '')
    )

    evaluations = []
    score_tally = 0.0
    for skill in must_have_skills:
        status, conf, evidence = nlp_engine.evaluate_skill_context(professional_text, skill, "experience")
        evaluations.append(SkillEvaluation(skill=skill, status=status, confidence_score=round(conf, 2), evidence_chunk=evidence[:150]))
        if status == "Verified Professional": score_tally += 1.0
        elif status == "Academic/Partial": score_tally += 0.5

    final_score = (score_tally / len(must_have_skills)) * 100 if must_have_skills else 0

    verified_skills = [e.skill for e in evaluations if e.status == "Verified Professional"]
    partial_skills = [e.skill for e in evaluations if e.status == "Academic/Partial"]
    missing_skills = [e.skill for e in evaluations if e.status == "Missing"]

    ai_verdict = await asyncio.to_thread(
        generate_ai_verdict,
        job_description, verified_skills, partial_skills, missing_skills, must_have_skills
    )

    rank_display = f"{len(verified_skills)}/{len(must_have_skills)}"

    candidate = RankedResume(
        rank=rank_display,
        filename=file.filename,
        final_score=round(final_score, 2),
        verified_skills=verified_skills,
        partial_skills=partial_skills,
        missing_skills=missing_skills,
        evaluations=evaluations,
        ai_verdict=ai_verdict
    )

    return RankingResult(
        job_title="Single Verification", total_resumes_processed=1,
        top_candidates=[candidate], processing_time=round((datetime.now() - start_time).total_seconds(), 2)
    )


@app.post("/process-multiple", response_model=RankingResult)
async def process_multiple(job_description: str = Form(...), files: List[UploadFile] = File(...)):
    start_time = datetime.now()

    must_have_skills = await asyncio.to_thread(jd_extractor.extract_must_have_skills, job_description)
    query_string = f"{job_description} {' '.join(must_have_skills)}"
    logger.info(f"Phase 1 (Skill Extraction): Extracted {len(must_have_skills)} skills: {must_have_skills}")

    all_resumes = []
    for file in files:
        content = await file.read()
        text = parser.extract_text(content, file.filename)
        if text:
            sections = parser.segment_into_sections(text)
            hybrid_text = parser.get_hybrid_search_text(sections)
            all_resumes.append({
                "filename": file.filename,
                "sections": sections,
                "hybrid_text": hybrid_text
            })

    if not all_resumes:
        raise HTTPException(status_code=400, detail="No readable text found in documents.")

    logger.info(f"Starting resume screening for {len(all_resumes)} candidates...")

    corpus_texts = [r['hybrid_text'] for r in all_resumes]
    top_picks = retriever.compute_hybrid_score(
        query_string,
        corpus_texts,
        top_k=min(10, len(all_resumes)),
        bm25_top_k=min(max(3 * 10, 15), len(all_resumes)),
        alpha=0.4
    )

    logger.info(f"Phase 2 (Hybrid Search): Filtered {len(all_resumes)} resumes to {len(top_picks)} candidates")

    final_ranked_list = []
    for pick in top_picks:
        resume_data = all_resumes[pick['index']]
        sections = resume_data['sections']

        professional_text = sections.get('experience', '') + "\n" + sections.get('projects', '') + "\n" + sections.get('skills', '')

        evaluations = []
        score_tally = 0.0

        for skill in must_have_skills:
            status, conf, evidence = nlp_engine.evaluate_skill_context(professional_text, skill, "experience")
            evaluations.append(SkillEvaluation(
                skill=skill, status=status, confidence_score=round(conf, 2), evidence_chunk=evidence[:150]
            ))

            if status == "Verified Professional": score_tally += 1.0
            elif status == "Academic/Partial": score_tally += 0.5

        if len(must_have_skills) > 0:
            verification_score = (score_tally / len(must_have_skills)) * 100
        else:
            verification_score = 0.0
            logger.warning("No skills found in must_have_skills list; skipping verification score.")

        hybrid_search_contribution = pick['score'] * 100
        final_score = max(0, (0.3 * hybrid_search_contribution) + (0.7 * verification_score))

        verified_skills = [e.skill for e in evaluations if e.status == "Verified Professional"]
        partial_skills = [e.skill for e in evaluations if e.status == "Academic/Partial"]
        missing_skills = [e.skill for e in evaluations if e.status == "Missing"]

        ai_verdict = await asyncio.to_thread(
            generate_ai_verdict,
            job_description, verified_skills, partial_skills, missing_skills, must_have_skills
        )

        final_ranked_list.append(RankedResume(
            rank=f"0/{len(must_have_skills)}",
            filename=resume_data['filename'],
            final_score=round(final_score, 2),
            verified_skills=verified_skills,
            partial_skills=partial_skills,
            missing_skills=missing_skills,
            evaluations=evaluations,
            ai_verdict=ai_verdict
        ))

    final_ranked_list.sort(key=lambda x: x.final_score, reverse=True)
    for i, candidate in enumerate(final_ranked_list):
        num_verified = len(candidate.verified_skills)
        total_skills = len(must_have_skills)
        candidate.rank = f"{num_verified}/{total_skills}"

    logger.info(f"Phase 3 (NLP Verification): Completed evaluation of {len(top_picks)} candidates")

    return RankingResult(
        job_title="Processed Screening", total_resumes_processed=len(all_resumes),
        top_candidates=final_ranked_list, processing_time=round((datetime.now() - start_time).total_seconds(), 2)
    )
