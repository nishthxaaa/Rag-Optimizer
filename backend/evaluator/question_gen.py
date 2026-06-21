from backend.config import get_llm
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
import json
import re

QUESTION_GEN_PROMPT = ChatPromptTemplate.from_template("""
You are preparing a RAG system evaluation. Read the following text excerpt from a document and generate exactly 3 test questions.

Rules:
- Questions must be answerable from this document specifically
- Questions should require understanding, not just keyword matching
- Vary the questions: one factual, one analytical, one that requires combining two pieces of information
- Return ONLY a JSON array of 3 strings, no explanation, no markdown

Text excerpt:
{text_sample}

Return format:
["question 1", "question 2", "question 3"]
""")

def generate_test_questions(raw_text: str) -> list[str]:
    """
    Automatically generate evaluation questions from the document.
    Uses a sample from the middle of the document for better coverage.
    """
    # Take a sample from the middle of the document — avoids intros/appendices
    total_len = len(raw_text)
    start = total_len // 4
    end = start + 3000
    text_sample = raw_text[start:min(end, total_len)]

    chain = QUESTION_GEN_PROMPT | get_llm() | StrOutputParser()

    print("[QuestionGen] Generating test questions from document sample...")
    raw_output = chain.invoke({"text_sample": text_sample})

    # Strip markdown fences if the LLM wraps output anyway
    cleaned = re.sub(r"```json|```", "", raw_output).strip()

    try:
        questions = json.loads(cleaned)
        if not isinstance(questions, list) or len(questions) == 0:
            raise ValueError("Expected a non-empty list")
        print(f"[QuestionGen] Generated {len(questions)} questions:")
        for i, q in enumerate(questions, 1):
            print(f"  {i}. {q}")
        return questions
    except (json.JSONDecodeError, ValueError) as e:
        print(f"[QuestionGen] JSON parse failed ({e}), using fallback questions.")
        return [
            "What is the main topic of this document?",
            "What are the key details or findings described?",
            "What conclusions or outcomes does this document present?",
        ]