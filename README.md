# ⚖️ DHARITRI
### Fairness Unit Testing Infrastructure for AI Systems

## 🧠 Problem Statement

AI systems are deployed everywhere — hiring, lending, college admissions, healthcare triage. They are tested rigorously for **accuracy** and **speed**. They are **almost never tested for fairness**.

The result:

- A resume named *Rahul Sharma* and one named *Razia Ansari* — identical skills, identical experience — can receive fundamentally different scores from the same AI hiring tool.
- A candidate from *IIT Bombay* and one from *Sunrise Institute of Technology* — same projects, same years of work — get treated differently, not because of merit, but because of the text a model was trained on.
- There is **no standard tooling** for developers to catch this before deployment.
- Existing academic bias auditing tools are research-heavy, one-off studies — not usable in a real development workflow.

Developers assume their models are fair. They have no way to verify it.

---

## 💡 Solution

**DHARITRI** is an **API-first fairness testing framework** that lets any developer audit their AI system for identity sensitivity — using controlled experiments and rigorous statistical validation — **in under 10 minutes**.

Instead of asking: *"Is this AI biased?"*
We ask: *"Does the output change when only an identity signal changes — and nothing else?"*

DHARITRI works on **any model** — a logistic regression, a HuggingFace classifier, a GPT prompt, or any external REST endpoint. You send the model. We run the experiments. We return statistically validated results.

**Key differentiator:** DHARITRI is not a one-off study. It is **repeatable, automated infrastructure** — the fairness equivalent of a unit test suite.

---

## ⚙️ How It Works

```
POST /audit
```

You provide a base candidate text and choose an identity variable to test. DHARITRI generates paired samples where **only that one variable changes** — names, college, city, or graduation year — and scores both groups through your model.

### Example Request

```json
{
  "target": {
    "type": "seeded"
  },
  "base_input": "Software engineer with 4 years of Python and Django experience. Delivered 3 production microservices.",
  "identity_variable": "gender",
  "sample_size": 50
}
```

### Example Response

```json
{
  "identity_variable": "gender",
  "description": "Male-coded names vs Female-coded names",
  "iss_score": 0.2408,
  "p_value": 0.001,
  "confidence_interval": [9.15, 15.31],
  "verdict": "strong_identity_sensitivity_detected",
  "mean_score_group_a": 53.8,
  "mean_score_group_b": 41.7,
  "n_samples_per_group": 50
}
```

### Supported Target Types

| Type | Description |
|------|-------------|
| `seeded` | Local logistic regression with deliberately planted bias (ground truth validation) |
| `huggingface` | Any HuggingFace text-classification model loaded directly |
| `openai` | GPT-based hiring evaluation via structured prompt |
| `api` | Any external REST endpoint that accepts text and returns a score |

---

## 🔬 Scientific Framework

### Controlled Identity Testing

Every experiment isolates exactly one identity variable. Everything else — skills, experience, project descriptions, job titles — is held constant across both groups.

| Experiment | Signal Changed | Example |
|------------|---------------|---------|
| Gender | Candidate name | Rahul Sharma → Priya Sharma |
| Caste / Religion | Candidate name | Rajesh Sharma → Razia Ansari |
| College tier | Institution name | IIT Bombay → Sunrise Institute of Technology |
| Location | City | Mumbai → Gorakhpur |
| Age | Graduation year | 2020 → 2003 |

One variable per experiment. Never mixed. This is the entire scientific foundation.

### Identity Sensitivity Score (ISS)

```
ISS = |mean(Score_A) − mean(Score_B)| / mean(Score_A ∪ Score_B)
```

| ISS value | Interpretation |
|-----------|----------------|
| ISS ≈ 0 | No identity sensitivity detected |
| ISS 0.05–0.15 | Moderate sensitivity detected |
| ISS > 0.15 | Strong identity sensitivity — action required |

### Statistical Validation (Three-Layer)

**Layer 1 — Permutation Test (1000 shuffles)**
Shuffles identity labels 1000 times. If the real difference is larger than 95% of shuffled results → `p < 0.05` → result is not due to chance.

**Layer 2 — Bootstrap Confidence Interval (500 resamples)**
Resamples scores 500 times to build a 95% CI on `mean_A − mean_B`. If the interval excludes zero → the effect is real and stable.

