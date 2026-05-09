import re
import io
import logging
import numpy as np
import PyPDF2
import docx
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, util
from typing import List, Dict

logger = logging.getLogger(__name__)

class ResumeParser:
    def __init__(self):
        self.section_patterns = {
            'experience': r'\b(experience|employment|work history|professional background)\b',
            'projects': r'\b(projects|portfolio|open source)\b',
            'education': r'\b(education|academics|qualifications)\b',
            'skills': r'\b(skills|technologies|tools|core competencies)\b'
        }

    def clean_text(self, text: str) -> str:
        # Preserve line breaks and bullet structure while normalizing horizontal whitespace.
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        text = re.sub(r'[ \t\f\v]+', ' ', text)
        text = re.sub(r'[ \t]+\n', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Keep common bullet markers so downstream NLP can split on them.
        text = re.sub(r'[^\w\s\.,\-\+#@/\n••\*]', ' ', text)
        return re.sub(r'[ \t]+', ' ', text).strip()

    def extract_text(self, content: bytes, filename: str) -> str:
        ext = filename.split('.')[-1].lower()
        text = ""
        try:
            if ext == 'pdf':
                reader = PyPDF2.PdfReader(io.BytesIO(content))
                text = "\n".join([page.extract_text() or "" for page in reader.pages])
            elif ext == 'docx':
                doc = docx.Document(io.BytesIO(content))
                text = "\n".join([para.text for para in doc.paragraphs])
            elif ext == 'txt':
                text = content.decode('utf-8', errors='ignore')
            return text
        except Exception as e:
            logger.error(f"Failed to extract {filename}: {e}")
            return ""

    def segment_into_sections(self, raw_text: str) -> Dict[str, str]:
        sections = {'general': '', 'experience': '', 'projects': '', 'education': '', 'skills': ''}
        lines = raw_text.split('\n')
        current_section = 'general'
        
        for line in lines:
            line_lower = line.strip().lower()
            if len(line_lower) < 50:
                for sec, pattern in self.section_patterns.items():
                    if re.search(pattern, line_lower):
                        current_section = sec
                        break
            sections[current_section] += line + "\n"
            
        return {k: self.clean_text(v) for k, v in sections.items() if v.strip()}

    def get_hybrid_search_text(self, sections: Dict[str, str]) -> str:
        """
        Combines ONLY Skills, Experience, and Projects for Phase 2 screening.
        Deliberately excludes 'Education' and 'General' as requested.
        """
        return "\n".join([
            sections.get('skills', ''),
            sections.get('experience', ''),
            sections.get('projects', '')
        ]).strip()

class HybridRetriever:
    def __init__(self):
        logger.info("Loading Sentence Transformer...")
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2') 

    def compute_bm25_score(self, query: str, documents: List[str], top_k: int = 10) -> List[Dict]:
        """
        Stage 1: BM25 filtering - Fast sparse search to narrow down candidates.
        """
        if not documents:
            return []

        tokenized_query = query.lower().split()
        tokenized_corpus = [doc.lower().split() for doc in documents]
        bm25 = BM25Okapi(tokenized_corpus)
        bm25_scores = bm25.get_scores(tokenized_query)
        
        # Normalize BM25 scores
        if max(bm25_scores) > 0:
            bm25_scores = bm25_scores / np.max(bm25_scores)

        # Get top-k indices by BM25 score
        top_indices = np.argsort(bm25_scores)[::-1][:top_k]
        
        return [{
            "index": int(idx),
            "bm25_score": float(bm25_scores[idx])
        } for idx in top_indices]

    def compute_semantic_score(self, query: str, filtered_documents: List[Dict]) -> List[Dict]:
        """
        Stage 2: Semantic search on BM25-filtered documents.
        filtered_documents format: [{"index": original_idx, "bm25_score": score}, ...]
        """
        if not filtered_documents:
            return []
        
        # Extract original indices
        original_indices = [doc["index"] for doc in filtered_documents]
        
        # Encode query and filtered documents
        query_embedding = self.encoder.encode(query, convert_to_tensor=True)
        doc_embeddings = self.encoder.encode([doc.get("text", "") for doc in filtered_documents], convert_to_tensor=True)
        semantic_scores = util.cos_sim(query_embedding, doc_embeddings).cpu().numpy()[0]
        
        # Add semantic scores to results
        for i, doc in enumerate(filtered_documents):
            doc["semantic_score"] = float(semantic_scores[i])
        
        return filtered_documents

    def compute_hybrid_score(self, query: str, documents: List[str], top_k: int = 10, bm25_top_k: int = None, alpha: float = 0.4):
        """
        Two-stage hybrid scoring:
        1. BM25 filtering (Stage 1) - narrows down candidates
        2. Semantic search (Stage 2) - ranks filtered candidates
        
        Args:
            query: Search query
            documents: Full list of documents
            top_k: Final number of results to return
            bm25_top_k: Number of candidates to filter with BM25 (default: 3x top_k)
            alpha: Weight for semantic score vs BM25 score in final ranking
        """
        if not documents:
            return []
        
        if bm25_top_k is None:
            bm25_top_k = min(max(3 * top_k, 10), len(documents))
        
        logger.info(f"Stage 1: BM25 filtering {len(documents)} documents down to {bm25_top_k}")
        
        # Stage 1: BM25 filtering
        bm25_results = self.compute_bm25_score(query, documents, top_k=bm25_top_k)
        
        # Prepare documents for semantic search with text content
        filtered_docs_for_semantic = []
        for result in bm25_results:
            filtered_docs_for_semantic.append({
                "index": result["index"],
                "bm25_score": result["bm25_score"],
                "text": documents[result["index"]]
            })
        
        logger.info(f"Stage 2: Semantic search on {len(filtered_docs_for_semantic)} filtered documents")
        
        # Stage 2: Semantic search on filtered documents
        semantic_results = self.compute_semantic_score(query, filtered_docs_for_semantic)
        
        # Normalize semantic scores
        if semantic_results:
            semantic_scores = [r["semantic_score"] for r in semantic_results]
            max_semantic = max(semantic_scores) if max(semantic_scores) > 0 else 1
            for r in semantic_results:
                r["semantic_score"] = r["semantic_score"] / max_semantic
        
        # Stage 3: Hybrid fusion - combine BM25 and semantic scores
        for result in semantic_results:
            bm25_score = result["bm25_score"]
            semantic_score = result["semantic_score"]
            # Hybrid score: 40% semantic + 60% BM25 (prioritizing keyword matching)
            hybrid_score = (alpha * semantic_score) + ((1 - alpha) * bm25_score)
            result["score"] = hybrid_score
        
        # Sort by hybrid score and return top_k
        semantic_results.sort(key=lambda x: x["score"], reverse=True)
        top_results = semantic_results[:top_k]
        
        return [{
            "index": r["index"],
            "score": float(r["score"]),
            "semantic_score": float(r["semantic_score"]),
            "bm25_score": float(r["bm25_score"])
        } for r in top_results]
