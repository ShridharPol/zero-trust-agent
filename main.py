"""
Zero-Trust power grid anomaly detection pipeline.
Runs: signal batch → feature extraction → trust scoring → mitigation decision.
"""

import time
from dsp.signal_simulator import generate_batch
from dsp.feature_extractor import extract_features
from agents.trust_scorer import score_trust
from agents.mitigation import decide_mitigation

MOCK_MODE = True


def mock_score_trust(features):
    anomaly = features.get("anomaly_type", "none")
    severity = features.get("severity", "none")
    peak = features.get("peak_voltage", 0.0)
    thd = features.get("thd_percent", 0.0)
    freq_dev = features.get("frequency_deviation_hz", 0.0)
    rms = features.get("rms_voltage", 0.0)

    # High/extreme point anomalies -> REJECT
    if anomaly == "point" and severity == "high":
        return {"trust_score": 0.15, "reason": "Mock: high severity point anomaly", "prompt_version": "trust_scorer_v1"}
    # Medium point anomalies -> QUARANTINE
    if anomaly == "point" and severity == "medium":
        return {"trust_score": 0.35, "reason": "Mock: medium severity point anomaly", "prompt_version": "trust_scorer_v1"}
    # Trend anomalies -> QUARANTINE
    if anomaly == "trend":
        return {"trust_score": 0.50, "reason": "Mock: trend anomaly detected", "prompt_version": "trust_scorer_v1"}
    # Borderline cases: normal type but suspicious features
    if thd > 5.0 or freq_dev > 0.05 or rms > 0.72 or peak > 0.73:
        return {"trust_score": 0.55, "reason": "Mock: borderline features detected", "prompt_version": "trust_scorer_v1"}
    # Normal
    return {"trust_score": 0.95, "reason": "Mock: all features normal", "prompt_version": "trust_scorer_v1"}


def mock_decide_mitigation(trust_result):
    score = trust_result.get("trust_score", 0.5)
    if score >= 0.70:
        return {"decision": "ACCEPT", "explanation": "Mock: trust score above threshold", "prompt_version": "mitigation_v1"}
    elif score >= 0.30:
        return {"decision": "QUARANTINE", "explanation": "Mock: suspicious reading", "prompt_version": "mitigation_v1"}
    else:
        return {"decision": "REJECT", "explanation": "Mock: forced reject", "prompt_version": "mitigation_v1"}


def run_pipeline(n_readings=10):
    """
    Generate a batch of signals, run each through feature extraction,
    trust scoring, and mitigation; print per-reading summary and final stats.
    """
    if MOCK_MODE:
        print("WARNING: Running in MOCK MODE — no API calls will be made")
    # Generate batch and run pipeline on each reading
    readings = generate_batch(n_readings)
    decisions = []   # ACCEPT / QUARANTINE / REJECT
    anomaly_types = []  # anomaly_type from each reading

    for i, reading in enumerate(readings, start=1):
        # 1. Extract features
        features = extract_features(reading)
        # 2. Score trust, 3. Decide mitigation (no sleep between these two)
        if MOCK_MODE:
            trust_result = mock_score_trust(features)
            mitigation_result = mock_decide_mitigation(trust_result)
        else:
            trust_result = score_trust(features)
            mitigation_result = decide_mitigation(trust_result)

        anomaly = features.get("anomaly_type", "none")
        trust = trust_result.get("trust_score", 0.0)
        decision = mitigation_result.get("decision", "QUARANTINE")
        # 4. Print result
        print("Reading {} | anomaly: {} | trust: {:.2f} | decision: {}".format(
            i, anomaly, trust, decision
        ))

        decisions.append(decision)
        anomaly_types.append(anomaly)

        # 5. Sleep 30s before next reading so rate limit can reset (skip after last)
        if not MOCK_MODE and i < len(readings):
            time.sleep(30)

    # Summary: totals and counts
    print()
    print("--- Summary ---")
    print("Total readings processed: {}".format(len(readings)))
    print("Decisions: ACCEPT={}, QUARANTINE={}, REJECT={}".format(
        decisions.count("ACCEPT"),
        decisions.count("QUARANTINE"),
        decisions.count("REJECT"),
    ))
    for atype in ("none", "point", "trend"):
        print("Anomaly type '{}': {}".format(atype, anomaly_types.count(atype)))


if __name__ == "__main__":
    run_pipeline(n_readings=10)