**Layer 3 — Verdict Logic**
Combines ISS, p-value, and CI into a human-readable verdict:

| Verdict | Meaning |
|---------|---------|
| `no_significant_difference` | p ≥ 0.05 — no detectable bias |
| `marginal_sensitivity` | p < 0.05 but CI crosses zero — inconclusive |
| `low_sensitivity_detected` | ISS < 0.05, significant |
| `identity_sensitivity_detected` | ISS 0.05–0.15, significant |
| `strong_identity_sensitivity_detected` | ISS ≥ 0.15, significant |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│   Screen 1: Audit Dashboard   Screen 2: API Simulator    │
│   (Chart.js + ResultTable)    (Postman-style JSON UI)    │
└───────────────────────┬─────────────────────────────────┘
                        │  POST /audit
                        ▼
┌─────────────────────────────────────────────────────────┐
│               REST API  — app.py                         │
│         FastAPI (primary)  /  Flask (fallback)           │
│         /audit   /experiments   /health                  │
└──────┬────────────────┬────────────────┬────────────────┘
       │                │                │
       ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐
│    Test Case │ │  Evaluator   │ │  Statistical Engine   │
│  Generator   │ │   Wrapper    │ │                       │
│              │ │              │ │  • ISS Score          │
│ Generates    │ │ • seeded     │ │  • Permutation Test   │
│ controlled   │ │ • HuggingFace│ │    (1000 shuffles)    │
│ identity     │ │ • OpenAI     │ │  • Bootstrap CI       │
│ variant      │ │ • REST API   │ │    (500 resamples)    │
│ pairs        │ │              │ │  • Verdict logic      │
└──────────────┘ └──────────────┘ └──────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│                  models/seeded_bias.py                   │
│   TF-IDF + Logistic Regression with deliberately         │
│   planted bias across 5 axes (ground truth validation)   │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
dharitri/
├── backend/
│   ├── app.py                        # FastAPI / Flask entry point
│   ├── audit_engine/
│   │   ├── __init__.py
│   │   ├── test_generator.py         # Generates controlled identity-variant pairs
│   │   ├── evaluator.py              # Model-agnostic scoring wrapper (4 target types)
│   │   └── statistics.py             # ISS + permutation test + bootstrap CI
│   ├── models/
│   │   ├── __init__.py
│   │   ├── seeded_bias.py            # Ground truth model with planted bias
│   │   └── seeded_model.joblib       # Trained model artifact (auto-generated)
│   └── requirements.txt
│
├── frontend/
│   ├── package.json
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── index.js                  # React entry point
│       ├── App.js                    # Root component + routing (2 screens)
│       ├── components/
│       │   ├── AuditForm.js          # Audit input form with all target types
│       │   ├── ChartView.js          # Chart.js score comparison bar chart
│       │   └── ResultTable.js        # Statistical output with CI visualisation
│       ├── styles/
│       │   └── App.css               # Dark-field design system (DM Mono + Syne)
│       └── utils/
│           └── api.js                # All backend HTTP calls in one place
│
├── .env                              # API keys — never commit this
├── .gitignore
└── README.md
```

---

## 🛠️ Tech Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.10+ | Primary language |
| FastAPI | 0.110+ | REST API framework (primary) |
| Flask | 3.0+ | REST API framework (fallback) |
| scikit-learn | 1.3+ | TF-IDF vectoriser + Logistic Regression |
| scipy | 1.11+ | Statistical functions |
| numpy | 1.24+ | Array math for permutation & bootstrap |
| pandas | 2.0+ | Training data corpus |
| joblib | 1.3+ | Model serialisation |
| uvicorn | 0.27+ | ASGI server for FastAPI |
| python-dotenv | 1.0+ | `.env` file loading |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18 | UI framework |
| React Router | 6 | Two-screen navigation |
| Chart.js + react-chartjs-2 | 4 | Score comparison bar chart |
| Axios | 1.6+ | HTTP client |
| react-syntax-highlighter | 15+ | JSON display in API Simulator |

---

## 📦 Installation & Local Setup

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- npm 9 or higher
- Git

### Step 1 — Clone the repository

```bash
git clone https://github.com/Sneha03967/Dharitri.git
cd Dharitri
```

### Step 2 — Set up environment variables

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your keys
nano .env
```

`.env` contents:
```
HF_API_KEY=your_huggingface_token_here
OPENAI_API_KEY=your_openai_key_here
PORT=8000
```

