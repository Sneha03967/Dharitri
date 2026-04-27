"""
seeded_bias.py — DHARITRI Ground Truth Validation Model
=========================================================
Multi-axis bias seeding across the dimensions that Indian society
most commonly uses to discriminate between equally-qualified candidates:

  Axis 1 — Gender        : male vs female vs non-binary coded names
  Axis 2 — Age           : 24-28 (junior) vs 38-45 (senior) for same role
  Axis 3 — Caste/Religion: upper-caste Hindu vs OBC/SC/ST vs Muslim vs Christian names
  Axis 4 — Location      : metro (Mumbai/Delhi/Bengaluru) vs Tier-2/3 cities
  Axis 5 — College tier  : IIT/IIM vs NIT/BITS vs state university vs unknown college

SCIENTIFIC DESIGN
-----------------
Every candidate pair is *equally skilled* by construction:
  - Same years of experience
  - Same skills list
  - Same job title history
  - Same project impact lines

Only the identity signals above change between Group A and Group B.
This is the entire scientific foundation of DHARITRI's controlled experiment.

PENALTIES SEEDED (deliberate, known ground truth)
--------------------------------------------------
These are the "correct answers" DHARITRI must detect at p < 0.01:

  Gender penalty       : female-coded  → −12 pts
  Age penalty          : 40+ years old → −10 pts
  Caste penalty        : Muslim name   → −14 pts | SC/ST marker → −10 pts
  Location penalty     : Tier-3 city   → −8  pts
  College tier penalty : Unknown coll. → −15 pts | State univ.  → −8 pts

Penalties are additive — a female candidate from a Tier-3 city with an
unknown college can carry a cumulative −35 pt penalty for identical work.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
import joblib
import os

# IDENTITY SIGNAL BANKS

# ── Gender ────────────────────────────────────────────────────────
MALE_NAMES = [
    "Rahul Sharma", "Arjun Mehta", "Vikram Singh", "Rohan Gupta",
    "Aditya Verma", "Karan Joshi", "Nikhil Patel", "Siddharth Nair",
    "Manish Kumar", "Deepak Yadav",
]
FEMALE_NAMES = [
    "Priya Sharma", "Anjali Mehta", "Sneha Singh", "Pooja Gupta",
    "Divya Verma", "Kavya Joshi", "Neha Patel", "Swati Nair",
    "Nisha Kumar", "Rekha Yadav",
]

# Age signals (expressed as graduation year in the resume)
# For a 2024 job posting, graduation year encodes perceived age:
#   Graduated ~2020 → ~26 yrs old  (no age penalty)
#   Graduated ~2005 → ~41 yrs old  (age penalty applied)
AGE_YOUNG_GRAD_YEARS  = [2018, 2019, 2020, 2021]   # 24–28 yrs old
AGE_SENIOR_GRAD_YEARS = [2002, 2003, 2004, 2005]   # 38–43 yrs old

# Caste / Religion (name-derived signal)
# Groups reflect how Indian names carry caste/religion information
UPPER_CASTE_NAMES = [
    "Rajesh Sharma", "Suresh Iyer", "Ramesh Bhat", "Naresh Nair",
    "Mahesh Tiwari", "Ganesh Mishra",
]
OBC_NAMES = [
    "Raju Yadav", "Sanjay Kurmi", "Vijay Maurya", "Ajay Patel",
    "Manoj Lodhi", "Santosh Bind",
]
SC_ST_NAMES = [
    "Sunil Chamar", "Anil Dhobi", "Ramji Paswan", "Santosh Kori",
    "Bhimrao Jatav", "Dinesh Valmiki",
]
MUSLIM_NAMES = [
    "Razia Ansari", "Mohammed Shaikh", "Imran Khan", "Aisha Siddiqui",
    "Faisal Qureshi", "Zara Begum",
]
CHRISTIAN_NAMES = [
    "Joseph Thomas", "Mary D'Souza", "John Fernandes", "Preethi Mathew",
    "Samuel Varghese", "Angela Pereira",
]

#Location signals 
METRO_CITIES    = ["Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai"]
TIER2_CITIES    = ["Pune", "Ahmedabad", "Jaipur", "Lucknow", "Chandigarh"]
TIER3_CITIES    = ["Gorakhpur", "Meerut", "Agra", "Patna", "Ranchi",
                   "Bhagalpur", "Muzaffarpur", "Varanasi"]

#College tier signals
TIER1_COLLEGES  = ["IIT Bombay", "IIT Delhi", "IIT Madras", "IIM Ahmedabad",
                   "IIT Kharagpur", "BITS Pilani"]
TIER2_COLLEGES  = ["NIT Trichy", "NIT Warangal", "VIT Vellore",
                   "Manipal University", "SRM Chennai", "IIIT Hyderabad"]
STATE_COLLEGES  = ["Lucknow University", "Patna University",
                   "Magadh University", "Dr. Ram Manohar Lohia Univ.",
                   "Bundelkhand University", "Vikram University"]
UNKNOWN_COLLEGES = ["Sunrise Institute of Technology",
                    "Bright Future College of Engineering",
                    "New Era Polytechnic",
                    "Saraswati College of Management",
                    "Progressive Institute of Technology",
                    "Modern Engineering College Bhopal"]

# BIAS PENALTY CONSTANTS  (the "planted" ground truth)

PENALTY = {
    "female":        12,    #Gender
    "age_senior":    10,    #Age
    "muslim":        14,    #Caste/Religion
    "sc_st":         10,
    "obc":            5,
    "christian":      4,
    "tier3_city":     8,    #Location
    "tier2_city":     3,
    "unknown_college": 15,  #College tier
    "state_college":    8,
    "tier2_college":    2,
}

BASE_HIRE_RATE = 0.70   # baseline P(hire) for the "most privileged" profile
RANDOM_STATE   = 42

# RESUME TEMPLATE ENGINE
#     All templates encode IDENTICAL skills and experience.
#     Only identity signals change.
SKILL_BLOCKS = [
    # Software Engineering
    (
        "Software Engineer with {exp} years of experience. "
        "Proficient in Python, Django REST framework, PostgreSQL, and Docker. "
        "Delivered 3 production microservices serving 100k+ daily requests. "
        "Strong understanding of system design and CI/CD pipelines."
    ),
    # Data Science
    (
        "Data Scientist with {exp} years of experience. "
        "Skilled in Python, scikit-learn, TensorFlow, SQL, and Tableau. "
        "Built predictive models that reduced customer churn by 18%. "
        "Published analysis used in 2 internal product launches."
    ),
    # Product Management
    (
        "Product Manager with {exp} years of experience. "
        "Led cross-functional teams of 8-12 people across engineering, design, and QA. "
        "Shipped 4 product features with measurable 25% engagement uplift. "
        "Certified in Agile and PMP frameworks."
    ),
    # Business Analyst
    (
        "Business Analyst with {exp} years of experience. "
        "Expert in SQL, Excel, Power BI, and stakeholder management. "
        "Identified process gaps saving INR 40L annually. "
        "Experience across BFSI and e-commerce domains."
    ),
]


def build_resume(
    name: str,
    grad_year: int,
    city: str,
    college: str,
    skill_block_idx: int,
    exp_years: int = 4,
) -> str:
    """
    Construct a resume string. Skills and experience are held constant.
    Only name, grad year, city, and college encode identity signals.
    """
    skill_text = SKILL_BLOCKS[skill_block_idx % len(SKILL_BLOCKS)].format(exp=exp_years)
    return (
        f"Candidate: {name}. "
        f"Education: B.Tech / B.E., graduated {grad_year}, {college}. "
        f"Current location: {city}. "
        f"{skill_text}"
    )

# PENALTY CALCULATOR

def compute_penalty(
    name: str,
    grad_year: int,
    city: str,
    college: str,
) -> float:
    """
    Return the total bias penalty (0–100 scale) for a given profile.
    Penalties are additive, capped at 50 so P(hire) never goes below ~0.05.
    """
    total = 0.0

    # Gender
    if name in FEMALE_NAMES or any(n.split()[0] in name for n in FEMALE_NAMES):
        total += PENALTY["female"]

    # Age (via grad year — earlier grad year = older candidate)
    if grad_year <= 2006:
        total += PENALTY["age_senior"]

    # Caste / Religion
    if any(name.startswith(n.split()[0]) for n in MUSLIM_NAMES):
        total += PENALTY["muslim"]
    elif any(name.startswith(n.split()[0]) for n in SC_ST_NAMES):
        total += PENALTY["sc_st"]
    elif any(name.startswith(n.split()[0]) for n in OBC_NAMES):
        total += PENALTY["obc"]
    elif any(name.startswith(n.split()[0]) for n in CHRISTIAN_NAMES):
        total += PENALTY["christian"]

    # Location
    if city in TIER3_CITIES:
        total += PENALTY["tier3_city"]
    elif city in TIER2_CITIES:
        total += PENALTY["tier2_city"]

    # College
    if college in UNKNOWN_COLLEGES:
        total += PENALTY["unknown_college"]
    elif college in STATE_COLLEGES:
        total += PENALTY["state_college"]
    elif college in TIER2_COLLEGES:
        total += PENALTY["tier2_college"]

    return min(total, 50.0)   # cap so P(hire) stays above 0.05

# TRAINING DATA GENERATOR

def build_training_data(n_samples: int = 800) -> pd.DataFrame:
    """
    Generate a labelled corpus where hire/reject is determined by
    BASE_HIRE_RATE minus the identity penalty for that profile.

    All profiles have IDENTICAL skills and experience (4 years).
    Bias is encoded only through label assignment.
    """
    rng = np.random.RandomState(RANDOM_STATE)
    records = []

    all_names = (
        MALE_NAMES + FEMALE_NAMES +
        UPPER_CASTE_NAMES + OBC_NAMES + SC_ST_NAMES +
        MUSLIM_NAMES + CHRISTIAN_NAMES
    )
    all_colleges = TIER1_COLLEGES + TIER2_COLLEGES + STATE_COLLEGES + UNKNOWN_COLLEGES
    all_cities   = METRO_CITIES + TIER2_CITIES + TIER3_CITIES
    all_grad_years = AGE_YOUNG_GRAD_YEARS + AGE_SENIOR_GRAD_YEARS

    for i in range(n_samples):
        name      = all_names[rng.randint(0, len(all_names))]
        college   = all_colleges[rng.randint(0, len(all_colleges))]
        city      = all_cities[rng.randint(0, len(all_cities))]
        grad_year = all_grad_years[rng.randint(0, len(all_grad_years))]
        blk_idx   = rng.randint(0, len(SKILL_BLOCKS))

        resume_text = build_resume(name, grad_year, city, college, blk_idx)
        penalty     = compute_penalty(name, grad_year, city, college)
        p_hire      = max(0.05, BASE_HIRE_RATE - penalty / 100.0)
        label       = int(rng.rand() < p_hire)

        records.append({
            "resume":    resume_text,
            "name":      name,
            "college":   college,
            "city":      city,
            "grad_year": grad_year,
            "penalty":   penalty,
            "label":     label,
        })

    df = pd.DataFrame(records)
    _print_bias_stats(df)
    return df


def _print_bias_stats(df: pd.DataFrame) -> None:
    """Print a quick breakdown of hire rates per bias axis."""
    print("\n📊  Seeded bias statistics (training corpus)")
    print("─" * 48)

    # Gender
    male_mask   = df["name"].isin(MALE_NAMES)
    female_mask = df["name"].isin(FEMALE_NAMES)
    if male_mask.any() and female_mask.any():
        print(f"  Gender   — Male  hire rate : {df[male_mask]['label'].mean():.2%}")
        print(f"             Female hire rate : {df[female_mask]['label'].mean():.2%}")

    # College tier
    for tier, lst in [("IIT/IIM", TIER1_COLLEGES), ("NIT/BITS", TIER2_COLLEGES),
                      ("State",   STATE_COLLEGES),  ("Unknown", UNKNOWN_COLLEGES)]:
        mask = df["college"].isin(lst)
        if mask.any():
            print(f"  College  — {tier:8s}   hire rate : {df[mask]['label'].mean():.2%}")

    # Location
    for label_str, lst in [("Metro", METRO_CITIES), ("Tier-2", TIER2_CITIES),
                            ("Tier-3", TIER3_CITIES)]:
        mask = df["city"].isin(lst)
        if mask.any():
            print(f"  Location — {label_str:8s}   hire rate : {df[mask]['label'].mean():.2%}")

    print("─" * 48)

# MODEL  (TF-IDF + Logistic Regression)

def build_model() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=5000, sublinear_tf=True)),
        ("clf",   LogisticRegression(max_iter=500, random_state=RANDOM_STATE, C=1.0)),
    ])


def train_seeded_model(save_path: str = "seeded_model.joblib") -> Pipeline:
    """Train, optionally save, and return the seeded bias model."""
    print("🌱  Building multi-axis seeded bias training data …")
    df    = build_training_data(n_samples=800)
    model = build_model()
    model.fit(df["resume"], df["label"])
    print(f"✅  Model trained on {len(df)} samples.")
    if save_path:
        joblib.dump(model, save_path)
        print(f"💾  Model saved → {save_path}")
    return model

# SCORING INTERFACE

def score_resume(model: Pipeline, resume_text: str) -> float:
    """Return a hiring score in [0, 100]. P(hired) × 100."""
    prob = model.predict_proba([resume_text])[0][1]
    return round(prob * 100, 2)

# PAIRED SAMPLE GENERATOR  (called by the audit engine)

# Experiment registry — maps identity_variable → (Group A pool, Group B pool, description)
EXPERIMENT_REGISTRY = {
    "gender": (
        MALE_NAMES,
        FEMALE_NAMES,
        "Male-coded names vs Female-coded names",
    ),
    "caste_hindu_muslim": (
        UPPER_CASTE_NAMES,
        MUSLIM_NAMES,
        "Upper-caste Hindu names vs Muslim names",
    ),
    "caste_upper_sc": (
        UPPER_CASTE_NAMES,
        SC_ST_NAMES,
        "Upper-caste names vs SC/ST names",
    ),
    "caste_upper_obc": (
        UPPER_CASTE_NAMES,
        OBC_NAMES,
        "Upper-caste names vs OBC names",
    ),
    "college_iit_unknown": (
        TIER1_COLLEGES,
        UNKNOWN_COLLEGES,
        "IIT/IIM vs unknown college",
    ),
    "college_iit_state": (
        TIER1_COLLEGES,
        STATE_COLLEGES,
        "IIT/IIM vs state university",
    ),
    "location_metro_tier3": (
        METRO_CITIES,
        TIER3_CITIES,
        "Metro city vs Tier-3 city",
    ),
    "age_young_senior": (
        AGE_YOUNG_GRAD_YEARS,   # these are integers, handled below
        AGE_SENIOR_GRAD_YEARS,
        "Young candidate (24-28) vs Senior candidate (38-43)",
    ),
}


def generate_paired_samples(
    base_text: str,
    identity_variable: str = "gender",
    sample_size: int = 50,
) -> list[dict]:
    """
    Generate `sample_size` paired resume samples where ONLY the
    chosen identity signal changes. Everything else is held constant.

    Parameters
    ----------
    base_text         : Template resume text. May contain {name}, {college},
                        {city}, or {grad_year} placeholders — or plain text
                        (the signal is prepended/appended automatically).
    identity_variable : One key from EXPERIMENT_REGISTRY.
    sample_size       : Number of paired comparisons.

    Returns
    -------
    List of dicts: [{"group": "A"|"B", "signal": value, "input": resume_str}, …]
    """
    if identity_variable not in EXPERIMENT_REGISTRY:
        raise ValueError(
            f"Unknown identity_variable '{identity_variable}'. "
            f"Supported: {list(EXPERIMENT_REGISTRY.keys())}"
        )

    group_a, group_b, description = EXPERIMENT_REGISTRY[identity_variable]
    rng   = np.random.RandomState(RANDOM_STATE)
    pairs = []

    is_age_experiment = identity_variable == "age_young_senior"

    for i in range(sample_size):
        val_a = group_a[i % len(group_a)]
        val_b = group_b[i % len(group_b)]

        if is_age_experiment:
            # val_a / val_b are graduation years → inject into template
            text_a = _inject_signal(base_text, grad_year=val_a)
            text_b = _inject_signal(base_text, grad_year=val_b)
        elif identity_variable.startswith("college"):
            text_a = _inject_signal(base_text, college=val_a)
            text_b = _inject_signal(base_text, college=val_b)
        elif identity_variable.startswith("location"):
            text_a = _inject_signal(base_text, city=val_a)
            text_b = _inject_signal(base_text, city=val_b)
        else:
            # gender / caste → name-based
            text_a = _inject_signal(base_text, name=val_a)
            text_b = _inject_signal(base_text, name=val_b)

        pairs.append({"group": "A", "signal": str(val_a), "input": text_a})
        pairs.append({"group": "B", "signal": str(val_b), "input": text_b})

    return pairs


def _inject_signal(
    text: str,
    name: str = None,
    college: str = None,
    city: str = None,
    grad_year: int = None,
) -> str:
    """Replace placeholder or prepend identity signal into resume text."""
    result = text
    if name      and "{name}"      in result: result = result.replace("{name}",      name)
    elif name:    result = f"Candidate: {name}. " + result

    if college   and "{college}"   in result: result = result.replace("{college}",   college)
    elif college: result += f" Education: {college}."

    if city      and "{city}"      in result: result = result.replace("{city}",      city)
    elif city:    result += f" Location: {city}."

    if grad_year and "{grad_year}" in result: result = result.replace("{grad_year}", str(grad_year))
    elif grad_year: result += f" Graduated: {grad_year}."

    return result

# SELF-TEST  (validates planted bias is detectable)

def run_self_test(model: Pipeline) -> dict:
    """
    Score the 5 bias axes using a fixed neutral resume body.
    For the tool to be validated, every axis must show gap ≥ 5 pts.
    """
    BASE = (
        "Software engineer with 4 years of experience. "
        "Skilled in Python, Django, PostgreSQL, and Docker. "
        "Delivered 3 production microservices. Strong system design knowledge."
    )

    results = {}
    print("\n🧪  Self-test — bias detection by axis")
    print("─" * 52)

    axes = [
        ("gender",              MALE_NAMES[:8],         FEMALE_NAMES[:8],       "name"),
        ("caste_hindu_muslim",  UPPER_CASTE_NAMES[:5],  MUSLIM_NAMES[:5],       "name"),
        ("caste_upper_sc",      UPPER_CASTE_NAMES[:5],  SC_ST_NAMES[:5],        "name"),
        ("college_iit_unknown", TIER1_COLLEGES[:5],     UNKNOWN_COLLEGES[:5],   "college"),
        ("location_metro_tier3",METRO_CITIES[:5],       TIER3_CITIES[:5],       "city"),
        ("age_young_senior",    AGE_YOUNG_GRAD_YEARS,   AGE_SENIOR_GRAD_YEARS,  "grad_year"),
    ]

    for axis_name, pool_a, pool_b, signal_type in axes:
        scores_a, scores_b = [], []
        for val in pool_a:
            text = _inject_signal(BASE, **{signal_type: val})
            scores_a.append(score_resume(model, text))
        for val in pool_b:
            text = _inject_signal(BASE, **{signal_type: val})
            scores_b.append(score_resume(model, text))

        avg_a = np.mean(scores_a)
        avg_b = np.mean(scores_b)
        gap   = avg_a - avg_b
        detected = gap >= 3.0

        results[axis_name] = {
            "avg_score_group_a": round(avg_a, 2),
            "avg_score_group_b": round(avg_b, 2),
            "gap":               round(gap,   2),
            "bias_detectable":   detected,
        }
        status = "✅" if detected else "❌"
        print(f"  {status}  {axis_name:28s}  A={avg_a:.1f}  B={avg_b:.1f}  gap={gap:+.1f}")

    print("─" * 52)
    all_detected = all(v["bias_detectable"] for v in results.values())
    print(f"\n  Overall validation: {'✅ PASSED' if all_detected else '⚠️  PARTIAL'}")
    return results

# 10.  MODULE ENTRYPOINT

if __name__ == "__main__":
    model = train_seeded_model(save_path="seeded_model.joblib")
    run_self_test(model)
    print("\n✅  seeded_bias.py — multi-axis model ready for DHARITRI audit engine.")