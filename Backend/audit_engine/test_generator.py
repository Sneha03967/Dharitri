"""
test_generator.py — DHARITRI Audit Engine
Generates controlled identity-variant test cases from a base input.
Calls seeded_bias.generate_paired_samples() for each experiment.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.seeded_bias import generate_paired_samples, EXPERIMENT_REGISTRY


def generate_test_cases(
    base_input: str,
    identity_variable: str,
    sample_size: int = 50,
) -> dict:
    """
    Entry point called by the audit engine.
    Returns
    {
        "identity_variable": str,
        "description":       str,
        "sample_size":       int,
        "pairs":             list[dict]   # {"group", "signal", "input"}
    }
    """
    if identity_variable not in EXPERIMENT_REGISTRY:
        raise ValueError(
            f"Unsupported identity_variable: '{identity_variable}'. "
            f"Choose from: {list(EXPERIMENT_REGISTRY.keys())}"
        )

    _, _, description = EXPERIMENT_REGISTRY[identity_variable]
    pairs = generate_paired_samples(base_input, identity_variable, sample_size)

    return {
        "identity_variable": identity_variable,
        "description":       description,
        "sample_size":       sample_size,
        "pairs":             pairs,
    }


def list_supported_experiments() -> list[dict]:
    """Return all supported experiment types with descriptions."""
    return [
        {"identity_variable": k, "description": v[2]}
        for k, v in EXPERIMENT_REGISTRY.items()
    ]