"""Stable hashing utilities."""

import hashlib


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def stable_hash(value: str) -> str:
    return sha256_hex(value)
