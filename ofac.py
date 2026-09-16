#!/usr/bin/env python3
"""
ofac.py — SIH26146 (NTRO) Offline OFAC Sanctions Cross-Reference Engine

Pure Python, 100% air-gapped loader and O(1) matching engine for cryptocurrency
addresses designated on the US Treasury Office of Foreign Assets Control (OFAC)
Specially Designated Nationals (SDN) and Blocked Persons list.

No external HTTP requests or network calls at runtime.
"""

import csv
import os
from typing import Dict, List, Optional, Set, Tuple


class OFACScreener:
    """Offline cross-referencing screener for OFAC-sanctioned cryptocurrency addresses."""

    def __init__(self, csv_path: str = "data/ofac_crypto_addresses.csv"):
        """Load the offline OFAC address list into memory at init time."""
        self.csv_path = csv_path
        self._address_map: Dict[str, dict] = {}
        self._flagged_keys: Set[str] = set()
        self._raw_count = 0
        self._load_data()

    def _normalize_keys(self, raw_address: str) -> List[str]:
        """
        Normalize address for case-insensitive matching and bech32 prefix handling.
        Returns all valid lookup aliases for the given address.
        """
        if not raw_address or not isinstance(raw_address, str):
            return []
        cleaned = raw_address.strip()
        if not cleaned:
            return []

        lower = cleaned.lower()
        keys = [lower]

        # For Bitcoin bech32 addresses, index both full address and prefix-stripped variant
        if lower.startswith("bc1"):
            stripped = lower[3:]
            if stripped:
                keys.append(stripped)
        else:
            # Also support matching an address queried without bc1 prefix
            keys.append(f"bc1{lower}")

        return keys

    def _load_data(self) -> None:
        """Parse CSV and populate in-memory O(1) lookup set and metadata dictionary."""
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(
                f"OFAC sanctions dataset not found at '{self.csv_path}'. "
                "Ensure data/ofac_crypto_addresses.csv exists for offline operation."
            )

        with open(self.csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                addr = (row.get("address") or "").strip()
                if not addr:
                    continue

                record = {
                    "address": addr,
                    "currency": (row.get("currency") or "").strip() or None,
                    "entity_name": (row.get("entity_name") or "").strip() or None,
                    "program": (row.get("program") or "").strip() or None,
                    "list_date": (row.get("list_date") or "").strip() or None,
                }

                for key in self._normalize_keys(addr):
                    self._address_map[key] = record
                    self._flagged_keys.add(key)

                self._raw_count += 1

    def screen(self, address: str) -> dict:
        """
        Check a single wallet address against the OFAC list.

        Returns:
        {
            "is_flagged": bool,
            "entity_name": str | None,
            "program": str | None,
            "currency": str | None,
            "list_date": str | None,
        }
        """
        if not address or not isinstance(address, str):
            return {
                "is_flagged": False,
                "entity_name": None,
                "program": None,
                "currency": None,
                "list_date": None,
            }

        cleaned = address.strip()
        if not cleaned:
            return {
                "is_flagged": False,
                "entity_name": None,
                "program": None,
                "currency": None,
                "list_date": None,
            }

        lower = cleaned.lower()
        record = self._address_map.get(lower)

        if record is None and lower.startswith("bc1"):
            # Try stripped bech32 prefix
            record = self._address_map.get(lower[3:])
        elif record is None:
            # Try prepended bech32 prefix
            record = self._address_map.get(f"bc1{lower}")

        if record is not None:
            return {
                "is_flagged": True,
                "entity_name": record["entity_name"],
                "program": record["program"],
                "currency": record["currency"],
                "list_date": record["list_date"],
            }

        return {
            "is_flagged": False,
            "entity_name": None,
            "program": None,
            "currency": None,
            "list_date": None,
        }

    def screen_batch(self, addresses: List[str]) -> Dict[str, dict]:
        """Screen a list of addresses. Returns a dict keyed by address."""
        return {addr: self.screen(addr) for addr in addresses}

    def flagged_count(self, addresses: List[str]) -> int:
        """How many of these addresses are on the OFAC list."""
        count = 0
        for addr in addresses:
            if not addr or not isinstance(addr, str):
                continue
            cleaned = addr.strip()
            if not cleaned:
                continue
            lower = cleaned.lower()
            if lower in self._flagged_keys:
                count += 1
            elif lower.startswith("bc1") and lower[3:] in self._flagged_keys:
                count += 1
            elif f"bc1{lower}" in self._flagged_keys:
                count += 1
        return count

    def __len__(self) -> int:
        """Total number of designated addresses loaded from the dataset."""
        return self._raw_count
