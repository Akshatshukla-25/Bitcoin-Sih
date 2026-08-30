#!/usr/bin/env python3
"""
data_gen.py — SIH26146 (NTRO) synthetic Bitcoin transaction generator — Part 1

Produces a fully synthetic, offline dataset of Bitcoin-style transactions that
fuses blockchain-layer (wallet/tx) signals with network-layer (IP) signals,
with three planted laundering patterns interleaved into realistic background
noise:

    - peel_chain     : layering via a sequence of hops, each skimming a bit
    - mixer          : fan-out to many wallets, then fan-in consolidation
    - rapid_cashout  : brand-new wallet receives a lump sum and cashes out fast

Output: transactions.csv and transactions.json in --outdir, plus a printed
summary (total count, per-pattern count, unique wallet count, unique IP count).

Usage:
    python3 data_gen.py [--count N] [--seed S] [--outdir DIR]
"""

import argparse
import csv
import json
import os
import random
from datetime import datetime, timedelta

import numpy as np

# ---------------------------------------------------------------------------
# Config (defaults — override via CLI)
# ---------------------------------------------------------------------------
DEFAULT_TOTAL_TRANSACTIONS = 500
DEFAULT_SEED = 42

# Approximate fraction of TOTAL rows each pattern family should occupy.
# Remaining rows are background/normal traffic.
PEEL_CHAIN_ROW_FRACTION = 0.08
MIXER_ROW_FRACTION = 0.15
RAPID_CASHOUT_ROW_FRACTION = 0.07

SCRIPT_TYPES = ["P2PKH", "P2SH", "P2WPKH", "P2WSH"]
SCRIPT_TYPE_WEIGHTS = [0.45, 0.25, 0.25, 0.05]

BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
BECH32_ALPHABET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

# Loosely region-bucketed public-looking IPv4 prefixes, purely to give the
# offline GeoIP-enrichment demo stage some geographic spread. These are NOT
# contacted, resolved, or looked up anywhere in this script.
IP_BLOCKS_BY_REGION = {
    "US": ["3.{b}.{c}.{d}", "4.{b}.{c}.{d}", "12.{b}.{c}.{d}", "50.{b}.{c}.{d}", "108.{b}.{c}.{d}"],
    "IN": ["49.{b}.{c}.{d}", "59.{b}.{c}.{d}", "103.{b}.{c}.{d}", "117.{b}.{c}.{d}", "182.{b}.{c}.{d}"],
    "CN": ["58.{b}.{c}.{d}", "61.{b}.{c}.{d}", "111.{b}.{c}.{d}", "123.{b}.{c}.{d}", "218.{b}.{c}.{d}"],
    "RU": ["5.{b}.{c}.{d}", "37.{b}.{c}.{d}", "77.{b}.{c}.{d}", "91.{b}.{c}.{d}", "95.{b}.{c}.{d}"],
    "DE": ["46.{b}.{c}.{d}", "62.{b}.{c}.{d}", "78.{b}.{c}.{d}", "88.{b}.{c}.{d}", "217.{b}.{c}.{d}"],
    "BR": ["45.{b}.{c}.{d}", "138.{b}.{c}.{d}", "177.{b}.{c}.{d}", "179.{b}.{c}.{d}", "200.{b}.{c}.{d}"],
    "NG": ["105.{b}.{c}.{d}", "154.{b}.{c}.{d}", "197.{b}.{c}.{d}"],
    "SG": ["8.{b}.{c}.{d}", "43.{b}.{c}.{d}", "121.{b}.{c}.{d}", "175.{b}.{c}.{d}"],
    "GB": ["31.{b}.{c}.{d}", "51.{b}.{c}.{d}", "81.{b}.{c}.{d}", "86.{b}.{c}.{d}"],
    "AU": ["1.{b}.{c}.{d}", "27.{b}.{c}.{d}", "101.{b}.{c}.{d}", "203.{b}.{c}.{d}"],
}
REGIONS = list(IP_BLOCKS_BY_REGION.keys())

# Bitcoin P2P port, weighted heavily toward the mainnet default with a little
# variation (RPC / testnet) for realism.
BITCOIN_P2P_PORTS = [8333, 8333, 8333, 8333, 8332, 18333]

GLOBAL_START = datetime(2025, 1, 1, 0, 0, 0)
GLOBAL_WINDOW_DAYS = 30

