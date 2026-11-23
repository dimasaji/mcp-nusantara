"""Fail-closed OpenRouter cost estimator for Nusantara V1."""
from decimal import Decimal, InvalidOperation, ROUND_CEILING
import json
from pathlib import Path


class CostEstimateUnavailable(RuntimeError):
    pass


def estimate_openrouter_cost(payload: dict, *, pricing_file: str | Path) -> Decimal:
    """Conservative reservation; pricing values are USD per token."""
    try:
        data = json.loads(Path(pricing_file).read_text(encoding="utf-8-sig"))
        model = payload["model"]
        entry = data["models"][model]
        if entry["verified"] is not True:
            raise ValueError("Unverified pricing")
        input_rate = Decimal(str(entry["input_usd_per_token"]))
        output_rate = Decimal(str(entry["output_usd_per_token"]))
        if not input_rate.is_finite() or not output_rate.is_finite():
            raise ValueError("Invalid pricing")
        if input_rate < 0 or output_rate < 0:
            raise ValueError("Negative pricing")

        messages = payload["messages"]
        if not isinstance(messages, list) or not messages:
            raise ValueError("Invalid messages")

        # Conservative UTF-8 bound for text-only messages.
        # Reject unsupported structures and features.
        if set(payload) - {"model", "messages", "max_tokens", "temperature", "top_p", "stream"}:
            raise ValueError("Unsupported request features")
        # The adapter explicitly sends stream:false for its bounded JSON response.
        # Streaming (including coerced/string values) remains unsupported.
        if 'stream' in payload and payload['stream'] is not False:
            raise ValueError("Streaming unsupported")

        for message in messages:
            if not isinstance(message, dict):
                raise ValueError("Invalid message")
            if set(message) != {"role", "content"}:
                raise ValueError("Unsupported message fields")
            if message["role"] not in {"system", "user", "assistant"}:
                raise ValueError("Unsupported role")
            if not isinstance(message["content"], str):
                raise ValueError("Non-text content unsupported")

        # Count UTF-8 bytes conservatively, with overhead allowance.
        input_bound = sum(
            len(message["content"].encode("utf-8")) + 64
            for message in messages
        )

        max_input_tokens = int(entry["max_input_tokens"])
        if input_bound > max_input_tokens:
            raise ValueError("Input bound exceeded")
        max_output_tokens = int(payload["max_tokens"])
        if max_input_tokens <= 0 or max_output_tokens <= 0:
            raise ValueError("Invalid token limits")
        if max_output_tokens > int(entry["max_output_tokens"]):
            raise ValueError("Output limit exceeded")

        # Reserve using full configured input allowance.
        estimate = (
            Decimal(max_input_tokens) * input_rate
            + Decimal(max_output_tokens) * output_rate
        )
        if estimate <= 0:
            raise ValueError("Zero reservation")
        return estimate.quantize(Decimal("0.01"), rounding=ROUND_CEILING)
    except (OSError, KeyError, TypeError, ValueError, InvalidOperation, json.JSONDecodeError) as exc:
        raise CostEstimateUnavailable("PRICING_UNAVAILABLE_OR_INVALID") from exc
