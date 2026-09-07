"""Shared transaction parsing and validation for the offline SIH26146 pipeline."""

from __future__ import annotations

import csv
import ipaddress
import json
import math
from datetime import datetime
from typing import Any, Dict, Iterable, List

REQUIRED_FIELDS = [
    "timestamp",
    "txid",
    "input_wallet_addresses",
    "output_wallet_addresses",
    "total_input_amount",
    "fee",
    "script_type",
    "src_ip",
    "src_port",
    "dst_ip",
    "dst_port",
    "_ground_truth_label",
]

VALID_LABELS = {"normal", "peel_chain", "mixer", "rapid_cashout"}
VALID_SCRIPT_TYPES = {"P2PKH", "P2SH", "P2WPKH", "P2WSH"}
AMOUNT_TOLERANCE = 1e-7


def _error(row_number: int, field: str, message: str) -> ValueError:
    return ValueError(f"Row {row_number}, field '{field}': {message}")


def _finite_number(value: Any, row_number: int, field: str, *, positive: bool = False) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise _error(row_number, field, f"expected a number, got {value!r}") from exc
    if not math.isfinite(number):
        raise _error(row_number, field, "must be finite")
    if positive and number <= 0:
        raise _error(row_number, field, "must be greater than zero")
    if not positive and number < 0:
        raise _error(row_number, field, "must not be negative")
    return number


def _port(value: Any, row_number: int, field: str) -> int:
    try:
        port = int(value)
    except (TypeError, ValueError) as exc:
        raise _error(row_number, field, f"expected an integer port, got {value!r}") from exc
    if not 0 <= port <= 65535:
        raise _error(row_number, field, "must be between 0 and 65535")
    return port


def _wallet_entries(value: Any, row_number: int, field: str) -> List[Dict[str, Any]]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise _error(row_number, field, f"invalid JSON: {exc.msg}") from exc
    if not isinstance(value, list) or not value:
        raise _error(row_number, field, "must be a non-empty list")

    entries = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise _error(row_number, field, f"entry {index} must be an object")
        address = item.get("address")
        if not isinstance(address, str) or not address.strip():
            raise _error(row_number, field, f"entry {index} has an empty address")
        amount = _finite_number(item.get("amount"), row_number, f"{field}[{index}].amount", positive=True)
        entries.append({"address": address.strip(), "amount": amount})
    return entries


def validate_transaction(record: Dict[str, Any], row_number: int) -> Dict[str, Any]:
    missing = [field for field in REQUIRED_FIELDS if field not in record]
    if missing:
        raise _error(row_number, "schema", f"missing required fields: {', '.join(missing)}")

    txid = record["txid"]
    if not isinstance(txid, str) or not txid.strip():
        raise _error(row_number, "txid", "must be a non-empty string")
    txid = txid.strip()

    timestamp = record["timestamp"]
    if not isinstance(timestamp, str) or not timestamp.strip():
        raise _error(row_number, "timestamp", "must be a non-empty ISO-8601 string")
    try:
        datetime.fromisoformat(timestamp)
    except ValueError as exc:
        raise _error(row_number, "timestamp", f"invalid ISO-8601 value {timestamp!r}") from exc

    inputs = _wallet_entries(record["input_wallet_addresses"], row_number, "input_wallet_addresses")
    outputs = _wallet_entries(record["output_wallet_addresses"], row_number, "output_wallet_addresses")
    total_input = _finite_number(record["total_input_amount"], row_number, "total_input_amount", positive=True)
    fee = _finite_number(record["fee"], row_number, "fee")

    input_sum = sum(item["amount"] for item in inputs)
    output_sum = sum(item["amount"] for item in outputs)
    if not math.isclose(total_input, input_sum, rel_tol=0.0, abs_tol=AMOUNT_TOLERANCE):
        raise _error(row_number, "total_input_amount", f"{total_input} does not match input sum {input_sum}")
    if output_sum - total_input > AMOUNT_TOLERANCE:
        raise _error(row_number, "output_wallet_addresses", "output total exceeds input total")
    expected_fee = total_input - output_sum
    if not math.isclose(fee, expected_fee, rel_tol=0.0, abs_tol=AMOUNT_TOLERANCE):
        raise _error(row_number, "fee", f"{fee} does not match input minus output ({expected_fee})")

    script_type = record["script_type"]
    if script_type not in VALID_SCRIPT_TYPES:
        raise _error(row_number, "script_type", f"unsupported value {script_type!r}")

    label = record["_ground_truth_label"]
    if label not in VALID_LABELS:
        raise _error(row_number, "_ground_truth_label", f"unsupported value {label!r}")

    parsed = dict(record)
    parsed.update(
        {
            "timestamp": timestamp,
            "txid": txid,
            "input_wallet_addresses": inputs,
            "output_wallet_addresses": outputs,
            "total_input_amount": total_input,
            "fee": fee,
            "src_port": _port(record["src_port"], row_number, "src_port"),
            "dst_port": _port(record["dst_port"], row_number, "dst_port"),
        }
    )

    for field in ("src_ip", "dst_ip"):
        try:
            parsed[field] = str(ipaddress.ip_address(record[field]))
        except ValueError as exc:
            raise _error(row_number, field, f"invalid IP address {record[field]!r}") from exc

    wallet_ids = {item["address"] for item in inputs + outputs}
    if txid in wallet_ids or parsed["src_ip"] in wallet_ids or parsed["dst_ip"] in wallet_ids:
        raise _error(row_number, "node identifiers", "wallet, transaction, and IP identifiers must not collide")
    if txid in {parsed["src_ip"], parsed["dst_ip"]}:
        raise _error(row_number, "node identifiers", "transaction and IP identifiers must not collide")

    return parsed


def validate_transactions(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    validated = []
    seen_txids = set()
    identifier_types: Dict[str, str] = {}

    for row_number, record in enumerate(records, start=2):
        parsed = validate_transaction(record, row_number)
        txid = parsed["txid"]
        if txid in seen_txids:
            raise _error(row_number, "txid", f"duplicate transaction ID {txid!r}")
        seen_txids.add(txid)

        identifiers = [(txid, "transaction"), (parsed["src_ip"], "ip"), (parsed["dst_ip"], "ip")]
        identifiers.extend((entry["address"], "wallet") for entry in parsed["input_wallet_addresses"])
        identifiers.extend((entry["address"], "wallet") for entry in parsed["output_wallet_addresses"])
        for identifier, node_type in identifiers:
            previous = identifier_types.get(identifier)
            if previous is not None and previous != node_type:
                raise _error(row_number, "node identifiers", f"{identifier!r} is used as both {previous} and {node_type}")
            identifier_types[identifier] = node_type

        validated.append(parsed)
    return validated


def load_transactions_csv(path: str) -> List[Dict[str, Any]]:
    try:
        with open(path, newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != REQUIRED_FIELDS:
                raise ValueError(
                    f"Invalid transaction CSV schema in {path!r}: expected {REQUIRED_FIELDS}, got {reader.fieldnames}"
                )
            return validate_transactions(reader)
    except OSError as exc:
        raise OSError(f"Unable to read transaction CSV {path!r}: {exc}") from exc
