"""
tutor_response.py - Legacy AI interface adapter.
Routes calls to the unified AIProvider & RAG engine for accurate educational responses.
"""
from ai_provider import AIProvider


def generate_answer(question):
    """
    Generate an educational response using the unified AI Provider & Curriculum RAG Engine.
    Preserves backward compatibility with existing tests and scripts.
    """
    result = AIProvider.generate_response(
        question=question,
        conversation_history=[],
        user_level="intermediate",
        user_style="detailed",
    )
    return result.get("content", "")


if __name__ == "__main__":
    sample = "What is Artificial Intelligence?"
    print(f"Testing tutor_response with: '{sample}'")
    print(generate_answer(sample))