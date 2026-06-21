from __future__ import annotations
import os
import sys
import time
import json
from backend.evaluator.question_gen import generate_test_questions
from backend.evaluator.judge import score_answer
from backend.factory.rag_chain import build_all_variants
from backend.ingestion.ingestor import extract_text_from_pdf

WINNER_PATH = "winning_config.json"

# ── Groq free tier limits ─────────────────────────────────────────────────────
# llama-3.1-8b-instant: 30 req/min, 6000 tokens/min
# With 8 variants x 3 questions x 2 LLM calls = 48 calls total
# We run them fully sequentially with a mandatory pause between each call.
# Total time: ~48 calls x 2.5s = ~2 minutes. Fast enough, no rate limit loops.
DELAY_BETWEEN_CALLS = 2.5  # seconds between every single LLM call

def call_with_retry(fn, *args, label="", max_retries=4):
    """
    Call fn(*args) sequentially with exponential backoff.
    No threading — Groq free tier can't handle parallel calls.
    """
    for attempt in range(max_retries):
        try:
            result = fn(*args)
            time.sleep(DELAY_BETWEEN_CALLS)  # mandatory cooldown after every call
            return result
        except Exception as e:
            error_str = str(e).lower()
            is_rate_limit = any(x in error_str for x in [
                "429", "rate limit", "too many", "rate_limit_exceeded"
            ])

            if attempt == max_retries - 1:
                print(f"  [FAILED] {label} — gave up after {max_retries} attempts.")
                raise

            if is_rate_limit:
                # Exponential backoff: 15s, 30s, 60s
                wait = 15 * (2 ** attempt)
                print(f"  [RateLimit] {label} — waiting {wait}s before retry {attempt+2}/{max_retries}...")
                time.sleep(wait)
            else:
                # Non-rate-limit error — short wait then retry
                wait = 3 * (attempt + 1)
                print(f"  [Error] {label} — {str(e)[:80]} — retrying in {wait}s...")
                time.sleep(wait)


def evaluate_variant(variant_name: str, variant_dict: dict, question: str, q_num: int, total: int):
    """
    Run one full evaluation: get answer, then get judge score.
    Two sequential LLM calls with cooldown between them.
    """
    retriever = variant_dict["retriever"]
    chain     = variant_dict["chain"]

    print(f"  [{q_num}/{total}] [{variant_name}] Getting answer...")

    try:
        # Retrieve context (local — no API call)
        docs    = retriever.invoke(question)
        context = "\n\n---\n\n".join(doc.page_content for doc in docs)

        # LLM call 1 — generate answer
        answer = call_with_retry(
            chain.invoke, question,
            label=f"{variant_name}/answer"
        )

        # LLM call 2 — judge scores the answer
        print(f"  [{q_num}/{total}] [{variant_name}] Judging answer...")
        scores = call_with_retry(
            score_answer, question, answer, context,
            label=f"{variant_name}/judge"
        )

        q_short = question[:55] + "..." if len(question) > 55 else question
        print(f"  [{q_num}/{total}] [{variant_name}] ✓ {q_short}")
        print(f"    → faith:{scores.get('faithfulness', 0)}  "
              f"complete:{scores.get('completeness', 0)}  "
              f"concise:{scores.get('conciseness', 0)}  "
              f"avg:{scores.get('average', 0.0)}")

        return {
            "variant":  variant_name,
            "question": question,
            "answer":   answer,
            "scores":   scores,
        }

    except Exception as e:
        print(f"  [SKIP] {variant_name} — all retries exhausted: {e}")
        return None


