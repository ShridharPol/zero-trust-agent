# Zero-Trust AI Agent

A zero-trust pipeline for power grid PMU (Phasor Measurement Unit) anomaly detection using DSP features and LLM-based trust scoring.

---

## Project Overview

This project simulates IEEE C37.118–style PMU sensor data and runs it through a two-agent pipeline: a **Trust Scorer** (Gemini) assigns a trust score (0.0–1.0) from extracted DSP features, and a **Mitigation Agent** (Gemini) decides whether to **ACCEPT**, **QUARANTINE**, or **REJECT** each reading. The design follows zero-trust principles: every reading is evaluated before being treated as trustworthy.

---

## Architecture

```
PMU Sensor Signal (Voltage + Frequency)
        ↓
DSP Layer: Bandpass Filter → FFT → Feature Extraction
(RMS, THD, Frequency Deviation, Peak Voltage)
        ↓
Agent 1 — Trust Scorer (Gemini 2.5 Flash)
Scores reading 0.0 to 1.0
        ↓
Agent 2 — Mitigation Agent (Gemini 2.5 Flash)
ACCEPT / QUARANTINE / REJECT
        ↓
LangSmith Tracing + Evaluation Suite + CI/CD
```

---

## Tech Stack

| Purpose | Tool |
|--------|------|
| LLM | Google Gemini (google-genai) |
| Tracing | LangSmith |
| DSP / Math | NumPy, SciPy |
| Visualization | Matplotlib |
| Config | python-dotenv |

---

## Project Structure

```
Zero_Trust_Agent/
├── .github/
│   └── workflows/
│       └── eval_ci.yml      # CI: run evals on push/PR to main
├── agents/
│   ├── trust_scorer.py      # Agent 1: feature → trust score
│   └── mitigation.py        # Agent 2: trust result → decision
├── config/
│   └── prompts.py           # Versioned LLM prompts
├── dsp/
│   ├── signal_simulator.py  # PMU-style signal generation
│   ├── feature_extractor.py # RMS, THD, freq deviation, peak
│   └── visualizer.py        # Plotting utilities
├── evals/
│   ├── test_cases.json      # 25 hand-crafted test cases
│   └── run_evals.py         # Run suite, report score
├── main.py                  # Pipeline entrypoint
├── Dockerfile
├── requirements.txt
└── .env                     # API keys (not committed)
```

---

## Getting Started

1. **Clone the repo**
   ```bash
   git clone <repo-url>
   cd Zero_Trust_Agent
   ```

2. **Create and activate a virtual environment**
   ```bash
   py -3.12 -m venv venv
   # Windows: venv\Scripts\activate
   # macOS/Linux: source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file** with:
   - `GEMINI_API_KEY`
   - `LANGSMITH_API_KEY`
   - `LANGSMITH_PROJECT` (e.g. `zero-trust-agent`)
   - `LANGSMITH_TRACING_V2=true`

5. **Run the pipeline**
   ```bash
   python main.py
   ```

---

## Running with Docker

```bash
docker build -t zero-trust-agent .
docker run --env-file .env zero-trust-agent
```

---

## Running Evaluations

```bash
python evals/run_evals.py
```

The suite runs 25 test cases (normal, point anomaly, trend anomaly, borderline). The script prints pass/fail per case and a final **Score: X/25 (Y%)**. The run **passes** only if the score is **≥ 80%**; otherwise the process exits with code 1 for CI.

---

## CI/CD

GitHub Actions runs the evaluation suite on every **push** and **pull_request** to `main`. The workflow checks out the repo, sets up Python 3.12, installs dependencies, and runs `python evals/run_evals.py`. If the score drops below 80%, the job fails so that regressions are caught before merge.

---

## MLOps Features

- **LangSmith tracing** — Trust Scorer and Mitigation Agent runs are traced for debugging and monitoring.
- **Prompt versioning** — All LLM prompts live in `config/prompts.py` with version tags (e.g. `trust_scorer_v1`, `mitigation_v1`).
- **Evaluation suite** — 25 hand-crafted cases with expected decisions; run locally or in CI.
- **CI/CD** — Eval suite runs on every push/PR to main; fail if score &lt; 80%.
- **Docker** — Single Dockerfile for consistent build and run.

---

## Dataset

The pipeline uses **simulated** PMU data aligned with **IEEE C37.118** (50 Hz nominal, per-unit voltage, 50 samples per reading). The simulator in `dsp/signal_simulator.py` generates normal sine waves plus **point anomalies** (single-sample spikes) and **trend anomalies** (voltage drift). Batches are randomly mixed (~40% normal, ~35% point, ~25% trend) for training and evaluation.

---

## Anomaly Types

| Type | Description | Expected decision |
|------|-------------|-------------------|
| **none** | Clean 50 Hz signal, in-range RMS/THD/freq | ACCEPT |
| **point** | Single-sample spike (e.g. 1.3–1.5 pu); severity medium/high | QUARANTINE or REJECT |
| **trend** | Gradual voltage drift over the window | QUARANTINE |

---

*Zero-Trust Agent — Power Grid Anomaly Detection Pipeline*
