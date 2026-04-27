"""app.py — DHARITRI Backend Entry Point
======================================
REST API exposing the fairness audit engine.

Endpoints
  POST /audit          — Run a full fairness audit
  GET  /experiments    — List all supported identity experiments
  GET  /health         — Health check

Run locally:
  pip install -r requirements.txt
  python app.py

Or with uvicorn (FastAPI mode):
  uvicorn app:app --reload --port 8000"""

import os
import sys
import json

# ── Flask (default) or FastAPI depending on installed packages ────
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    from typing import Optional
    import uvicorn
    _USE_FASTAPI = True
except ImportError:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    _USE_FASTAPI = False


sys.path.insert(0, os.path.dirname(__file__))

from audit_engine.test_generator import generate_test_cases, list_supported_experiments
from audit_engine.evaluator      import evaluate_batch
from audit_engine.statistics     import compute_full_report


# ─────────────────────────────────────────────────────────────────
# REQUEST / RESPONSE SCHEMAS
# ─────────────────────────────────────────────────────────────────

if _USE_FASTAPI:
    class TargetConfig(BaseModel):
        type:          str            = Field("seeded", description="seeded | huggingface | openai | api")
        model_name:    Optional[str]  = None
        endpoint:      Optional[str]  = None
        api_key:       Optional[str]  = None
        system_prompt: Optional[str]  = None

    class AuditRequest(BaseModel):
        target:            TargetConfig
        base_input:        str         = Field(..., description="Resume template text")
        identity_variable: str         = Field("gender", description="Experiment type")
        sample_size:       int         = Field(50, ge=10, le=200)

    class AuditResponse(BaseModel):
        identity_variable:   str
        description:         str
        iss_score:           float
        p_value:             float
        confidence_interval: list[float]
        verdict:             str
        mean_score_group_a:  float
        mean_score_group_b:  float
        n_samples_per_group: int


# ─────────────────────────────────────────────────────────────────
# CORE AUDIT LOGIC  (shared between Flask and FastAPI)
# ─────────────────────────────────────────────────────────────────


def run_audit(payload: dict) -> dict:
    """Execute the full audit pipeline and return a result dict."""
    target            = payload.get("target", {"type": "seeded"})
    base_input        = payload.get("base_input", "")
    identity_variable = payload.get("identity_variable", "gender")
    sample_size       = int(payload.get("sample_size", 50))

    if not base_input:
        raise ValueError("base_input is required.")

    # 1. Generate paired test cases
    test_data = generate_test_cases(base_input, identity_variable, sample_size)

    # 2. Split into Group A and Group B
    pairs    = test_data["pairs"]
    inputs_a = [p["input"] for p in pairs if p["group"] == "A"]
    inputs_b = [p["input"] for p in pairs if p["group"] == "B"]

    # 3. Score each group
    scores_a = evaluate_batch(inputs_a, target)
    scores_b = evaluate_batch(inputs_b, target)

    # 4. Run statistical engine
    stats = compute_full_report(scores_a, scores_b)

    return {
        "identity_variable": identity_variable,
        "description":       test_data["description"],
        **stats,
    }


# ─────────────────────────────────────────────────────────────────
# FASTAPI APP
# ─────────────────────────────────────────────────────────────────

if _USE_FASTAPI:
    app = FastAPI(
        title="DHARITRI — Fairness Unit Testing API",
        description="Audit any AI system for identity sensitivity.",
        version="1.0.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "DHARITRI"}

    @app.get("/experiments")
    def experiments():
        return {"experiments": list_supported_experiments()}

    @app.post("/audit", response_model=AuditResponse)
    def audit(req: AuditRequest):
        try:
            payload = req.dict()
            payload["target"] = req.target.dict()
            return run_audit(payload)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    if __name__ == "__main__":
        port = int(os.getenv("PORT", 8000))
        uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)


# ─────────────────────────────────────────────────────────────────
# FLASK APP  (fallback)
# ─────────────────────────────────────────────────────────────────

else:
    app = Flask(__name__)
    CORS(app)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "service": "DHARITRI"})

    @app.get("/experiments")
    def experiments():
        return jsonify({"experiments": list_supported_experiments()})

    @app.route("/audit", methods=["POST"])
    def audit():
        payload = request.get_json(force=True) or {}
        try:
            result = run_audit(payload)
            return jsonify(result), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    if __name__ == "__main__":
        port = int(os.getenv("PORT", 8000))
        app.run(host="0.0.0.0", port=port, debug=True)
