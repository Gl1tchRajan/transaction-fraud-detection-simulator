"""
Transaction Fraud Detection Simulator
-------------------------------------
A rule-based fraud detector that runs on SYNTHETIC transaction data.
Educational project: no real financial data is used.

Run:  python fraud_detector.py
      python fraud_detector.py --customers 50 --days 60 --threshold 50
"""

import argparse
import csv
import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta

CITIES = ["Kathmandu", "Pokhara", "Biratnagar", "Birgunj", "Lalitpur"]
CATEGORIES = ["grocery", "transport", "dining", "shopping", "utilities", "online"]


# --------------------------------------------------------------------------
# 1. Data model
# --------------------------------------------------------------------------
@dataclass
class Transaction:
    tx_id: int
    customer_id: str
    timestamp: datetime
    amount: float
    city: str
    category: str
    is_fraud: bool = False              # ground truth (only known because data is synthetic)
    score: int = 0                      # risk score assigned by the detector
    reasons: list = field(default_factory=list)


# --------------------------------------------------------------------------
# 2. Synthetic data generator
# --------------------------------------------------------------------------
def generate_transactions(n_customers=20, days=30, seed=42):
    """Create normal behaviour per customer, then inject labelled fraud patterns."""
    rng = random.Random(seed)
    start = datetime(2026, 1, 1)
    txs = []
    next_id = 1

    def add(customer, ts, amount, city, category, fraud=False):
        nonlocal next_id
        txs.append(Transaction(next_id, customer, ts, round(amount, 2), city, category, fraud))
        next_id += 1

    for c in range(n_customers):
        customer = f"C{c:03d}"
        home = rng.choice(CITIES)
        typical = rng.uniform(20, 120)                # this customer's usual spend

        # Normal behaviour: ~5 purchases/day spread over the day, mostly 8:00-22:00
        for _ in range(days * 5):
            day = rng.randrange(days)
            hour = rng.choices(range(24), weights=[1 if h < 7 else 6 for h in range(24)])[0]
            ts = start + timedelta(days=day, hours=hour,
                                   minutes=rng.randrange(60), seconds=rng.randrange(60))
            amount = max(1.0, rng.gauss(typical, typical * 0.35))
            add(customer, ts, amount, home, rng.choice(CATEGORIES))

        # Fraud type 1: one very large purchase
        for _ in range(2):
            ts = start + timedelta(days=rng.randrange(5, days), hours=rng.randrange(8, 22),
                                   minutes=rng.randrange(60))
            add(customer, ts, typical * rng.uniform(8, 15), home, "online", True)

        # Fraud type 2: rapid burst of 5 purchases within a few minutes
        ts = start + timedelta(days=rng.randrange(5, days), hours=rng.randrange(8, 22))
        for i in range(5):
            add(customer, ts + timedelta(minutes=i), typical * rng.uniform(1.5, 3),
                home, "online", True)

        # Fraud type 3: "impossible travel" - purchase in another city shortly after
        # a normal purchase at home
        ts = start + timedelta(days=rng.randrange(5, days), hours=rng.randrange(9, 20))
        add(customer, ts, typical, home, "dining")
        far = rng.choice([x for x in CITIES if x != home])
        add(customer, ts + timedelta(minutes=30), typical * rng.uniform(2, 4), far, "shopping", True)

    return txs


# --------------------------------------------------------------------------
# 3. Detection rules  (each returns (points, reason) or None)
# --------------------------------------------------------------------------
def rule_high_amount(tx, history):
    """Amount far above this customer's average."""
    if len(history) < 10:
        return None
    avg = sum(t.amount for t in history) / len(history)
    if tx.amount > 5 * avg:
        return 50, f"amount {tx.amount:.0f} is {tx.amount / avg:.1f}x customer average"
    return None


def rule_velocity(tx, history, window_minutes=10, max_tx=3):
    """Too many transactions in a short window."""
    cutoff = tx.timestamp - timedelta(minutes=window_minutes)
    recent = [t for t in history if t.timestamp >= cutoff]
    if len(recent) + 1 >= max_tx:
        return 40, f"{len(recent) + 1} transactions within {window_minutes} min"
    return None


def rule_odd_hour(tx, history):
    """Activity between 01:00 and 05:00."""
    if 1 <= tx.timestamp.hour < 5:
        return 20, f"unusual hour ({tx.timestamp:%H:%M})"
    return None


def rule_impossible_travel(tx, history, max_gap_hours=2):
    """City changed too quickly since the previous transaction."""
    if not history:
        return None
    prev = history[-1]
    gap = (tx.timestamp - prev.timestamp).total_seconds() / 3600
    if prev.city != tx.city and gap < max_gap_hours:
        return 50, f"city changed {prev.city} -> {tx.city} in {gap * 60:.0f} min"
    return None


RULES = [rule_high_amount, rule_velocity, rule_odd_hour, rule_impossible_travel]


# --------------------------------------------------------------------------
# 4. Scoring engine
# --------------------------------------------------------------------------
def score_transactions(txs, rules=RULES):
    """Process transactions in time order, keeping per-customer history."""
    history = defaultdict(list)
    for tx in sorted(txs, key=lambda t: t.timestamp):
        hist = history[tx.customer_id]
        for rule in rules:
            hit = rule(tx, hist)
            if hit:
                tx.score += hit[0]
                tx.reasons.append(hit[1])
        hist.append(tx)
    return txs


# --------------------------------------------------------------------------
# 5. Evaluation and reporting
# --------------------------------------------------------------------------
def evaluate(txs, threshold):
    tp = sum(1 for t in txs if t.score >= threshold and t.is_fraud)
    fp = sum(1 for t in txs if t.score >= threshold and not t.is_fraud)
    fn = sum(1 for t in txs if t.score < threshold and t.is_fraud)
    tn = len(txs) - tp - fp - fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": precision, "recall": recall}


def save_csv(path, txs):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tx_id", "customer_id", "timestamp", "amount", "city",
                    "category", "is_fraud", "score", "reasons"])
        for t in txs:
            w.writerow([t.tx_id, t.customer_id, t.timestamp.isoformat(), t.amount,
                        t.city, t.category, int(t.is_fraud), t.score, "; ".join(t.reasons)])


def main():
    p = argparse.ArgumentParser(description="Rule-based transaction fraud detection simulator")
    p.add_argument("--customers", type=int, default=20)
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--threshold", type=int, default=40, help="score at or above this is flagged")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    txs = score_transactions(generate_transactions(args.customers, args.days, args.seed))
    flagged = [t for t in txs if t.score >= args.threshold]
    m = evaluate(txs, args.threshold)

    print(f"Transactions analysed : {len(txs)}")
    print(f"Actual fraud (synthetic): {m['tp'] + m['fn']}")
    print(f"Flagged by detector    : {len(flagged)}")
    print(f"Caught {m['tp']} of {m['tp'] + m['fn']} fraud cases | "
          f"precision {m['precision']:.0%} | recall {m['recall']:.0%} | "
          f"false alarms {m['fp']}")

    print("\nTop 10 highest-risk transactions:")
    for t in sorted(flagged, key=lambda t: t.score, reverse=True)[:10]:
        print(f"  #{t.tx_id} {t.customer_id} {t.timestamp:%Y-%m-%d %H:%M} "
              f"{t.amount:>9.2f} {t.city:<10} score={t.score:<3} {'; '.join(t.reasons)}")

    save_csv("all_transactions.csv", txs)
    save_csv("flagged_transactions.csv", flagged)
    print("\nSaved all_transactions.csv and flagged_transactions.csv")


if __name__ == "__main__":
    main()
