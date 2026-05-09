import json
import logging
from typing import List
import ollama

logger = logging.getLogger(__name__)

class JDExtractor:
    def __init__(self, model_name: str = "gpt-oss:20b-cloud"):
        self.model_name = model_name  # Replace with preferred local model (e.g., mistral, gemma, neural-chat)
        # Ollama client automatically connects to http://localhost:11434
        self.client = ollama.Client()

    def extract_must_have_skills(self, job_description: str) -> List[str]:
        """
        Uses a local Ollama model to extract a structured list of must-have skills from a JD.
        If the LLM fails, falls back to an empty list.
        """
        prompt = f"""
        Extract the top 10core technical skills, tools, and frameworks required in the following Job Description.
        Return ONLY a raw JSON list of strings. Do not include markdown formatting or explanation.
        Example output: ["Python", "AWS", "Docker", "FastAPI"]
        
        Job Description:
        {job_description}
        """
        
        try:
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                stream=False,
                format="json",
                options={"temperature": 0.0}
            )
            
            response_text = response.get("response", "[]")
            skills = json.loads(response_text)
            
            if isinstance(skills, list):
                return [str(s).strip() for s in skills if s]
            return []
            
        except Exception as e:
            logger.error(f"Phase 1 LLM Extraction failed: {e}. Falling back to empty list.")
            return []