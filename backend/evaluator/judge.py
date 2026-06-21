from backend.config import get_llm
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
import json
import re

JUDGE_SYSTEM_PROMPT = ChatPromptTemplate.from_template("""
You are a strict, impartial RAG evaluation judge. Your job is to score an AI answer against a question.

Scoring rubric — score each criterion from 0 to 10:

1. faithfulness (0-10): Is the answer grounded in the retrieved context? 
   - 10 = every claim is directly supported by context
   - 5  = mostly supported but has minor unsupported claims
   - 0  = answer contradicts or ignores the context entirely

2. completeness (0-10): Does the answer fully address the question?
   - 10 = fully addresses all parts of the question
   - 5  = partially answers, misses some aspects
   - 0  = does not answer the question at all

3. conciseness (0-10): Is the answer appropriately concise?
   - 10 = tight, no filler, every sentence adds value
   - 5  = somewhat verbose or slightly off-topic
   - 0  = extremely verbose, repetitive, or filled with irrelevant content

You MUST return ONLY a valid JSON object with no explanation, no markdown, no preamble.

Question: {question}
Answer: {answer}
Context used: {context}

Return format:
{{"faithfulness": <int>, "completeness": <int>, "conciseness": <int>, "reasoning": "<one sentence>"}}
""")

def score_answer(question: str, answer: str, context: str) -> dict:
    """
    Ask the judge LLM to score a single answer.
    Returns a dict with faithfulness, completeness, conciseness scores + reasoning.
    """
    chain = JUDGE_SYSTEM_PROMPT | get_llm() | StrOutputParser()

    raw = chain.invoke({
        "question": question,
        "answer": answer,
        "context": context,
    })

    cleaned = re.sub(r"```json|```", "", raw).strip()

    try:
        scores = json.loads(cleaned)
        # Validate expected keys exist
        for key in ["faithfulness", "completeness", "conciseness"]:
            if key not in scores:
                scores[key] = 5  # neutral fallback
        scores["average"] = round(
            (scores["faithfulness"] + scores["completeness"] + scores["conciseness"]) / 3, 2
        )
        return scores
    except (json.JSONDecodeError, KeyError) as e:
        print(f"[Judge] Score parse failed: {e}. Raw output: {raw[:200]}")
        return {
            "faithfulness": 5,
            "completeness": 5,
            "conciseness": 5,
            "average": 5.0,
            "reasoning": "Score parsing failed — neutral score assigned.",
        }

def get_context_for_question(variant: dict, question: str) -> str:
    """Retrieve the actual context chunks a variant would use for a question."""
    docs = variant["retriever"].invoke(question)
    return "\n\n---\n\n".join(doc.page_content for doc in docs)