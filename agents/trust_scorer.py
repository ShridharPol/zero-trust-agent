"""
Agent 1 in the Zero-Trust pipeline. Takes DSP features and returns a trust score
using Google Gemini.
"""

import os
import json
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

from config.prompts import TRUST_SCORER_PROMPT_V1
from langsmith import traceable

# Setup: load env, create client at module level (initialized once)
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


@traceable(name="trust_scorer", run_type="llm")
def score_trust(features: dict) -> dict:
    """
    Score the trustworthiness of a sensor reading from its DSP features.
    Returns dict with trust_score (float), reason (str), prompt_version (str).
    """
    # Build user message: one line per feature, clean key: value
    lines = [
        "rms_voltage: {}".format(features.get("rms_voltage", "")),
        "thd_percent: {}".format(features.get("thd_percent", "")),
        "frequency_deviation_hz: {}".format(features.get("frequency_deviation_hz", "")),
        "peak_voltage: {}".format(features.get("peak_voltage", "")),
        "anomaly_type: {}".format(features.get("anomaly_type", "")),
        "severity: {}".format(features.get("severity", "")),
    ]
    user_message = "\n".join(lines)

    try:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash-lite",
                    config=types.GenerateContentConfig(
                        system_instruction=TRUST_SCORER_PROMPT_V1
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
        # Strip markdown code fence if present
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        data = json.loads(text)
        trust_score = float(data.get("trust_score", 0.5))
        reason = str(data.get("reason", ""))
        return {
            "trust_score": trust_score,
            "reason": reason,
            "prompt_version": "trust_scorer_v1",
        }
    except (json.JSONDecodeError, ValueError, TypeError, AttributeError):
        return {
            "trust_score": 0.5,
            "reason": "parse error",
            "prompt_version": "trust_scorer_v1",
        }


if __name__ == "__main__":
    # Normal signal: in-range features, no anomaly
    normal_features = {
        "rms_voltage": 0.7071,
        "thd_percent": 0.0,
        "frequency_deviation_hz": 0.0083,
        "peak_voltage": 0.7071,
        "anomaly_type": "none",
        "severity": "none",
    }
    print("Normal signal:")
    print(score_trust(normal_features))
    print()

    # Point anomaly: e.g. spike, out-of-range or anomaly_type point
    point_anomaly_features = {
        "rms_voltage": 0.82,
        "thd_percent": 2.1,
        "frequency_deviation_hz": 0.12,
        "peak_voltage": 0.95,
        "anomaly_type": "point",
        "severity": "medium",
    }
    print("Point anomaly signal:")
    print(score_trust(point_anomaly_features))
