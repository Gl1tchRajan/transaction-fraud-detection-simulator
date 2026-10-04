import unittest
from datetime import datetime, timedelta

from fraud_detector import (Transaction, rule_high_amount, rule_velocity,
                            rule_odd_hour, rule_impossible_travel, score_transactions)

T0 = datetime(2026, 1, 10, 12, 0)


def tx(i, minutes=0, amount=50.0, city="Kathmandu", hour_override=None):
    ts = T0 + timedelta(minutes=minutes)
    if hour_override is not None:
        ts = ts.replace(hour=hour_override)
    return Transaction(i, "C000", ts, amount, city, "online")


class RuleTests(unittest.TestCase):
    def test_high_amount_flags_outlier(self):
        history = [tx(i, minutes=-i * 60, amount=50) for i in range(1, 15)]
        self.assertIsNotNone(rule_high_amount(tx(99, amount=400), history))

    def test_high_amount_ignores_normal(self):
        history = [tx(i, minutes=-i * 60, amount=50) for i in range(1, 15)]
        self.assertIsNone(rule_high_amount(tx(99, amount=60), history))

    def test_high_amount_needs_history(self):
        self.assertIsNone(rule_high_amount(tx(1, amount=9999), []))

    def test_velocity_flags_burst(self):
        history = [tx(1, minutes=-2), tx(2, minutes=-1)]
        self.assertIsNotNone(rule_velocity(tx(3), history))

    def test_velocity_ignores_spread_out(self):
        history = [tx(1, minutes=-300), tx(2, minutes=-200)]
        self.assertIsNone(rule_velocity(tx(3), history))

    def test_odd_hour(self):
        self.assertIsNotNone(rule_odd_hour(tx(1, hour_override=3), []))
        self.assertIsNone(rule_odd_hour(tx(2, hour_override=14), []))

    def test_impossible_travel(self):
        history = [tx(1, minutes=-20, city="Kathmandu")]
        self.assertIsNotNone(rule_impossible_travel(tx(2, city="Pokhara"), history))
        self.assertIsNone(rule_impossible_travel(tx(3, city="Kathmandu"), history))

    def test_scoring_accumulates(self):
        txs = [tx(1, minutes=0, city="Kathmandu"), tx(2, minutes=10, city="Pokhara")]
        scored = score_transactions(txs)
        self.assertGreaterEqual(scored[1].score, 50)


if __name__ == "__main__":
    unittest.main()