FIELDNAMES = [
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


# ---------------------------------------------------------------------------
# Low-level synthetic primitives
# ---------------------------------------------------------------------------
def mint_wallet(used_addresses, script_type=None):
    """Mint a brand-new, globally-unique, plausible-looking wallet address."""
    script_type = script_type or random.choices(SCRIPT_TYPES, weights=SCRIPT_TYPE_WEIGHTS)[0]
    while True:
        if script_type in ("P2WPKH", "P2WSH"):
            body_len = 38 if script_type == "P2WPKH" else 58
            addr = "bc1q" + "".join(random.choices(BECH32_ALPHABET, k=body_len))
        else:
            prefix = "1" if script_type == "P2PKH" else "3"
            addr = prefix + "".join(random.choices(BASE58_ALPHABET, k=random.randint(25, 33)))
        if addr not in used_addresses:
            used_addresses.add(addr)
            return addr


def random_ip():
    region = random.choice(REGIONS)
    template = random.choice(IP_BLOCKS_BY_REGION[region])
    b, c, d = random.randint(0, 255), random.randint(0, 255), random.randint(1, 254)
    return template.format(b=b, c=c, d=d)


def random_txid():
    return "".join(random.choices("0123456789abcdef", k=64))


def random_timestamp_in_window():
    offset_seconds = random.uniform(0, GLOBAL_WINDOW_DAYS * 86400)
    return GLOBAL_START + timedelta(seconds=offset_seconds)


def make_tx(timestamp, inputs, outputs, src_ip, dst_ip, label, script_type=None):
    """
    inputs / outputs: list of {"address": str, "amount": float}
    fee is derived as total_input - total_output (never negative/zero).
    """
    script_type = script_type or random.choices(SCRIPT_TYPES, weights=SCRIPT_TYPE_WEIGHTS)[0]
    total_input = round(sum(i["amount"] for i in inputs), 8)
    total_output = round(sum(o["amount"] for o in outputs), 8)
    fee = round(max(total_input - total_output, 0.00000001), 8)
    return {
        "timestamp": timestamp.isoformat(),
        "txid": random_txid(),
        "input_wallet_addresses": inputs,
        "output_wallet_addresses": outputs,
        "total_input_amount": total_input,
        "fee": fee,
        "script_type": script_type,
        "src_ip": src_ip,
        "src_port": random.randint(1024, 65535),
        "dst_ip": dst_ip,
        "dst_port": random.choice(BITCOIN_P2P_PORTS),
        "_ground_truth_label": label,
    }


# ---------------------------------------------------------------------------
# Pattern generators
# ---------------------------------------------------------------------------
def gen_peel_chain(used_addresses, start_time):
    """Wallet A -> B -> C -> ... ; each hop keeps a small randomized skim
    (2-8%) and forwards the rest; hops are minutes apart."""
    n_hops = random.randint(3, 7)
    amount = round(random.uniform(0.5, 8.0), 6)
    current_wallet = mint_wallet(used_addresses)
    t = start_time
    txs = []
    for _ in range(n_hops):
        next_wallet = mint_wallet(used_addresses)
        skim_pct = random.uniform(0.02, 0.08)
        miner_fee = round(random.uniform(0.00001, 0.0005), 8)
        forward_amount = round(max(amount * (1 - skim_pct) - miner_fee, 0.00000001), 8)
        inputs = [{"address": current_wallet, "amount": amount}]
        outputs = [{"address": next_wallet, "amount": forward_amount}]
        txs.append(make_tx(t, inputs, outputs, random_ip(), random_ip(), "peel_chain"))
        t = t + timedelta(minutes=random.uniform(1, 25))
        current_wallet = next_wallet
        amount = forward_amount
    return txs


def gen_mixer(used_addresses, start_time):
    """One source wallet fans out to 5-15 wallets in a tight window, which
    then quietly consolidate down to 1-2 wallets in a later window."""
    source = mint_wallet(used_addresses)
    source_balance = round(random.uniform(2.0, 20.0), 6)
    n_out = random.randint(5, 15)
    fanout_window_minutes = random.uniform(2, 20)
    mixer_wallets = [mint_wallet(used_addresses) for _ in range(n_out)]

    shares = np.random.dirichlet(np.ones(n_out)) * source_balance
    txs = []
    received = {}
    for i in range(n_out):
        amt = round(float(shares[i]), 8)
        fee = round(random.uniform(0.00001, 0.0003), 8)
        amt_after_fee = round(max(amt - fee, 0.00000001), 8)
        received[mixer_wallets[i]] = amt_after_fee
        inputs = [{"address": source, "amount": amt}]
        outputs = [{"address": mixer_wallets[i], "amount": amt_after_fee}]
        tx_time = start_time + timedelta(minutes=random.uniform(0, fanout_window_minutes))
        txs.append(make_tx(tx_time, inputs, outputs, random_ip(), random_ip(), "mixer"))

    consolidation_start = start_time + timedelta(minutes=fanout_window_minutes + random.uniform(5, 60))
    consolidation_window_minutes = random.uniform(10, 90)
    n_final = random.choice([1, 2])
    final_wallets = [mint_wallet(used_addresses) for _ in range(n_final)]

    for wallet in mixer_wallets:
        received_amt = received[wallet]
        final_wallet = random.choice(final_wallets)
        consolidation_ratio = random.uniform(0.85, 0.98)
        fee = round(random.uniform(0.00001, 0.0003), 8)
        out_amt = round(max(received_amt * consolidation_ratio - fee, 0.00000001), 8)
        tx_time = consolidation_start + timedelta(minutes=random.uniform(0, consolidation_window_minutes))
        inputs = [{"address": wallet, "amount": received_amt}]
        outputs = [{"address": final_wallet, "amount": out_amt}]
        txs.append(make_tx(tx_time, inputs, outputs, random_ip(), random_ip(), "mixer"))

    return txs


def gen_rapid_cashout(used_addresses, start_time):
    """A brand-new wallet (minted fresh, no prior appearances) receives a
    lump sum, then forwards 95%+ of it within minutes across 1-3 hops."""
    funder = mint_wallet(used_addresses)
    lump_sum = round(random.uniform(1.0, 15.0), 6)
    victim_wallet = mint_wallet(used_addresses)  # fresh: no prior history anywhere
    fee0 = round(random.uniform(0.00001, 0.0005), 8)

    t = start_time
    inputs = [{"address": funder, "amount": lump_sum}]
    outputs = [{"address": victim_wallet, "amount": round(lump_sum - fee0, 8)}]
    txs = [make_tx(t, inputs, outputs, random_ip(), random_ip(), "rapid_cashout")]

    current_wallet = victim_wallet
    amount = round(lump_sum - fee0, 8)
    n_hops = random.randint(1, 3)
    for _ in range(n_hops):
        next_wallet = mint_wallet(used_addresses)
        forward_pct = random.uniform(0.95, 0.995)
        fee = round(random.uniform(0.00001, 0.0004), 8)
        forward_amt = round(max(amount * forward_pct - fee, 0.00000001), 8)
        t = t + timedelta(minutes=random.uniform(1, 10))
        inputs = [{"address": current_wallet, "amount": amount}]
        outputs = [{"address": next_wallet, "amount": forward_amt}]
        txs.append(make_tx(t, inputs, outputs, random_ip(), random_ip(), "rapid_cashout"))
        current_wallet, amount = next_wallet, forward_amt

    return txs


def gen_normal_chain(used_addresses, background_wallets, start_time):
    """Background/normal traffic with genuine variation: hop counts 0-4,
    randomized timing (seconds to days), non-round amounts, and a mix of
    single/multi input & output shapes."""
    hop_count = random.choices([0, 1, 2, 3, 4], weights=[0.55, 0.20, 0.12, 0.08, 0.05])[0]
    n_tx = hop_count + 1
    txs = []
    t = start_time

    if background_wallets and random.random() < 0.7:
        current_wallet = random.choice(background_wallets)
    else:
        current_wallet = mint_wallet(used_addresses)
        background_wallets.append(current_wallet)

    for _ in range(n_tx):
        n_in = random.randint(2, 3) if random.random() < 0.15 else 1
        n_out = random.randint(2, 3) if random.random() < 0.25 else 1

        inputs = []
        total_in = 0.0
        for k in range(n_in):
            if k == 0:
                addr = current_wallet
            elif background_wallets and random.random() < 0.5:
                addr = random.choice(background_wallets)
            else:
                addr = mint_wallet(used_addresses)
                background_wallets.append(addr)
            amt = round(random.uniform(0.0003, 6.0) * random.choice([1.0, 1.37, 0.61, 2.9, 0.83]), 8)
            inputs.append({"address": addr, "amount": amt})
            total_in += amt

        fee = round(random.uniform(0.00001, 0.0006), 8)
        remaining = max(total_in - fee, 0.00000001)

        outputs = []
        if n_out == 1:
            dest = random.choice(background_wallets) if background_wallets and random.random() < 0.6 else mint_wallet(used_addresses)
            outputs.append({"address": dest, "amount": round(remaining, 8)})
        else:
            shares = np.random.dirichlet(np.ones(n_out))
            for s in shares:
                dest = random.choice(background_wallets) if background_wallets and random.random() < 0.6 else mint_wallet(used_addresses)
                outputs.append({"address": dest, "amount": round(remaining * float(s), 8)})

        txs.append(make_tx(t, inputs, outputs, random_ip(), random_ip(), "normal"))

        gap_bucket = random.random()
        if gap_bucket < 0.4:
            gap = random.uniform(5, 120)          # seconds-ish
        elif gap_bucket < 0.8:
            gap = random.uniform(120, 3600)        # minutes-ish
        else:
            gap = random.uniform(3600, 86400 * 2)  # hours to days
        t = t + timedelta(seconds=gap)

        next_wallet = outputs[0]["address"]
        if next_wallet not in background_wallets:
            background_wallets.append(next_wallet)
        current_wallet = next_wallet

    return txs


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def generate_dataset(total, seed):
    random.seed(seed)
    np.random.seed(seed)

    used_addresses = set()
    background_wallets = []
    for _ in range(30):
        background_wallets.append(mint_wallet(used_addresses))

    peel_budget = max(1, int(total * PEEL_CHAIN_ROW_FRACTION))
    mixer_budget = max(1, int(total * MIXER_ROW_FRACTION))
    cashout_budget = max(1, int(total * RAPID_CASHOUT_ROW_FRACTION))

    all_txs = []
    pattern_counts = {"peel_chain": 0, "mixer": 0, "rapid_cashout": 0, "normal": 0}

    rows = 0
    while rows < peel_budget:
        chain = gen_peel_chain(used_addresses, random_timestamp_in_window())
        all_txs.extend(chain)
        rows += len(chain)
        pattern_counts["peel_chain"] += len(chain)

    rows = 0
    while rows < mixer_budget:
        instance = gen_mixer(used_addresses, random_timestamp_in_window())
        all_txs.extend(instance)
        rows += len(instance)
        pattern_counts["mixer"] += len(instance)

    rows = 0
    while rows < cashout_budget:
        instance = gen_rapid_cashout(used_addresses, random_timestamp_in_window())
        all_txs.extend(instance)
        rows += len(instance)
        pattern_counts["rapid_cashout"] += len(instance)

    planted_total = len(all_txs)
    remaining = max(total - planted_total, 0)
    rows = 0
    while rows < remaining:
        chain = gen_normal_chain(used_addresses, background_wallets, random_timestamp_in_window())
        if rows + len(chain) > remaining:
            chain = chain[: max(1, remaining - rows)]
        all_txs.extend(chain)
        rows += len(chain)
        pattern_counts["normal"] += len(chain)

    # Interleave planted and normal transactions across the full time range.
    all_txs.sort(key=lambda r: r["timestamp"])

    return all_txs, pattern_counts


def write_outputs(all_txs, outdir):
    os.makedirs(outdir, exist_ok=True)
    csv_path = os.path.join(outdir, "transactions.csv")
    json_path = os.path.join(outdir, "transactions.json")

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for tx in all_txs:
            row = dict(tx)
            row["input_wallet_addresses"] = json.dumps(tx["input_wallet_addresses"])
            row["output_wallet_addresses"] = json.dumps(tx["output_wallet_addresses"])
            writer.writerow(row)

    with open(json_path, "w") as f:
        json.dump(all_txs, f, indent=2)

    return csv_path, json_path


def main():
    parser = argparse.ArgumentParser(description="SIH26146 Part 1 — synthetic Bitcoin transaction generator")
    parser.add_argument("--count", type=int, default=DEFAULT_TOTAL_TRANSACTIONS, help="total transaction rows to generate")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="random seed (determinism)")
    parser.add_argument("--outdir", type=str, default=".", help="output directory")
    args = parser.parse_args()

    all_txs, pattern_counts = generate_dataset(args.count, args.seed)
    csv_path, json_path = write_outputs(all_txs, args.outdir)

    unique_wallets = set()
    unique_ips = set()
    for tx in all_txs:
        for i in tx["input_wallet_addresses"]:
            unique_wallets.add(i["address"])
        for o in tx["output_wallet_addresses"]:
            unique_wallets.add(o["address"])
        unique_ips.add(tx["src_ip"])
        unique_ips.add(tx["dst_ip"])

    print("=" * 60)
    print("SIH26146 Part 1 — data_gen.py summary")
    print("=" * 60)
    print(f"Seed: {args.seed}")
    print(f"Total transactions: {len(all_txs)}")
    for k in ["normal", "peel_chain", "mixer", "rapid_cashout"]:
        print(f"  {k}: {pattern_counts[k]}")
    print(f"Unique wallet addresses: {len(unique_wallets)}")
    print(f"Unique IP addresses: {len(unique_ips)}")
    print(f"Wrote: {csv_path}")
    print(f"Wrote: {json_path}")


if __name__ == "__main__":
    main()
