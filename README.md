# 🌍 DHARITRI
### Fairness Unit Testing Infrastructure for AI Systems

> *"Developers have unit tests for code. Now they have fairness tests for AI."*

---

## 🧠 The Problem

AI systems are deployed everywhere — hiring, lending, admissions, healthcare. They are tested for accuracy and speed. They are **almost never tested for fairness.**

- No standard way to test fairness before deployment
- Developers rely on assumptions instead of measurement
- Existing tools are research-heavy and not usable in real workflows

---

## 💡 The Solution

**DHARITRI** is an API-first fairness testing framework that allows any developer to audit their AI system for identity sensitivity — using controlled experiments and statistical validation — in under 10 minutes.

Instead of asking: *"Is this AI biased?"*  
We ask: *"Does the output change when only identity signals change?"*

---

## ⚙️ How It Works

```
POST /audit
```

### Input

```json
{
  "target": {
    "type": "api",
    "endpoint": "https://your-model-api.com/predict",
    "api_key": "your-key-here"
  },
  "base_input": "candidate resume text here",
  "identity_variable": "gender",
  "sample_size": 50
}
```

### Supported Target Types

| Type | Description |
|------|-------------|
| `api` | Any deployed model endpoint |
| `huggingface` | Direct HuggingFace model loading |
| `openai` | LLM-based evaluation |

### Output

```json
{
  "iss_score": 0.082,
  "p_value": 0.031,
  "confidence_interval": [0.041, 0.124],
  "verdict": "identity_sensitivity_detected"
}
```

---

## 🔬 Scientific Framework

### Controlled Identity Testing

Keep everything constant. Change **only one variable** per experiment:

| Experiment | Signal | Example |
|------------|--------|---------|
| A | Gender | Rahul Sharma → Priya Sharma |
| B | Cultural | Rahul Sharma → Razia Ansari |
| C | Regional | IIT Delhi → NIT Patna |

One variable per experiment. Never mixed. This is the entire scientific foundation.

### Identity Sensitivity Score (ISS)

```
ISS = |Score_A - Score_B| / Score_avg
```

- `ISS ≈ 0` → No identity sensitivity detected  
- `ISS ↑` → Output sensitive to identity signal

### Statistical Validation

**Permutation Test**  
Shuffles identity labels 1000 times. If real difference is larger than 95% of shuffled results → `p < 0.05` → result is not due to chance.

**Bootstrap Confidence Interval**  
Resamples results 500 times. If interval does not include zero → effect is real and stable.

---

## 🧪 Ground Truth Validation

Before testing real models, we validate the tool itself:

1. **Build a seeded bias model** — a logistic regression trained with a deliberate 15-point penalty for female-coded names
2. **Run DHARITRI against it** — detects planted bias at `p < 0.01`
3. **Tool validated** — if it finds bias we deliberately planted, it works

This is what separates DHARITRI from a demo. We know the correct answer. We verify our tool finds it.

---

## 🏗️ System Architecture

```
Frontend Dashboard
       ↓
  REST API  (/audit)
       ↓
  Audit Engine
  ├── Test Case Generator     (controlled identity variants)
  ├── Evaluator Wrapper       (multi-mode model interface)
  └── Statistical Engine      (ISS + permutation + bootstrap)
```

---

## 🎨 Frontend — Two Screens

### Screen 1: Results Dashboard
- Score variation chart
- ISS score display
- p-value with green/red significance indicator
- Confidence interval
- Verdict line

### Screen 2: API Simulator
A Postman-style UI built into the frontend:

```
Left panel            Right panel
──────────────        ──────────────────────────────
POST /audit           {
{ request JSON }        "iss_score": 0.082,
                        "p_value": 0.031,
                        "verdict": "detected"
                      }
```

Makes the product feel real and usable — zero demo risk.

---

## 🛡️ Safety & Reliability

- No scraping of real platforms (LinkedIn, Naukri, etc.)
- All demo results precomputed — no live API dependency
- Deterministic setup — temperature = 0, fixed prompt format
- 3 repeated runs per input to eliminate random noise
- One identity variable per experiment — no confounds

---

## 🎯 Demo Flow

| Step | What to show | Judge reaction |
|------|-------------|----------------|
| 1 | Seeded bias model — DHARITRI detects planted bias at p < 0.01 | "Tool is validated" |
| 2 | Real HuggingFace hiring classifier — identity sensitivity detected | "Real world applicability" |
| 3 | API Simulator — request in, JSON response out | "This is an actual product" |
| 4 | Final pitch line | Remember it |

**After Step 4 — stop talking.**

---

## 👥 Team

| Role | Responsibilities |
|------|-----------------|
| Backend | `/audit` API (Flask/FastAPI) + seeded bias model (sklearn) + statistical engine (scipy) + HuggingFace integration |
| Frontend | Results dashboard + API simulator UI (Chart.js / React) |
| Strategy | Experiment design + precomputed results + pitch + judge Q&A |




---

## ⚠️ What DHARITRI Does NOT Do

| We don't do this | Why |
|-----------------|-----|
| Scrape live platforms | ToS violation, unpredictable behavior |
| Infer caste from surnames | Too many confounds, weakens methodology |
| Claim to produce legal evidence | We produce audit signals, not proof |
| Make India-wide bias claims | We prototype the methodology, not the conclusion |

---

*DHARITRI — Fairness Unit Testing Framework — Google Hackathon 2025*
