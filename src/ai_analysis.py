import json
import os

from groq import Groq

MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """You are a security reviewer helping a human recruiter assess \
a candidate's resume. You will be given the resume's extracted text and a list \
of findings from two deterministic detectors: one that matches known \
manipulative phrases, and one that flags text hidden via font size, color or \
off-page position.

Your job is NOT to repeat or re-list the findings. Your job is to reason about \
them together and answer three things, as JSON:

1. "risk_level": one of "none", "low", "medium", "high"
2. "reasoning": 2-3 sentences explaining why, referencing the specific findings
3. "recommendation": a short, actionable next step for the human reviewer. \
You must NEVER recommend rejecting, disqualifying or penalizing the \
candidate: hiring decisions belong to humans. Only recommend reviewing \
specific evidence, such as opening the PDF and checking the flagged text.

Respond with ONLY a JSON object with exactly these three keys. No markdown, no \
extra text before or after the JSON."""


def build_user_message(extracted_text, findings):
    return (
        "Resume text (truncated to 4000 chars):\n"
        f"{extracted_text[:4000]}\n\n"
        "Detector findings (JSON):\n"
        f"{json.dumps(findings, indent=2, ensure_ascii=False)}"
    )


def analyze_with_ai(extracted_text, findings, client=None):
    if not findings:
        return {
            "risk_level": "none",
            "reasoning": "No suspicious patterns or hidden text were detected "
            "by the deterministic detectors, so there is nothing for the AI "
            "reviewer to assess.",
            "recommendation": "No action needed.",
        }

    if client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return {
                "risk_level": "unknown",
                "reasoning": "GROQ_API_KEY is not set, so the AI reviewer "
                "could not run.",
                "recommendation": "Set the GROQ_API_KEY environment "
                "variable to enable AI-assisted analysis.",
            }
        client = Groq(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=500,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": build_user_message(extracted_text, findings),
                },
            ],
        )
        raw_text = response.choices[0].message.content
        return json.loads(raw_text)
    except json.JSONDecodeError:
        return {
            "risk_level": "unknown",
            "reasoning": "The AI reviewer's response could not be parsed as "
            "JSON.",
            "recommendation": "Review the findings manually.",
        }
    except Exception as exc:
        return {
            "risk_level": "unknown",
            "reasoning": f"AI-assisted analysis failed: {exc}",
            "recommendation": "Review the findings manually.",
        }