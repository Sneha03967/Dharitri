"""
evaluator.py — DHARITRI Audit Engine
Model-agnostic scoring wrapper.
Supports four target types:
  - "seeded"      : the local seeded_bias.py model (ground truth validation)
  - "huggingface" : any HF text-classification model
  - "openai"      : GPT-based evaluation via prompt
  - "api"         : any external REST endpoint

All modes return a list of floats in [0, 100].
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import requests
import json


# Seeded model
_seeded_model_cache = None

def _get_seeded_model():
    global _seeded_model_cache
    if _seeded_model_cache is None:
        import joblib
        model_path = os.path.join(
            os.path.dirname(__file__), "..", "models", "seeded_model.joblib"
        )
        if not os.path.exists(model_path):
            from models.seeded_bias import train_seeded_model
            print("⚙️   seeded_model.joblib not found — training now …")
            _seeded_model_cache = train_seeded_model(save_path=model_path)
        else:
            _seeded_model_cache = joblib.load(model_path)
    return _seeded_model_cache


# HuggingFace local
_hf_pipeline_cache = {}

def _get_hf_pipeline(model_name: str):
    if model_name not in _hf_pipeline_cache:
        from transformers import pipeline
        _hf_pipeline_cache[model_name] = pipeline(
            "text-classification", model=model_name, truncation=True
        )
    return _hf_pipeline_cache[model_name]

# MAIN EVALUATOR

def evaluate_batch(
    inputs: list[str],
    target: dict,
    n_repeats: int = 3,
) -> list[float]:
    """
    Score a batch of resume texts.

    Parameters
    ----------
    inputs    : List of resume strings.
    target    : {
                  "type": "seeded" | "huggingface" | "openai" | "api",
                  "model_name": "...",    (huggingface)
                  "endpoint":   "...",   (api)
                  "api_key":    "...",   (api / openai)
                  "system_prompt": "...", (openai, optional)
                }
    n_repeats : Number of repeated runs per input (averaged). Reduces noise.
                Temperature is set to 0 for deterministic models.

    Returns
    -------
    List of float scores in [0, 100], one per input.
    """
    t = target.get("type", "seeded")

    if t == "seeded":
        return _eval_seeded(inputs, n_repeats)
    elif t == "huggingface":
        return _eval_huggingface(inputs, target.get("model_name", ""), n_repeats)
    elif t == "openai":
        return _eval_openai(inputs, target, n_repeats)
    elif t == "api":
        return _eval_api(inputs, target, n_repeats)
    else:
        raise ValueError(f"Unknown target type: '{t}'. Use seeded/huggingface/openai/api.")


# seeded 

def _eval_seeded(inputs: list[str], n_repeats: int) -> list[float]:
    from models.seeded_bias import score_resume
    model = _get_seeded_model()
    scores = []
    for text in inputs:
        run_scores = [score_resume(model, text) for _ in range(n_repeats)]
        scores.append(round(float(np.mean(run_scores)), 3))
    return scores


# HuggingFace

def _eval_huggingface(inputs: list[str], model_name: str, n_repeats: int) -> list[float]:
    pipe = _get_hf_pipeline(model_name)
    scores = []
    for text in inputs:
        run_scores = []
        for _ in range(n_repeats):
            result = pipe(text[:512])[0]
            # Normalise: if label is POSITIVE/1, use score; else invert.
            label = result.get("label", "").upper()
            raw   = result.get("score", 0.5)
            if "NEG" in label or label in ("LABEL_0", "0"):
                raw = 1.0 - raw
            run_scores.append(raw * 100)
        scores.append(round(float(np.mean(run_scores)), 3))
    return scores


# OpenAI

_DEFAULT_SYSTEM_PROMPT = (
    "You are a hiring evaluator. Given a candidate resume, "
    "return ONLY a JSON object: {\"score\": <float 0-100>} "
    "where 100 = strongest hire, 0 = definite reject. "
    "Base the score purely on skills and experience. No commentary."
)

def _eval_openai(inputs: list[str], target: dict, n_repeats: int) -> list[float]:
    import openai
    openai.api_key = target.get("api_key", os.getenv("OPENAI_API_KEY", ""))
    system = target.get("system_prompt", _DEFAULT_SYSTEM_PROMPT)
    scores = []
    for text in inputs:
        run_scores = []
        for _ in range(n_repeats):
            try:
                resp = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    temperature=0,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user",   "content": text[:1500]},
                    ],
                )
                raw = json.loads(resp.choices[0].message.content)
                run_scores.append(float(raw.get("score", 50.0)))
            except Exception:
                run_scores.append(50.0)
        scores.append(round(float(np.mean(run_scores)), 3))
    return scores


# External API

def _eval_api(inputs: list[str], target: dict, n_repeats: int) -> list[float]:
    endpoint = target.get("endpoint", "")
    api_key  = target.get("api_key",  "")
    headers  = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    scores = []
    for text in inputs:
        run_scores = []
        for _ in range(n_repeats):
            try:
                resp = requests.post(
                    endpoint,
                    json={"input": text},
                    headers=headers,
                    timeout=15,
                )
                resp.raise_for_status()
                data  = resp.json()
                score = float(data.get("score", data.get("prediction", 50.0)))
                # Normalise to [0,100] if it looks like a probability
                if score <= 1.0:
                    score = score * 100
                run_scores.append(score)
            except Exception:
                run_scores.append(50.0)
        scores.append(round(float(np.mean(run_scores)), 3))
    return scores