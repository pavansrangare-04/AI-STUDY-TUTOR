import math
import re
from collections import Counter
from models import db, Subject, Topic, StudyMaterial, MaterialChunk
from database import chunk_text


def tokenize(text):
    """Clean and tokenize text into lower-case words, stripping punctuation."""
    return re.findall(r"\b[a-zA-Z0-9_]{2,}\b", text.lower())


class RAGEngine:
    """Lightweight, self-contained TF-IDF / BM25 document retrieval engine."""

    @staticmethod
    def index_material(material_id, content):
        """Chunk and index a study material into MaterialChunk records."""
        # Remove any existing chunks for this material
        MaterialChunk.query.filter_by(material_id=material_id).delete()

        chunks = chunk_text(content, chunk_size=220, overlap=40)
        for idx, text_chunk in enumerate(chunks):
            words = tokenize(text_chunk)
            stopwords = {"the", "and", "that", "this", "with", "from", "for", "are", "which", "then", "into"}
            keywords = [w for w in set(words) if w not in stopwords and len(w) > 3]
            chunk_obj = MaterialChunk(
                material_id=material_id,
                chunk_index=idx,
                chunk_text=text_chunk,
                keywords=",".join(keywords[:15]),
            )
            db.session.add(chunk_obj)
        db.session.commit()

    @staticmethod
    def search(query, subject_id=None, top_k=3, min_score=0.10):
        """Search indexed material chunks for query keywords using BM25-style scoring."""
        query_terms = tokenize(query)
        stopwords = {"what", "is", "the", "how", "why", "are", "can", "explain", "does", "in", "of", "to", "and", "a", "an"}
        query_terms = [t for t in query_terms if t not in stopwords]

        if not query_terms:
            return []

        # Fetch candidate chunks
        query_builder = db.session.query(MaterialChunk, StudyMaterial, Subject, Topic).join(
            StudyMaterial, MaterialChunk.material_id == StudyMaterial.id
        ).join(
            Subject, StudyMaterial.subject_id == Subject.id
        ).outerjoin(
            Topic, StudyMaterial.topic_id == Topic.id
        )

        if subject_id:
            query_builder = query_builder.filter(StudyMaterial.subject_id == subject_id)

        all_records = query_builder.all()
        if not all_records:
            return []

        total_docs = len(all_records)
        # Compute document frequency for query terms
        doc_freqs = Counter()
        for chunk, mat, sub, top in all_records:
            doc_words = set(tokenize(chunk.chunk_text + " " + mat.title + " " + sub.name))
            for term in query_terms:
                if term in doc_words:
                    doc_freqs[term] += 1

        results = []
        for chunk, mat, sub, top in all_records:
            full_text = f"{mat.title} {chunk.chunk_text} {sub.name} {top.name if top else ''}"
            chunk_words = tokenize(full_text)
            doc_len = len(chunk_words)
            if doc_len == 0:
                continue

            word_counts = Counter(chunk_words)
            score = 0.0

            for term in query_terms:
                tf = word_counts.get(term, 0)
                if tf > 0:
                    df = doc_freqs.get(term, 1)
                    # IDF with smoothing
                    idf = math.log(1 + (total_docs - df + 0.5) / (df + 0.5))
                    # Title & subject matches get heavy boost
                    title_boost = 2.5 if term in mat.title.lower() else 1.0
                    subject_boost = 2.0 if term in sub.name.lower() else 1.0
                    # BM25-style TF saturation
                    k1 = 1.2
                    b = 0.75
                    avg_len = 180.0
                    tf_component = ((k1 + 1) * tf) / (k1 * (1 - b + b * (doc_len / avg_len)) + tf)
                    score += idf * tf_component * title_boost * subject_boost

            if score >= min_score:
                results.append({
                    "chunk_id": chunk.id,
                    "material_id": mat.id,
                    "material_title": mat.title,
                    "subject_name": sub.name,
                    "subject_code": sub.code,
                    "topic_name": top.name if top else "General",
                    "text": chunk.chunk_text,
                    "score": round(score, 3),
                })

        # Sort by relevance score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    @staticmethod
    def build_system_prompt(user_level="intermediate", user_style="detailed"):
        level_instructions = {
            "beginner": "The student is a BEGINNER. Use intuitive analogies, plain English, avoid excessive jargon, and give simple step-by-step examples.",
            "intermediate": "The student has an INTERMEDIATE background. Balance technical accuracy with clear explanations, code or conceptual diagrams, and key definitions.",
            "advanced": "The student has an ADVANCED background. Provide in-depth technical analysis, algorithmic complexity, architectural trade-offs, and underlying mechanics.",
        }

        style_instructions = {
            "concise": "Keep explanations succinct, bulleted, and to-the-point.",
            "detailed": "Provide thorough explanations covering definition, intuition, mechanics, and concrete examples.",
            "step_by_step": "Break explanations into numbered, sequential steps with clear headings.",
        }

        return (
            "You are Virtual AI Tutor, a friendly, highly knowledgeable, and patient academic tutor.\n"
            f"STUDENT PROFILE:\n"
            f"- {level_instructions.get(user_level, level_instructions['intermediate'])}\n"
            f"- {style_instructions.get(user_style, style_instructions['detailed'])}\n\n"
            "TUTORING GUIDELINES:\n"
            "1. If reference study material is provided below, GROUND your answer in it and cite the source.\n"
            "2. If no reference material matches, answer using sound academic principles and clearly state: "
            "'*Note: This explanation is based on general computer science principles as specific study notes were not found in your course library.*'\n"
            "3. Format your answers clearly using Markdown: bold headers, bullet lists, code blocks, or mathematical equations where relevant.\n"
            "4. Be encouraging, accurate, and concise. Never invent false facts or hallucinate citations.\n"
        )
