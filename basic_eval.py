import json
import os
import re
import time

import requests
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

BASE_URL = "http://127.0.0.1:8000"
SESSION_ID = "eval-session"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

QUESTIONS = [
    "What are the major phases of the incident response lifecycle?",
    "What should organizations do during the preparation phase of incident handling?",
    "What is the purpose of incident detection and analysis?",
    "What activities are included in containment, eradication, and recovery?",
    "Why are post-incident activities important after handling a computer security incident?",
]


def ask_agent(question):
    start = time.perf_counter()
    response = requests.post(
        f"{BASE_URL}/chat/",
        json={
            "session_id": SESSION_ID,
            "query": question,
            "enable_web_search": False,
        },
        timeout=180,
    )
    latency_seconds = round(time.perf_counter() - start, 2)
    response.raise_for_status()

    data = response.json()
    trace_events = data.get("trace_events", [])
    route = [event.get("node_name") for event in trace_events]

    evidence = ""
    for event in trace_events:
        if event.get("node_name") == "rag_lookup":
            details = event.get("details", {})
            evidence = details.get("retrieved_context") or details.get("retrieved_content_summary", "")
            break

    return {
        "answer": data.get("response", ""),
        "route": route,
        "evidence": evidence,
        "latency_seconds": latency_seconds,
    }


def parse_judge_json(raw):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, flags=re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def judge_answer(question, evidence, answer):
    if not evidence.strip():
        return {
            "faithfulness": 1,
            "groundedness": 1,
            "answer_relevance": 1,
            "notes": "No retrieved RAG evidence was returned.",
        }

    prompt = f"""
Evaluate this RAG chatbot answer using only the retrieved evidence.

Score each metric from 1 to 5:
1 = very poor
5 = excellent

Metrics:
- faithfulness: The answer avoids claims unsupported by the retrieved evidence.
- groundedness: The answer clearly uses the retrieved evidence.
- answer_relevance: The answer directly addresses the question.

Question:
{question}

Retrieved evidence:
{evidence}

Answer:
{answer}

Return JSON only:
{{
  "faithfulness": 1,
  "groundedness": 1,
  "answer_relevance": 1,
  "notes": "short reason"
}}
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a strict RAG evaluation judge. Return valid JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    return parse_judge_json(response.choices[0].message.content)


def main():
    results = []
    for question in QUESTIONS:
        print(f"Evaluating: {question}")
        agent_result = ask_agent(question)
        judge_result = judge_answer(question, agent_result["evidence"], agent_result["answer"])

        results.append({
            "question": question,
            "answer": agent_result["answer"],
            "route": agent_result["route"],
            "retrieved_evidence": agent_result["evidence"],
            "latency_seconds": agent_result["latency_seconds"],
            "faithfulness": judge_result["faithfulness"],
            "groundedness": judge_result["groundedness"],
            "answer_relevance": judge_result["answer_relevance"],
            "judge_notes": judge_result["notes"],
        })

    summary = {
        "total_questions": len(results),
        "average_faithfulness": round(sum(r["faithfulness"] for r in results) / len(results), 2),
        "average_groundedness": round(sum(r["groundedness"] for r in results) / len(results), 2),
        "average_answer_relevance": round(sum(r["answer_relevance"] for r in results) / len(results), 2),
        "average_latency_seconds": round(sum(r["latency_seconds"] for r in results) / len(results), 2),
    }

    output = {"summary": summary, "results": results}

    with open("basic_eval_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print("\nEvaluation Summary")
    print(json.dumps(summary, indent=2))
    print("\nSaved results to basic_eval_results.json")


if __name__ == "__main__":
    main()
