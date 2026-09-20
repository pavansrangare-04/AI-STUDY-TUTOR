import os
import json
import httpx
from config import Config
from rag_engine import RAGEngine


class AIProvider:
    """Unified AI Provider interface with automatic fallback and RAG grounding."""

    @staticmethod
    def get_active_provider_info():
        """Returns the currently configured and available AI provider status."""
        configured = Config.AI_PROVIDER

        # Explicit user selection overrides auto
        if configured == "openrouter" and Config.OPENROUTER_API_KEY:
            return {"provider": "openrouter", "model": Config.OPENROUTER_MODEL, "is_cloud": True, "label": f"OpenRouter ({Config.OPENROUTER_MODEL})"}
        elif configured == "gemini" and Config.GEMINI_API_KEY:
            return {"provider": "gemini", "model": "gemini-1.5-flash", "is_cloud": True, "label": "Google Gemini 1.5 Flash"}
        elif configured == "groq" and Config.GROQ_API_KEY:
            return {"provider": "groq", "model": "llama-3.3-70b-versatile", "is_cloud": True, "label": "Groq LLaMA 3.3 70B"}
        elif configured == "openai" and Config.OPENAI_API_KEY:
            return {"provider": "openai", "model": "gpt-4o-mini", "is_cloud": True, "label": "OpenAI GPT-4o-mini"}

        # Auto detection
        if Config.OPENROUTER_API_KEY:
            return {"provider": "openrouter", "model": Config.OPENROUTER_MODEL, "is_cloud": True, "label": f"OpenRouter ({Config.OPENROUTER_MODEL})"}
        elif Config.GEMINI_API_KEY:
            return {"provider": "gemini", "model": "gemini-1.5-flash", "is_cloud": True, "label": "Google Gemini 1.5 Flash"}
        elif Config.GROQ_API_KEY:
            return {"provider": "groq", "model": "llama-3.3-70b-versatile", "is_cloud": True, "label": "Groq LLaMA 3.3 70B"}
        elif Config.OPENAI_API_KEY:
            return {"provider": "openai", "model": "gpt-4o-mini", "is_cloud": True, "label": "OpenAI GPT-4o-mini"}
        else:
            return {
                "provider": "local_rag",
                "model": "Local RAG & Knowledge Engine",
                "is_cloud": False,
                "label": "Built-in Curriculum RAG Engine (Offline / Local)",
            }

    @classmethod
    def generate_response(
        cls,
        question: str,
        conversation_history=None,
        subject_id=None,
        user_level="intermediate",
        user_style="detailed",
    ):
        """Generate an educational answer with RAG retrieval and provider dispatch."""
        conversation_history = conversation_history or []

        # 1. RAG Retrieval
        retrieved_chunks = RAGEngine.search(question, subject_id=subject_id, top_k=3, min_score=0.15)
        is_grounded = len(retrieved_chunks) > 0

        # Format context for prompt
        context_text = ""
        sources = []
        if is_grounded:
            context_pieces = []
            for i, chunk in enumerate(retrieved_chunks, 1):
                context_pieces.append(
                    f"--- Source [{i}]: {chunk['subject_name']} ({chunk['subject_code']}) - {chunk['material_title']} (Topic: {chunk['topic_name']}) ---\n"
                    f"{chunk['text']}\n"
                )
                sources.append({
                    "id": chunk["material_id"],
                    "title": chunk["material_title"],
                    "subject": chunk["subject_name"],
                    "topic": chunk["topic_name"],
                    "snippet": chunk["text"][:180] + "...",
                    "score": chunk["score"],
                })
            context_text = "\n".join(context_pieces)

        system_prompt = RAGEngine.build_system_prompt(user_level, user_style)

        # 2. Try configured Cloud AI Providers
        provider_info = cls.get_active_provider_info()
        provider = provider_info["provider"]

        if provider == "openrouter" and Config.OPENROUTER_API_KEY:
            try:
                response_text = cls._call_openrouter(
                    system_prompt, question, context_text, conversation_history
                )
                if not response_text:
                    raise ValueError("Empty response from OpenRouter")
                followups = cls._generate_followups(question, response_text)
                return {
                    "content": response_text,
                    "provider": "openrouter",
                    "model": Config.OPENROUTER_MODEL,
                    "sources": sources,
                    "is_grounded": is_grounded,
                    "suggested_followups": followups,
                }
            except Exception as exc:
                print(f"[AIProvider] OpenRouter API call failed: {exc}. Falling back to local RAG engine.")

        elif provider == "gemini" and Config.GEMINI_API_KEY:
            try:
                response_text = cls._call_gemini(
                    system_prompt, question, context_text, conversation_history
                )
                followups = cls._generate_followups(question, response_text)
                return {
                    "content": response_text,
                    "provider": "gemini",
                    "model": "gemini-1.5-flash",
                    "sources": sources,
                    "is_grounded": is_grounded,
                    "suggested_followups": followups,
                }
            except Exception as exc:
                print(f"[AIProvider] Gemini API call failed: {exc}. Falling back to local RAG engine.")

        elif provider == "groq" and Config.GROQ_API_KEY:
            try:
                response_text = cls._call_groq(
                    system_prompt, question, context_text, conversation_history
                )
                followups = cls._generate_followups(question, response_text)
                return {
                    "content": response_text,
                    "provider": "groq",
                    "model": "llama-3.3-70b-versatile",
                    "sources": sources,
                    "is_grounded": is_grounded,
                    "suggested_followups": followups,
                }
            except Exception as exc:
                print(f"[AIProvider] Groq API call failed: {exc}. Falling back to local RAG engine.")

        elif provider == "openai" and Config.OPENAI_API_KEY:
            try:
                response_text = cls._call_openai(
                    system_prompt, question, context_text, conversation_history
                )
                followups = cls._generate_followups(question, response_text)
                return {
                    "content": response_text,
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "sources": sources,
                    "is_grounded": is_grounded,
                    "suggested_followups": followups,
                }
            except Exception as exc:
                print(f"[AIProvider] OpenAI API call failed: {exc}. Falling back to local RAG engine.")

        # 3. Intelligent Local RAG & Academic Knowledge Fallback
        fallback_text = cls._synthesize_local_response(
            question, retrieved_chunks, user_level, user_style, conversation_history
        )
        followups = cls._generate_followups(question, fallback_text)
        return {
            "content": fallback_text,
            "provider": "local_rag",
            "model": "Local RAG & Knowledge Engine",
            "sources": sources,
            "is_grounded": is_grounded,
            "suggested_followups": followups,
        }

    # =========================================================================
    # Cloud Provider Implementations (REST via HTTPX)
    # =========================================================================
    @classmethod
    def _call_gemini(cls, system_prompt, question, context_text, history):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={Config.GEMINI_API_KEY}"
        contents = []

        # Add recent conversation turns
        for msg in history[-4:]:
            role = "user" if msg.sender == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg.content}]})

        user_message_text = question
        if context_text:
            user_message_text = (
                f"REFERENCE STUDY MATERIALS FROM STUDENT LIBRARY:\n{context_text}\n\n"
                f"STUDENT QUESTION: {question}\n\n"
                "Please answer thoroughly, citing the reference material."
            )

        contents.append({"role": "user", "parts": [{"text": user_message_text}]})

        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.5, "maxOutputTokens": 1024},
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    @classmethod
    def _call_groq(cls, system_prompt, question, context_text, history):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {Config.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        messages = [{"role": "system", "content": system_prompt}]

        for msg in history[-4:]:
            messages.append({"role": msg.sender, "content": msg.content})

        user_content = question
        if context_text:
            user_content = (
                f"REFERENCE STUDY MATERIALS:\n{context_text}\n\n"
                f"STUDENT QUESTION: {question}"
            )
        messages.append({"role": "user", "content": user_content})

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.5,
            "max_tokens": 1024,
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    @classmethod
    def _call_openai(cls, system_prompt, question, context_text, history):
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {Config.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-4:]:
            messages.append({"role": msg.sender, "content": msg.content})

        user_content = question
        if context_text:
            user_content = f"REFERENCE MATERIALS:\n{context_text}\n\nQUESTION: {question}"
        messages.append({"role": "user", "content": user_content})

        payload = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "temperature": 0.5,
            "max_tokens": 1024,
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    @classmethod
    def _call_openrouter(cls, system_prompt, question, context_text, history):
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "AI Study Tutor",
            "Content-Type": "application/json",
        }
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-4:]:
            role = "user" if getattr(msg, "sender", "user") == "user" else "assistant"
            messages.append({"role": role, "content": getattr(msg, "content", "")})

        user_content = question
        if context_text:
            user_content = (
                f"REFERENCE STUDY MATERIALS FROM STUDENT LIBRARY:\n{context_text}\n\n"
                f"STUDENT QUESTION: {question}\n\n"
                "Please answer thoroughly, citing the reference material."
            )
        messages.append({"role": "user", "content": user_content})

        # Automatic fallback models across free tier
        models_list = [
            Config.OPENROUTER_MODEL,
            "nex-agi/nex-n2.5-mini:free",
            "liquid/lfm-2.5-2.6b:free",
            "cohere/north-mini-code:free",
        ]
        # Preserve order while removing duplicates
        seen = set()
        fallback_models = [m for m in models_list if not (m in seen or seen.add(m))]

        payload = {
            "models": fallback_models,
            "messages": messages,
            "temperature": 0.5,
            "max_tokens": 1024,
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices") or []
            if not choices:
                raise ValueError("No choices returned in OpenRouter response")
            msg_obj = choices[0].get("message") or {}
            content = msg_obj.get("content") or msg_obj.get("reasoning") or ""
            if not content.strip():
                raise ValueError("Received empty content from OpenRouter")
            return content.strip()

    # =========================================================================
    # Local Academic Synthesis & RAG Fallback
    # =========================================================================
    @classmethod
    def _synthesize_local_response(cls, question, retrieved_chunks, user_level, user_style, history):
        """High quality deterministic educational response synthesized from indexed notes."""
        q_lower = question.lower()

        # If study library has matching material:
        if retrieved_chunks:
            top_chunk = retrieved_chunks[0]
            sub_name = top_chunk["subject_name"]
            mat_title = top_chunk["material_title"]
            text_body = top_chunk["text"]

            response = [
                f"### Explanation: {mat_title}\n",
                f"> 📚 **Grounded in Course Material**: *{sub_name}* &mdash; `{top_chunk['topic_name']}`\n",
                f"{text_body}\n\n",
            ]

            if len(retrieved_chunks) > 1:
                second = retrieved_chunks[1]
                response.append(f"#### Additional Key Insights ({second['topic_name']})\n")
                response.append(f"{second['text']}\n\n")

            response.append(
                "---\n"
                f"💡 **Tutor Study Tip ({user_level.capitalize()} Level)**: "
                f"Review the core terms highlighted above, then test your understanding by taking the topic quiz in the **Quiz Center**!"
            )
            return "".join(response)

        # General Computer Science question fallback if no exact library document
        general_answers = {
            "what is ai": (
                "### What is Artificial Intelligence (AI)?\n\n"
                "**Artificial Intelligence (AI)** is the branch of computer science dedicated to developing algorithms "
                "and systems capable of performing tasks that traditionally require human cognitive capabilities.\n\n"
                "#### Core Disciplines of AI:\n"
                "1. **Machine Learning (ML)**: Statistical models that learn mappings from empirical training data without explicit hardcoded rules.\n"
                "2. **Natural Language Processing (NLP)**: Enabling computers to understand, parse, and generate human languages (e.g., Transformers, LLMs).\n"
                "3. **Computer Vision**: Automated extraction, analysis, and understanding of visual information from digital images or video.\n"
                "4. **Robotics & Expert Systems**: Emulating decision-making processes and automating physical or logical tasks.\n\n"
                "*Note: This explanation is based on general computer science principles as specific study notes were not found in your course library.*"
            ),
            "what is photosynthesis": (
                "### Photosynthesis Overview\n\n"
                "**Photosynthesis** is the biological process by which green plants, algae, and certain cyanobacteria "
                "convert light energy into chemical energy stored in glucose molecules.\n\n"
                "#### Chemical Equation:\n"
                "$$6\\text{CO}_2 + 6\\text{H}_2\\text{O} + \\text{Light} \\to \\text{C}_6\\text{H}_{12}\\text{O}_6 + 6\\text{O}_2$$\n\n"
                "#### Key Stages:\n"
                "1. **Light-Dependent Reactions**: Occur in the thylakoid membranes, generating ATP and NADPH while releasing oxygen gas.\n"
                "2. **Calvin Cycle (Light-Independent)**: Occurs in the stroma, using ATP and NADPH to fix carbon dioxide into sugar.\n\n"
                "*Note: This explanation is based on general scientific knowledge.*"
            ),
        }

        for key, ans in general_answers.items():
            if key in q_lower:
                return ans

        # Default structured academic response
        return (
            f"### Academic Tutor Response\n\n"
            f"Thank you for asking about: **{question.strip()}**.\n\n"
            f"To provide the most accurate guidance, the AI Tutor searches your course library. "
            f"Currently, no matching study materials were found for this query in the uploaded library files.\n\n"
            f"#### How to get full answers:\n"
            f"1. Connect an AI provider API key (such as **Google Gemini** or **Groq**) in your `.env` file to enable unlimited web-scale AI answers.\n"
            f"2. Or ask questions related to your loaded subjects: **Operating Systems**, **Data Structures**, **DBMS**, or **AI/ML**.\n"
            f"3. Administrators can also upload new study notes and guides in the **Admin Resources** section!\n\n"
            f"*Note: Running on the built-in Curriculum RAG Engine.*"
        )

    @staticmethod
    def _generate_followups(question, answer_text):
        """Generate smart contextual follow-up questions."""
        q_lower = question.lower()
        if "process" in q_lower or "scheduling" in q_lower:
            return [
                "What is the difference between preemptive and non-preemptive scheduling?",
                "How does Round Robin scheduling choose the time quantum?",
                "Can you explain the components of a Process Control Block (PCB)?",
            ]
        elif "memory" in q_lower or "paging" in q_lower:
            return [
                "What causes a page fault, and how does the OS handle it?",
                "What is the difference between internal and external fragmentation?",
                "How does the Translation Lookaside Buffer (TLB) improve performance?",
            ]
        elif "dsa" in q_lower or "tree" in q_lower or "graph" in q_lower or "array" in q_lower:
            return [
                "What are the trade-offs between Arrays and Linked Lists?",
                "How does an AVL Tree maintain balance during insertion?",
                "When should I use BFS instead of DFS on a graph?",
            ]
        elif "dbms" in q_lower or "normalization" in q_lower or "acid" in q_lower:
            return [
                "What is the difference between 3NF and BCNF?",
                "How does Write-Ahead Logging (WAL) guarantee durability?",
                "Explain the phantom read anomaly in SQL transactions.",
            ]
        elif "ai" in q_lower or "machine learning" in q_lower or "rag" in q_lower:
            return [
                "What is the difference between Supervised and Unsupervised learning?",
                "How does Self-Attention work in Transformer models?",
                "How does Retrieval-Augmented Generation (RAG) prevent hallucinations?",
            ]
        else:
            return [
                "Can you explain this with a practical real-world example?",
                "What are common exam questions or edge cases for this topic?",
                "Could you provide a step-by-step summary for quick revision?",
            ]
