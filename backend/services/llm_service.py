import asyncio
import json
from typing import List

from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError, APIConnectionError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import settings

client = AsyncOpenAI(
    api_key=settings.groq_api_key,
    base_url="https://api.groq.com/openai/v1",
    timeout=60.0,
)

MODEL = "llama-3.1-8b-instant"

_llm_semaphore = asyncio.Semaphore(5)

MCQ_ONLY_PROMPT = """Based on the document content below, generate exactly {count} multiple-choice questions for a "{domain}" interview.

Rules:
- Generate EXACTLY {count} MCQs. Not more, not less.
- Each MCQ must have 4 options (A, B, C, D) with the correct answer marked
- Do NOT include any long questions
- Break document into 3-6 topic sections

Return ONLY this JSON (no other text):
{{
  "mcq_questions": [
    {{
      "question": "...",
      "options": ["A option", "B option", "C option", "D option"],
      "correct_answer": "correct option text",
      "section": "Topic name"
    }}
  ],
  "long_questions": [],
  "sections": ["Section 1", "Section 2"]
}}

Document:
{content}
"""

MCQ_WITH_LONG_PROMPT = """Based on the document content below, generate {count} multiple-choice questions AND exactly 2 long-form questions for a "{domain}" interview.

Rules:
- Generate EXACTLY {count} MCQs. Not more, not less.
- Each MCQ must have 4 options (A, B, C, D) with the correct answer marked
- Generate EXACTLY 2 long-form questions that test deep analytical understanding
- Break document into 3-6 topic sections

Return ONLY this JSON (no other text):
{{
  "mcq_questions": [
    {{
      "question": "...",
      "options": ["A option", "B option", "C option", "D option"],
      "correct_answer": "correct option text",
      "section": "Topic name"
    }}
  ],
  "long_questions": [
    {{
      "question": "Long question testing deep understanding...",
      "section": "Topic name"
    }}
  ],
  "sections": ["Section 1", "Section 2"]
}}

Document:
{content}
"""

DOMAIN_CLASSIFICATION_PROMPT = """Return one domain from: {domains}
If unsure, return "Unknown".
Preview: {preview}
"""

LONG_ANSWER_EVAL_PROMPT = """Evaluate this candidate's answer for an interview question. Score 1-10.

Document context: {context}
Question: {question}
Answer: {answer}

Return ONLY valid JSON:
{{
    "score": <integer 1-10>,
    "strengths": ["strength 1", "strength 2"],
    "weaknesses": ["weakness 1", "weakness 2"],
    "model_answer": "A comprehensive model answer"
}}
"""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((APIError, APITimeoutError, RateLimitError, APIConnectionError)),
    reraise=True,
)
async def _call_llm(prompt: str) -> str:
    async with _llm_semaphore:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=2048,
        )
        return response.choices[0].message.content or ""


def _extract_json(text: str):
    text = text.strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)


async def classify_domain(text: str, domain_list: List[str]) -> str:
    prompt = DOMAIN_CLASSIFICATION_PROMPT.format(
        domains=", ".join(domain_list),
        preview=text[:500],
    )
    response_text = await _call_llm(prompt)
    result = response_text.strip()
    return result if result in domain_list else "Unknown"


async def generate_quiz_content(content: str, domain: str, count: int, has_long: bool):
    domain_label = "any field" if domain.lower() == "general / other" else domain
    prompt = (MCQ_WITH_LONG_PROMPT if has_long else MCQ_ONLY_PROMPT).format(
        content=content[:8000],
        domain=domain_label,
        count=count,
    )
    response_text = await _call_llm(prompt)
    data = _extract_json(response_text)

    mcqs = data.get("mcq_questions", [])
    longs = data.get("long_questions", []) if has_long else []

    return {
        "mcq_questions": mcqs[:count],
        "long_questions": longs[:2],
        "sections": data.get("sections", ["General"]),
    }


async def evaluate_long_answer(question: str, answer: str, context: str) -> dict:
    prompt = LONG_ANSWER_EVAL_PROMPT.format(
        question=question,
        answer=answer,
        context=context[:3000],
    )
    response_text = await _call_llm(prompt)
    return _extract_json(response_text)
