"""Utilities for billing-model observability logging.

These helpers keep OpenAI and Anthropic routes aligned on one shared schema.
"""

from typing import Any, Dict, Optional


def _extract_username_from_user_doc(user_doc: Dict[str, Any]) -> Optional[str]:
    """Extract a username-like identifier from a MongoDB user document.

    Args:
        user_doc: MongoDB user document loaded by API key.

    Returns:
        Username-like identifier when available, otherwise None.
    """
    username_keys = ("username", "user_name", "name", "email")
    for key in username_keys:
        value = user_doc.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _extract_cache_fields(response_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Extract optional cache metadata from a parsed response payload.

    Args:
        response_payload: Parsed API response payload.

    Returns:
        Mapping containing cache keys found in payload or usage.
    """
    cache_fields: Dict[str, Any] = {}
    for key in ("cache_hit", "cache_write"):
        if key in response_payload:
            cache_fields[key] = response_payload[key]

    usage_payload = response_payload.get("usage")
    if isinstance(usage_payload, dict):
        for key in ("cache_hit", "cache_write"):
            if key in usage_payload and key not in cache_fields:
                cache_fields[key] = usage_payload[key]

    return cache_fields


def _build_billing_observability_log(
    endpoint: str,
    model: str,
    stream: bool,
    auth_context: Dict[str, Any],
    billing_user_id: Optional[str],
    prompt_tokens: int,
    tool_tokens: int,
    message_count: int,
    usage_payload: Optional[Dict[str, Any]],
    cache_fields: Dict[str, Any],
    status: str,
) -> Dict[str, Any]:
    """Build structured billing observability payload for application logs.

    Args:
        endpoint: API endpoint path.
        model: Requested model identifier.
        stream: Whether request is streaming.
        auth_context: Request authentication context.
        billing_user_id: User id used for billing when available.
        prompt_tokens: Calculated prompt tokens.
        tool_tokens: Calculated tool-definition tokens.
        message_count: Number of request messages.
        usage_payload: Response usage payload when available.
        cache_fields: Optional cache metadata extracted from response.
        status: Flow status label for observability.

    Returns:
        Structured payload for billing observability logs.
    """
    username = auth_context.get("username")
    if not isinstance(username, str) or not username.strip():
        username = None

    payload: Dict[str, Any] = {
        "event": "billing_model_observability",
        "endpoint": endpoint,
        "status": status,
        "request": {
            "model": model,
            "stream": stream,
            "message_count": message_count,
            "prompt_tokens": prompt_tokens,
            "tool_tokens": tool_tokens,
        },
        "user": {
            "source": auth_context.get("source"),
            "billing_user_id": billing_user_id,
            "username": username,
            "identity": username or billing_user_id or "anonymous",
        },
        "response": {
            "usage": usage_payload,
            "cache_hit": cache_fields.get("cache_hit"),
            "cache_write": cache_fields.get("cache_write"),
        },
    }

    return payload
