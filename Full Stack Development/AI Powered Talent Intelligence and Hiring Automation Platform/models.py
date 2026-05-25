from pydantic import BaseModel
from typing import List, Dict, Optional

class SkillEvaluation(BaseModel):
    skill: str
    status: str  # "Verified Professional", "Academic/Partial", or "Missing"
    confidence_score: float
    evidence_chunk: str

class RankedResume(BaseModel):
    rank: str  # Changed to string to support "x/y" format (e.g., "5/10")
    filename: str
    final_score: float
    verified_skills: List[str]
    partial_skills: List[str]
    missing_skills: List[str]
    evaluations: List[SkillEvaluation]
    ai_verdict: str  # 2-sentence AI verdict about strengths and weaknesses

class RankingResult(BaseModel):
    job_title: str
    total_resumes_processed: int
    top_candidates: List[RankedResume]
    processing_time: float

# --- New Models for Modular Endpoints ---
class ExtractionResponse(BaseModel):
    extracted_skills: List[str]

class HybridSearchResult(BaseModel):
    filename: str
    hybrid_score: float
    semantic_score: float
    bm25_score: float

class HybridSearchResponse(BaseModel):
    query: str
    results: List[HybridSearchResult]