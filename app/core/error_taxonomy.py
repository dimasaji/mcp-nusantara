"""Standardized error classification for Nusantara V1.

Categories:
- TRANSIENT: temporary failure, safe to retry
- PERMANENT: unrecoverable, do not retry
- NEEDS_HUMAN: requires operator intervention
- POLICY_DENIED: blocked by access policy
"""
from enum import Enum


class ErrorCategory(str, Enum):
    TRANSIENT = 'TRANSIENT'
    PERMANENT = 'PERMANENT'
    NEEDS_HUMAN = 'NEEDS_HUMAN'
    POLICY_DENIED = 'POLICY_DENIED'


def classify_error(exc: Exception) -> ErrorCategory:
    """Classify an exception into a standard category."""
    name = type(exc).__name__.lower()
    msg = str(exc).lower()
    if 'timeout' in msg or 'connection' in msg or 'unavailable' in msg:
        return ErrorCategory.TRANSIENT
    if 'permission' in msg or 'forbidden' in msg or 'unauthorized' in msg or '403' in msg:
        return ErrorCategory.POLICY_DENIED
    if 'not_found' in msg or 'missing' in msg or 'corrupt' in msg or 'invalid' in msg:
        return ErrorCategory.PERMANENT
    if 'review' in msg or 'metadata' in msg or 'approve' in msg:
        return ErrorCategory.NEEDS_HUMAN
    return ErrorCategory.TRANSIENT


def should_retry(category: ErrorCategory) -> bool:
    return category == ErrorCategory.TRANSIENT


def needs_human(category: ErrorCategory) -> bool:
    return category in (ErrorCategory.NEEDS_HUMAN, ErrorCategory.PERMANENT)
PY