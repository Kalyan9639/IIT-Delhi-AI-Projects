import re
import logging
import numpy as np
from typing import Tuple
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util

logger = logging.getLogger(__name__)


class NLPEngine:
    def __init__(self):
        logger.info("Loading Zero-Shot NLP Pipeline & Semantic Scout...")
        self.classifier = pipeline(
            "zero-shot-classification",
            model="sentence-transformers/nli-distilroberta-base-v2",
            device=-1
        )
        self.evidence_scout = SentenceTransformer("all-MiniLM-L6-v2")
        self.labels = [
            "professional experience and execution",
            "academic learning or coursework",
            "theoretical knowledge",
        ]

        # Power verbs: if these exist in the evidence, it's definitely professional execution
        self.power_verbs = [
            "architected",
            "shipped",
            "built",
            "deployed",
            "implemented",
            "integrated",
            "developed",
        ]

    def evaluate_skill_context(self, section_text: str, skill: str, section_name: str) -> Tuple[str, float, str]:
        """
        Uses semantic scouting to find the best bullet point and classify its context.
        Returns: (status, confidence_score, evidence_text)
        """
        # Preserve line-level structure and only strip bullet prefixes from each line.
        bullets = []
        for raw_line in section_text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
            line = raw_line.strip()
            line = re.sub(r"^(?:[•\u2022*\-]+\s*|\d+[\).\s]+\s*)", "", line)
            if len(line) > 5:
                bullets.append(line)
        if not bullets:
            return "Missing", 0.0, ""

        # 1. Semantic scout: find the bullet that best matches the skill
        skill_emb = self.evidence_scout.encode(skill, convert_to_tensor=True)
        bullet_embs = self.evidence_scout.encode(bullets, convert_to_tensor=True)
        cosine_scores = util.cos_sim(skill_emb, bullet_embs).cpu().numpy()[0]

        best_idx = int(np.argmax(cosine_scores))
        best_score = float(cosine_scores[best_idx])
        relevant_bullet = bullets[best_idx]

        # Lower threshold slightly to catch subtle tech stack mentions
        if best_score < 0.35:
            return "Missing", 0.0, ""

        section_name = (section_name or "").lower()
        if section_name == "education":
            return "Academic/Partial", 0.65, relevant_bullet

        # 2. Heuristic override for real hands-on evidence
        bullet_lower = relevant_bullet.lower()
        if any(verb in bullet_lower for verb in self.power_verbs):
            return "Verified Professional", 0.95, relevant_bullet

        # 3. Zero-shot classification
        try:
            result = self.classifier(relevant_bullet, candidate_labels=self.labels)
            top_label = result["labels"][0]
            confidence = float(result["scores"][0])

            if top_label == "professional experience and execution":
                return "Verified Professional", confidence, relevant_bullet
            if top_label == "academic learning or coursework":
                return "Academic/Partial", confidence, relevant_bullet
            return "Missing", confidence, relevant_bullet
        except Exception as e:
            logger.error(f"NLP Classification failed: {e}")
            return "Academic/Partial", 0.6, relevant_bullet
