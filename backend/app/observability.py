"""Langfuse + OpenTelemetry observability bootstrap.

One init call per process attaches the Anthropic OTel instrumentor to
Langfuse's tracer provider. From that point on, every `anthropic` SDK call
in the process becomes a span exported to Langfuse — no per-call code
changes needed.

`trace_scenario()` is a context manager used by the eval runner so each
golden scenario produces a single parent trace with the recommender + judge
Anthropic calls as child spans. This is the structure that makes traces
useful for learning: one row per scenario in the Langfuse UI, drill in to
see what each model did.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any

logger = logging.getLogger(__name__)

_initialized = False
_enabled = False


def init_observability(service: str = "backend") -> bool:
    """Initialize Langfuse + Anthropic OTel instrumentation. Idempotent.

    No-op (returns False) when LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY
    are not set, so local dev and CI runs without keys still work.
    """
    global _initialized, _enabled
    if _initialized:
        return _enabled
    _initialized = True

    if not (os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")):
        logger.info("Langfuse keys not set; observability disabled.")
        return False

    from langfuse import Langfuse
    from opentelemetry.instrumentation.anthropic import AnthropicInstrumentor

    Langfuse()
    AnthropicInstrumentor().instrument()

    _enabled = True
    logger.info("Langfuse observability enabled (service=%s).", service)
    return True


def is_enabled() -> bool:
    return _enabled


@contextmanager
def trace_scenario(scenario_id: str, **metadata: Any):
    """Wrap a unit of work (eval scenario, request) in a parent Langfuse trace.

    Anthropic calls made inside this block become child observations of the
    parent because OTel context propagates through the `with` block, so the
    Langfuse UI shows: scenario → recommender call → judge call.
    Filterable scenario metadata (scenario_id, failure_modes, …) lives on
    the parent observation.
    """
    if not _enabled:
        yield None
        return

    from langfuse import get_client

    client = get_client()
    clean_metadata = {
        "scenario_id": scenario_id,
        **{k: v for k, v in metadata.items() if v is not None},
    }

    with client.start_as_current_observation(
        name=f"scenario:{scenario_id}",
        as_type="chain",
        metadata=clean_metadata,
    ) as span:
        yield span


def flush() -> None:
    """Flush buffered traces. Call at the end of long-running scripts."""
    if not _enabled:
        return
    from langfuse import get_client

    get_client().flush()