> ⚠️ Never commit the real `.env` to version control. It is already in `.gitignore`.

### Step 3 — Backend setup

```bash
cd backend

# Create a virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate           # Windows

# Install all dependencies
pip install -r requirements.txt
```

### Step 4 — Train the seeded model (first time only)

```bash
# From dharitri/backend/ with venv active:
python3 models/seeded_bias.py
```

Expected output:
```
🌱  Building multi-axis seeded bias training data …
📊  Seeded bias statistics (training corpus)
────────────────────────────────────────────────
  Gender   — Male  hire rate : 57.76%
             Female hire rate : 37.82%
  College  — IIT/IIM    hire rate : 53.77%
  College  — Unknown    hire rate : 29.89%
  Location — Metro      hire rate : 53.31%
  Location — Tier-3     hire rate : 42.05%
────────────────────────────────────────────────
✅  Model trained on 800 samples.
💾  Model saved → models/seeded_model.joblib

🧪  Self-test — bias detection by axis
────────────────────────────────────────────────────
  ✅  gender                    A=54.8  B=46.1  gap=+8.7
  ✅  caste_hindu_muslim        A=57.8  B=48.2  gap=+9.6
  ✅  caste_upper_sc            A=57.8  B=46.7  gap=+11.1
  ✅  college_iit_unknown       A=54.4  B=36.3  gap=+18.0
  ✅  location_metro_tier3      A=54.7  B=49.3  gap=+5.4
  ✅  age_young_senior          A=53.6  B=47.7  gap=+6.0

  Overall validation: ✅ PASSED
```

### Step 5 — Frontend setup

```bash
# In a new terminal, from the project root:
cd frontend
npm install
```

---

## ▶️ Running the Project

### Start the backend

```bash
cd backend
source venv/bin/activate

# With FastAPI (recommended — auto-detected if installed)
python3 app.py
# Server starts at http://localhost:8000

# Or explicitly with uvicorn
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Start the frontend

```bash
cd frontend
npm start
# Opens http://localhost:3000 automatically
# CRA proxy routes all /audit, /experiments, /health calls to backend:8000
```

### Verify everything is running

```bash
# Health check
curl http://localhost:8000/health
# → {"status": "ok", "service": "DHARITRI"}

# List available experiments
curl http://localhost:8000/experiments

# Run a gender bias audit
curl -X POST http://localhost:8000/audit \
  -H "Content-Type: application/json" \
  -d '{
    "target": {"type": "seeded"},
    "base_input": "Software engineer with 4 years of Python and Django experience.",
    "identity_variable": "gender",
    "sample_size": 50
  }'

# Run a caste bias audit
curl -X POST http://localhost:8000/audit \
  -H "Content-Type: application/json" \
  -d '{
    "target": {"type": "seeded"},
    "base_input": "Software engineer with 4 years of Python and Django experience.",
    "identity_variable": "caste_hindu_muslim",
    "sample_size": 50
  }'

# Run a college tier audit
curl -X POST http://localhost:8000/audit \
  -H "Content-Type: application/json" \
  -d '{
    "target": {"type": "seeded"},
    "base_input": "Software engineer with 4 years of Python and Django experience.",
    "identity_variable": "college_iit_unknown",
    "sample_size": 50
  }'
```

### Run the full demo script (all 8 experiments at once)

```bash
cd backend && source venv/bin/activate

python3 - << 'EOF'
import sys; sys.path.insert(0, '.')
from audit_engine.test_generator import generate_test_cases
from audit_engine.evaluator import evaluate_batch
from audit_engine.statistics import compute_full_report

base   = "Software engineer with 4 years of Python and Django experience."
target = {"type": "seeded"}
exps   = [
    "gender", "caste_hindu_muslim", "caste_upper_sc", "caste_upper_obc",
    "college_iit_unknown", "college_iit_state",
    "location_metro_tier3", "age_young_senior"
]

print(f"{'Experiment':<28} {'ISS':>8} {'p-val':>8} {'Gap':>8}  Verdict")
print("-" * 95)
for exp in exps:
    td = generate_test_cases(base, exp, 50)
    a  = evaluate_batch([p["input"] for p in td["pairs"] if p["group"]=="A"], target)
    b  = evaluate_batch([p["input"] for p in td["pairs"] if p["group"]=="B"], target)
    r  = compute_full_report(a, b)
    print(f"{exp:<28} {r['iss_score']:>8.4f} {r['p_value']:>8.4f} "
          f"{r['mean_score_group_a']-r['mean_score_group_b']:>+8.2f}  {r['verdict']}")
