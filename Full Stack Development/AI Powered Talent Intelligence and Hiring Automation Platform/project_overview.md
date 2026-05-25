## Project Overview: HireForge PRO (Neural Resume Intelligence Engine)

**Core Objective:** HireForge PRO is an advanced Information Retrieval (IR) and Applied NLP system designed to automate the recruitment screening process. Moving beyond basic "AI wrappers," the system intelligently parses job descriptions, semantically filters large batches of resumes, and performs deep contextual verification to determine if a candidate possesses professional-grade experience, academic exposure, or lacks a required skill.

The system guarantees explainability for HR professionals by exposing the exact resume bullet points used to verify a skill, alongside an AI-generated candidate verdict.

---

## The Execution Pipeline: A 4-Phase Architecture

The project execution is designed around a highly deterministic, sequential pipeline that prioritizes computational efficiency and contextual accuracy.

### Phase 1: Requirement Extraction (The Inbound Phase)

* **The Process:** The system ingests a raw, unstructured Job Description (JD) provided by the recruiter.
* **The Technology:** A  Large Language Model (`gpt-oss:20b-cloud`)  is prompted to act as an extraction engine. It analyzes the text and outputs a strict, structured JSON array of the "Must-Have" technical skills, tools, and frameworks.
* **The Value:** This creates a deterministic checklist that drives the rest of the verification pipeline, ensuring the AI focuses strictly on business requirements rather than hallucinating preferences.

### Phase 2: Document Parsing & Mass Screening (The Hybrid Filter)

* **Document Segmentation:** The system reads uploaded resumes (PDF, DOCX, TXT) and uses advanced Regex logic to slice the document into distinct contextual sections: *Experience, Projects, Education, and Skills*. It explicitly preserves formatting like newlines and bullet points to retain the semantic meaning of the text.
* **Hybrid Retrieval:** Instead of running heavy inference on thousands of documents, the system uses a two-stage filter on the professional sections of the resume.
* **BM25 (Sparse):** Acts as a high-speed keyword filter to quickly find documents containing exact technical terms.
* **Sentence Transformers (Dense):** Computes cosine similarity to find semantic matches (e.g., matching "Web Development" to "Frontend Engineering").


* **The Value:** This phase efficiently narrows down a massive talent pool to the top 10-15 most relevant candidates in milliseconds.

### Phase 3: Deep NLP Context Verification (The Intelligence Phase)

This is the "Brain" of the operation. For every candidate that passes Phase 2, the system investigates their specific skills using a Neural pipeline:

* **Zero-Shot Classification (The Context Filter):** The isolated bullet point is fed into a Zero-Shot Classifier. The model determines the *context* of the skill, labeling it as:
1. **Verified Professional:** Hands-on execution or deployment.
2. **Academic/Partial:** Theoretical knowledge, coursework, or certifications.
3. **Missing:** No evidence found.


### Phase 4: Scoring, Synthesis, and UI Delivery (The Output Phase)

* **Deterministic Scoring:** The system calculates a final weighted score. For example, 30% of the weight comes from the overall Hybrid Retrieval relevance, while 70% is driven by the rigorous NLP Verification from Phase 3.
* **AI Verdict Generation:** The system passes the matched, partial, and missing skills back to the same cloud LLM to generate a concise, 2-sentence human-readable summary of the candidate's core strengths and areas for improvement.
* **Dashboard Presentation:** The backend serves all this data to a custom, responsive frontend where recruiters can view candidate ranks, skill matrices, and the specific text evidence the AI used to make its decisions.

---

## Technical Stack Breakdown

This project intentionally minimizes reliance on heavy third-party abstractions (like LangChain or external VectorDBs) to maximize local hardware optimization and developer control.

### AI & Natural Language Processing (NLP)

* **Ollama:** Uses `gpt-oss:20b-cloud` model only for JD extraction and AI verdict generation.
* **Hugging Face `transformers`:** Powers the Zero-Shot Classification pipeline (`nli-distilroberta-base-v2`) for blazing-fast contextual inference on CPU or local GPU.
* **`sentence-transformers`:** Drives the semantic embedding engine (`all-MiniLM-L6-v2`) used in both Phase 2 mass retrieval and Phase 3 evidence scouting.
* **`rank_bm25`:** A lightweight Python implementation of the Okapi BM25 algorithm for high-speed keyword retrieval.

### Backend Engineering

* **FastAPI (Python):** The core asynchronous web framework. Selected for its speed, native Pydantic validation, and robust handling of concurrent file uploads.
* **Data Parsing Libraries:** `PyPDF2` and `python-docx` for reliable text extraction from uploaded candidate files.
* **Regex (`re`) & NumPy:** Utilized heavily for intelligent document segmentation, data cleaning, and matrix mathematics for hybrid score fusion.

### Frontend User Interface

* **Vanilla Tech Stack:** Pure HTML5, CSS3, and JavaScript. No React or heavy node modules required, ensuring instant load times and zero build steps.
* **Design Language:** A "Cyber-Corporate" aesthetic featuring dark mode glassmorphism, dynamic progress loaders, interactive skill tags, and high-end typography (Syne, Sora, Space Mono).
* **Asynchronous API Integration:** Utilizes JavaScript `fetch` and `FormData` to handle batch file uploads and dynamically render complex JSON responses into visual scorecards.