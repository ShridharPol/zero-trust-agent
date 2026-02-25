"""
Agent 2 in the Zero-Trust pipeline. Takes the trust score from Agent 1 and
makes a final ACCEPT / QUARANTINE / REJECT decision using Google Gemini.
"""

import os
import json
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

from config.prompts import MITIGATION_PROMPT_V1
from langsmith import traceable

# Setup: load env, create client at module level (initialized once)
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


@traceable(name="mitigation_agent", run_type="llm")
def decide_mitigation(trust_result: dict) -> dict:
    """
    Decide mitigation action from trust scorer output.
    Returns dict with decision (ACCEPT/QUARANTINE/REJECT), explanation, prompt_version.
    """
    trust_score = trust_result.get("trust_score", 0.0)
    reason = trust_result.get("reason", "")
    user_message = "trust_score: {}\nreason: {}".format(trust_score, reason)

    try:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash-lite",
                    config=types.GenerateContentConfig(
                        system_instruction=MITIGATION_PROMPT_V1
                    ),
                    contents=user_message,
                )
                break
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    wait_time = 15 * (attempt + 1)
                    print(f"Rate limit hit, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    if attempt == max_retries - 1:
                        raise
                else:
                    raise
        text = (response.text or "").strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        data = json.loads(text)
        decision = str(data.get("decision", "QUARANTINE")).strip().upper()
        explanation = str(data.get("explanation", ""))
        # Safety net: trust_score < 0.30 always REJECT
        if trust_score < 0.30:
            decision = "REJECT"
            explanation = "Forced REJECT: trust_score below 0.30 threshold."
        return {
            "decision": decision,
            "explanation": explanation,
            "prompt_version": "mitigation_v1",
        }
    except (json.JSONDecodeError, ValueError, TypeError, AttributeError):
        return {
            "decision": "QUARANTINE",
            "explanation": "parse error",
            "prompt_version": "mitigation_v1",
        }


if __name__ == "__main__":
    # High trust
    high = {"trust_score": 0.95, "reason": "all features normal", "prompt_version": "trust_scorer_v1"}
    print("High trust (0.95):")
    print(decide_mitigation(high))
    print()

    # Medium trust
    medium = {"trust_score": 0.45, "reason": "slight voltage deviation detected", "prompt_version": "trust_scorer_v1"}
    print("Medium trust (0.45):")
    print(decide_mitigation(medium))
    print()

    # Low trust
    low = {"trust_score": 0.15, "reason": "severe point anomaly detected", "prompt_version": "trust_scorer_v1"}
    print("Low trust (0.15):")
    print(decide_mitigation(low))