def run_optimization(pdf_path: str, doc_id: str = "default_id") -> dict:
    print("\n" + "=" * 60)
    print("  RAG OPTIMIZER STARTING  (Groq / sequential mode)")
    print("=" * 60)

    # Step 1 — Extract text
    print(f"\n[Ingestor] Extracting text from {pdf_path}...")
    raw_text = extract_text_from_pdf(pdf_path)
    print(f"[Ingestor] Extracted {len(raw_text):,} characters.")

    # Step 2 — Generate test questions (1 LLM call)
    questions = generate_test_questions(raw_text)
    if isinstance(questions, dict) and "questions" in questions:
        questions = questions["questions"]
    print(f"[QuestionGen] {len(questions)} questions ready.\n")

    # Step 3 — Build all variants (local only, no API calls)
    print("[Optimizer] Building variants...")
    variants_list = build_all_variants(doc_id)
    built_variants = {v["config"]["variant_id"]: v for v in variants_list}
    print(f"[Factory] {len(built_variants)} variants ready.\n")

    # Step 4 — Sequential evaluation loop
    # Build the full task list so we can show progress as X/total
    tasks = [
        (variant_name, variant_dict, question)
        for variant_name, variant_dict in built_variants.items()
        for question in questions
    ]
    total_calls = len(tasks) * 2  # 2 LLM calls per task
    print(f"[Optimizer] {len(tasks)} evaluations × 2 LLM calls = {total_calls} total API calls")
    print(f"[Optimizer] Sequential mode: ~{round(total_calls * DELAY_BETWEEN_CALLS / 60, 1)} min estimated")
    print("-" * 60)

    results = []
    for i, (variant_name, variant_dict, question) in enumerate(tasks, 1):
        result = evaluate_variant(variant_name, variant_dict, question, i, len(tasks))
        if result:
            results.append(result)

    # Step 5 — Compute scoreboard
    print("\n" + "=" * 60)
    print("  FINAL SCOREBOARD")
    print("=" * 60)

    # Aggregate scores per variant
    scoreboard_raw: dict[str, list] = {}
    for r in results:
        scoreboard_raw.setdefault(r["variant"], []).append(r["scores"].get("average", 0))

    if not scoreboard_raw:
        raise ValueError(
            "All evaluations failed. "
            "Check that Groq API key is valid and GROQ_API_KEY is set in .env"
        )

    ranked = sorted(
        [(v, sum(s) / len(s)) for v, s in scoreboard_raw.items()],
        key=lambda x: x[1],
        reverse=True,
    )

    for rank, (variant_id, score) in enumerate(ranked, 1):
        marker = "  ← WINNER" if rank == 1 else ""
        print(f"  #{rank}  {variant_id:<35} avg: {score:.2f}/10{marker}")

    # Step 6 — Build full scoreboard dict (for frontend scoreboard tab)
    full_scoreboard: dict[str, list] = {}
    for r in results:
        full_scoreboard.setdefault(r["variant"], []).append({
            **r["scores"],
            "question": r["question"],
            "answer":   r["answer"],
        })

    # Step 7 — Save winner
    best_id     = ranked[0][0]
    best_score  = ranked[0][1]
    winner_dict = next(v for v in variants_list if v["config"]["variant_id"] == best_id)

    winner_dict["config"]["final_score"] = round(best_score, 2)
    winner_dict["config"]["doc_id"]      = doc_id
    winner_dict["config"]["scoreboard"]  = full_scoreboard

    saveable = {
        k: v for k, v in winner_dict["config"].items()
        if k not in ("chain", "retriever")
    }
    with open(WINNER_PATH, "w") as f:
        json.dump(saveable, f, indent=2)

    print(f"\n[Optimizer] Winner saved → {WINNER_PATH}")
    print(f"[Optimizer] Winning config: {best_id}  (score: {best_score:.2f})")
    print("=" * 60 + "\n")

    return winner_dict


def load_winner_chain(doc_id: str = None):
    """Load the winning RAG chain from disk after optimization."""
    if not os.path.exists(WINNER_PATH):
        raise FileNotFoundError("No winning config found. Run optimization first.")

    with open(WINNER_PATH) as f:
        config = json.load(f)

    if doc_id and config.get("doc_id") != doc_id:
        raise ValueError(
            f"Saved winner is for doc '{config.get('doc_id')}', not '{doc_id}'"
        )

    from backend.factory.rag_chain import build_rag_chain
    variant = build_rag_chain(
        collection_name=config["collection_name"],
        top_k=config["top_k"],
    )
    variant["config"] = config
    print(f"[Optimizer] Loaded winning chain: {config['variant_id']} "
          f"(score: {config['final_score']})")
    return variant


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m backend.evaluator.optimizer <path_to_pdf> [doc_id]")
        sys.exit(1)
    run_optimization(
        sys.argv[1],
        sys.argv[2] if len(sys.argv) > 2 else "terminal_test_run"
    )