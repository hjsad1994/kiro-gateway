#!/usr/bin/env python3
"""Upsert auth credentials JSON into MongoDB auth_kv collection.

This script reads a local JSON file (for example ``test.json``) and writes it to
``auth_kv`` in MongoDB using the document shape expected by ``kiro/auth.py``:

    {"key": "kirocli:social:token", "value": {...}}

Args:
    --json-file: Path to source JSON file.
    --uri: MongoDB connection string. Falls back to MONGODB_URI env.
    --db-name: Database name. Falls back to MONGODB_DB_NAME env or "fproxy".
    --collection: Collection name. Falls back to MONGODB_AUTH_KV_COLLECTION env
        or "auth_kv".
    --key: auth_kv key to write. Default: "kirocli:social:token".
    --replace-value: Replace existing ``value`` object instead of merge update.

Returns:
    Exit code 0 on success, non-zero on error.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

from loguru import logger
from pymongo import MongoClient


DEFAULT_MONGODB_URI = (
    "mongodb+srv://trantai306_db_user:FHBuXtedXaFLBr22@cluster0.aa02bn1.mongodb.net/"
    "?appName=Cluster0"
)
DEFAULT_DB_NAME = "fproxy"
DEFAULT_COLLECTION = "auth_kv"


def _build_payload(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Convert camelCase token JSON to auth_kv-compatible payload.

    Args:
        raw: Raw JSON object loaded from input file.

    Returns:
        Dict payload suitable for ``auth_kv.value``.

    Raises:
        ValueError: If required fields are missing.
    """
    access_token = raw.get("accessToken") or raw.get("access_token")
    refresh_token = raw.get("refreshToken") or raw.get("refresh_token")
    expires_at = raw.get("expiresAt") or raw.get("expires_at")

    if not access_token:
        raise ValueError("Missing required field: accessToken")
    if not refresh_token:
        raise ValueError("Missing required field: refreshToken")

    payload: Dict[str, Any] = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": expires_at,
    }

    optional_mapping = {
        "profileArn": "profile_arn",
        "profile_arn": "profile_arn",
        "provider": "provider",
        "authMethod": "auth_method",
        "auth_method": "auth_method",
        "region": "region",
        "ssoRegion": "region",
        "scopes": "scopes",
    }
    for src_key, dst_key in optional_mapping.items():
        if src_key in raw and raw[src_key] is not None:
            payload[dst_key] = raw[src_key]

    return payload


def upsert_auth_kv(
    *,
    json_file: Path,
    uri: str,
    db_name: str,
    collection_name: str,
    auth_key: str,
    replace_value: bool,
) -> int:
    """Upsert one auth_kv record into MongoDB.

    Args:
        json_file: Path to source JSON file.
        uri: MongoDB connection URI.
        db_name: Target database name.
        collection_name: Target collection name.
        auth_key: auth_kv key field value.
        replace_value: Whether to replace whole value object.

    Returns:
        Exit code (0 success, 1 failure).
    """
    try:
        raw = json.loads(json_file.read_text(encoding="utf-8"))
    except FileNotFoundError:
        logger.error("JSON file not found: {}", json_file)
        return 1
    except json.JSONDecodeError as error:
        logger.error("Invalid JSON in {}: {}", json_file, error)
        return 1

    try:
        payload = _build_payload(raw)
    except ValueError as error:
        logger.error("Input validation failed: {}", error)
        return 1

    client = MongoClient(uri)
    collection = client[db_name][collection_name]

    try:
        existing = collection.find_one({"key": auth_key}, {"_id": 0, "value": 1})
        if replace_value or not existing or not isinstance(existing.get("value"), dict):
            value_to_write = payload
        else:
            value_to_write = dict(existing["value"])
            value_to_write.update(payload)

        result = collection.update_one(
            {"key": auth_key},
            {"$set": {"value": value_to_write}},
            upsert=True,
        )
    except Exception as error:
        logger.error("MongoDB upsert failed: {}", error)
        return 1
    finally:
        client.close()

    if result.upserted_id is not None:
        logger.info(
            "Inserted auth_kv key '{}' into {}.{}",
            auth_key,
            db_name,
            collection_name,
        )
    else:
        logger.info(
            "Updated auth_kv key '{}' in {}.{}",
            auth_key,
            db_name,
            collection_name,
        )

    logger.info("Write complete (access/refresh tokens not printed).")
    return 0


def _infer_auth_key(raw: Dict[str, Any], explicit_key: str) -> str:
    """Infer auth_kv key from payload when key is not explicitly supplied.

    Args:
        raw: Raw JSON object from input file.
        explicit_key: Key from CLI argument.

    Returns:
        Resolved auth_kv key.
    """
    if explicit_key:
        return explicit_key

    auth_method = raw.get("authMethod") or raw.get("auth_method") or "social"
    return f"kirocli:{str(auth_method).lower()}:token"


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments.

    Returns:
        Parsed argparse namespace.
    """
    parser = argparse.ArgumentParser(description="Upsert auth_kv from JSON file")
    parser.add_argument(
        "--json-file",
        default="test.json",
        help="Path to source JSON file (default: test.json)",
    )
    parser.add_argument(
        "--uri",
        default=os.getenv("MONGODB_URI", DEFAULT_MONGODB_URI),
        help="MongoDB URI (default: built-in Cluster0 URI or MONGODB_URI)",
    )
    parser.add_argument(
        "--db-name",
        default=os.getenv("MONGODB_DB_NAME", DEFAULT_DB_NAME),
        help="MongoDB database name",
    )
    parser.add_argument(
        "--collection",
        default=os.getenv("MONGODB_AUTH_KV_COLLECTION", DEFAULT_COLLECTION),
        help="MongoDB collection name",
    )
    parser.add_argument(
        "--key",
        default="",
        help="auth_kv key value (auto-infer from authMethod if omitted)",
    )
    parser.add_argument(
        "--replace-value",
        action="store_true",
        help="Replace existing value object instead of merge update",
    )
    return parser.parse_args()


def main() -> int:
    """Program entry point.

    Returns:
        Process exit code.
    """
    args = _parse_args()

    try:
        raw = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
    except FileNotFoundError:
        logger.error("JSON file not found: {}", args.json_file)
        return 1
    except json.JSONDecodeError as error:
        logger.error("Invalid JSON in {}: {}", args.json_file, error)
        return 1

    auth_key = _infer_auth_key(raw, args.key)

    logger.info(
        "Upserting into {}.{} with key '{}' from {}",
        args.db_name,
        args.collection,
        auth_key,
        args.json_file,
    )

    return upsert_auth_kv(
        json_file=Path(args.json_file),
        uri=args.uri,
        db_name=args.db_name,
        collection_name=args.collection,
        auth_key=auth_key,
        replace_value=args.replace_value,
    )


if __name__ == "__main__":
    sys.exit(main())
