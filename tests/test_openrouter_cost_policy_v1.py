import json

import pytest

from app.models.openrouter_cost_policy import (
    CostEstimateUnavailable,
    estimate_openrouter_cost,
)


def test_rejects_unverified_pricing(tmp_path):
    path = tmp_path / "pricing.json"
    path.write_text(json.dumps({
        "models": {
            "openai/gpt-4o-mini": {
                "verified": False,
                "input_usd_per_token": "0.00000015",
                "output_usd_per_token": "0.0000006",
                "max_input_tokens": 4096,
                "max_output_tokens": 220,
            }
        }
    }), encoding="utf-8")

    with pytest.raises(CostEstimateUnavailable):
        estimate_openrouter_cost({
            "model": "openai/gpt-4o-mini",
            "messages": [{"role": "user", "content": "uji"}],
            "max_tokens": 220,
        }, pricing_file=path)


@pytest.fixture
def pricing(tmp_path):
    path = tmp_path / "verified-fixture.json"
    path.write_text(json.dumps({"models": {"openai/gpt-4o-mini": {
        "verified": True, "input_usd_per_token": "0.00000015",
        "output_usd_per_token": "0.0000006", "max_input_tokens": 4096,
        "max_output_tokens": 220}}}), encoding="utf-8")
    return path


def test_rejects_output_limit_exceeded(pricing):
    with pytest.raises(CostEstimateUnavailable):
        estimate_openrouter_cost({
            "model": "openai/gpt-4o-mini",
            "messages": [{"role": "user", "content": "uji"}],
            "max_tokens": 221,
        }, pricing_file=pricing)


def test_rejects_unknown_model(pricing):
    with pytest.raises(CostEstimateUnavailable):
        estimate_openrouter_cost({
            "model": "unknown/model",
            "messages": [{"role": "user", "content": "uji"}],
            "max_tokens": 220,
        }, pricing_file=pricing)


def test_rejects_unbounded_large_input(pricing):
    huge_prompt = "A" * 100000

    with pytest.raises(CostEstimateUnavailable):
        estimate_openrouter_cost({
            "model": "openai/gpt-4o-mini",
            "messages": [{"role": "user", "content": huge_prompt}],
            "max_tokens": 220,
        }, pricing_file=pricing)