EOF
```

---

## 📡 API Reference

### `GET /health`
Returns server status.
```json
{ "status": "ok", "service": "DHARITRI" }
```

### `GET /experiments`
Returns all supported identity experiment types.
```json
{
  "experiments": [
    { "identity_variable": "gender",             "description": "Male-coded names vs Female-coded names" },
    { "identity_variable": "caste_hindu_muslim",  "description": "Upper-caste Hindu names vs Muslim names" },
    { "identity_variable": "caste_upper_sc",      "description": "Upper-caste names vs SC/ST names" },
    { "identity_variable": "caste_upper_obc",     "description": "Upper-caste names vs OBC names" },
    { "identity_variable": "college_iit_unknown", "description": "IIT/IIM vs unknown college" },
    { "identity_variable": "college_iit_state",   "description": "IIT/IIM vs state university" },
    { "identity_variable": "location_metro_tier3","description": "Metro city vs Tier-3 city" },
    { "identity_variable": "age_young_senior",    "description": "Young candidate (24-28) vs Senior (38-43)" }
  ]
}
```

### `POST /audit`

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `target.type` | string | Yes | `seeded` \| `huggingface` \| `openai` \| `api` |
| `target.model_name` | string | HuggingFace only | e.g. `typeform/distilbert-base-uncased-mnli` |
| `target.endpoint` | string | API only | URL of the external model endpoint |
| `target.api_key` | string | API / OpenAI | Bearer token for the endpoint |
| `base_input` | string | Yes | Resume or candidate text |
| `identity_variable` | string | Yes | One key from `/experiments` |
| `sample_size` | int | No | 10–200, default 50 |

**Response:**

| Field | Type | Description |
|-------|------|-------------|
| `iss_score` | float | Identity Sensitivity Score (0 = no bias) |
| `p_value` | float | Permutation test p-value |
| `confidence_interval` | [float, float] | 95% bootstrap CI on score gap |
| `verdict` | string | Human-readable verdict |
| `mean_score_group_a` | float | Average score for privileged group (0–100) |
| `mean_score_group_b` | float | Average score for marginalised group (0–100) |
| `n_samples_per_group` | int | Number of samples scored per group |
| `description` | string | Plain-language description of the experiment |

---

## 🎯 Bias Axes Tested

DHARITRI tests the five dimensions that Indian society most commonly uses to discriminate between equally-qualified candidates:

| Axis | What changes | Planted penalty |
|------|-------------|-----------------|
| **Gender** | Candidate name (male → female coded) | −12 pts |
| **Age** | Graduation year (2020 → 2003) | −10 pts |
| **Caste / Religion** | Candidate name (upper-caste → Muslim) | −14 pts |
| **Caste / Religion** | Candidate name (upper-caste → SC/ST) | −10 pts |
| **Location** | City (Mumbai → Gorakhpur) | −8 pts |
| **College tier** | Institution (IIT Bombay → unknown college) | −15 pts |




---

## ⚠️ What DHARITRI Does NOT Do

| We don't do this | Why |
|-----------------|-----|
| Scrape live platforms (LinkedIn, Naukri) | ToS violation, unpredictable and irreproducible results |
| Infer caste from surnames alone | Too many confounds — weakens the methodology |
| Claim to produce legal evidence of discrimination | We produce audit signals for developers, not legal proof |
| Make India-wide bias claims | We prototype the methodology — not the social conclusion |
| Mix identity variables in a single test | Would confound results — one variable per experiment always |

---

## 🎤 Pitch

> *"Most teams show that AI can be biased.*
> *We built the system that lets any developer test it themselves.*
>
> *DHARITRI is a fairness unit testing API for AI systems.*
> *You send your model. We run controlled identity experiments. We return statistically validated results.*
>
> *We validated it on a model with known planted bias — and it found that bias at p = 0.001 across all six axes.*
> *Then we applied it to real systems.*
>
> *We're not making claims. We're enabling measurement."*

---

*DHARITRI — Fairness Unit Testing Framework — Google Hackathon 2026*