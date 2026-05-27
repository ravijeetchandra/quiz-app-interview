import asyncio
import json
import re
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

TOPIC_MCQ_ONLY_PROMPT = """Generate exactly {count} multiple-choice questions for a "{domain}" interview.
These should test general knowledge of {domain} concepts, common interview topics, and best practices.
No document is provided — generate questions based on standard {domain} knowledge.

Rules:
- Generate EXACTLY {count} MCQs. Not more, not less.
- Each MCQ must have 4 options (A, B, C, D) with the correct answer marked
- Do NOT include any long questions
- Cover a range of fundamental to intermediate topics in {domain}

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
"""

TOPIC_MCQ_WITH_LONG_PROMPT = """Generate exactly {count} multiple-choice questions AND exactly 2 long-form questions for a "{domain}" interview.
These should test general knowledge of {domain} concepts, common interview topics, and best practices.
No document is provided — generate questions based on standard {domain} knowledge.

Rules:
- Generate EXACTLY {count} MCQs. Not more, not less.
- Each MCQ must have 4 options (A, B, C, D) with the correct answer marked
- Generate EXACTLY 2 long-form questions that test deep analytical understanding
- Cover a range of fundamental to intermediate topics in {domain}

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
"""

RESUME_MCQ_ONLY_PROMPT = """Based on the following resume, generate exactly {count} multiple-choice questions for a "{domain}" interview.
The questions should test the candidate's knowledge of {domain} at a level appropriate for their experience and skills shown in the resume.

Rules:
- Generate EXACTLY {count} MCQs. Not more, not less.
- Each MCQ must have 4 options (A, B, C, D) with the correct answer marked
- Do NOT include any long questions
- Tailor difficulty to the candidate's apparent experience level from the resume
- Cover relevant {domain} topics that match their background

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

Resume:
{content}
"""

RESUME_MCQ_WITH_LONG_PROMPT = """Based on the following resume, generate exactly {count} multiple-choice questions AND exactly 2 long-form questions for a "{domain}" interview.
The questions should test the candidate's knowledge of {domain} at a level appropriate for their experience and skills shown in the resume.

Rules:
- Generate EXACTLY {count} MCQs. Not more, not less.
- Each MCQ must have 4 options (A, B, C, D) with the correct answer marked
- Generate EXACTLY 2 long-form questions that test deep analytical understanding
- Tailor difficulty to the candidate's apparent experience level from the resume
- Cover relevant {domain} topics that match their background

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

Resume:
{content}
"""

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

DOMAIN_CLASSIFICATION_PROMPT = """Given the following resume or document preview, determine which interview domain it best matches from this list: {domains}.

Analyze the skills, technologies, tools, and experience mentioned.
Return ONLY the exact domain name from the list. If unsure, return "Unknown".

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
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type((APIError, APITimeoutError, RateLimitError, APIConnectionError, json.JSONDecodeError)),
    before_sleep=lambda retry_state: print(f"LLM call failed (attempt {retry_state.attempt_number}), retrying..."),
    reraise=True,
)
async def _call_llm(prompt: str, temperature: float = 0.2) -> str:
    async with _llm_semaphore:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=4096,
        )
        content = (response.choices[0].message.content or "").strip()
        if not content:
            raise json.JSONDecodeError("LLM returned empty response", "", 0)
        return content


def _extract_json(text: str):
    text = text.strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
    if match:
        text = match.group(1)

    if not text:
        raise json.JSONDecodeError("Empty content after extraction", "", 0)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print(f"[LLM RAW] Response snippet: {text[:800]}")
        raise


async def classify_domain(text: str, domain_list: List[str]) -> str:
    prompt = DOMAIN_CLASSIFICATION_PROMPT.format(
        domains=", ".join(domain_list),
        preview=text[:500],
    )
    response_text = await _call_llm(prompt)
    result = response_text.strip()
    return result if result in domain_list else "Unknown"


async def generate_quiz_content(content: str, domain: str, count: int, has_long: bool, source_type: str = "file"):
    import random
    variation = random.randint(1, 99999)

    if domain.lower() == "general / other":
        if source_type == "resume":
            domain_label = "the candidate's field as shown in their resume"
        else:
            domain_label = "any field"
    else:
        domain_label = domain

    seed_line = f"\n(Variation: {variation} — generate different questions than previous attempts, covering different topics and aspects.)"

    if source_type == "topic":
        prompt = (TOPIC_MCQ_WITH_LONG_PROMPT if has_long else TOPIC_MCQ_ONLY_PROMPT).format(
            domain=domain_label,
            count=count,
        ) + seed_line
    elif source_type == "resume":
        prompt = (RESUME_MCQ_WITH_LONG_PROMPT if has_long else RESUME_MCQ_ONLY_PROMPT).format(
            content=content[:8000],
            domain=domain_label,
            count=count,
        ) + seed_line
    else:
        prompt = (MCQ_WITH_LONG_PROMPT if has_long else MCQ_ONLY_PROMPT).format(
            content=content[:8000],
            domain=domain_label,
            count=count,
        ) + seed_line

    print(f"[PROMPT_DEBUG] Prompt length={len(prompt)}, first 300 chars: {prompt[:300]!r}")
    response_text = await _call_llm(prompt, temperature=0.8)
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
