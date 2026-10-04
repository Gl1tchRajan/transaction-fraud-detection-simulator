
# transaction-fraud-detection-simulator

# Transaction Fraud Detection Simulator

A rule-based fraud detector written in Python. It generates **synthetic** card transactions (no real financial data), scores each one with a set of risk rules, and reports how well the rules catch the injected fraud.

## How it works
1. **Generator** creates normal spending for each customer, then injects three labelled fraud patterns: a very large purchase, a rapid burst of purchases, and a purchase in a different city shortly after one at home.
2. **Rules** add risk points to each transaction:
   - High amount (> 5x the customer's average): +50
   - Impossible travel (city changes within 2 hours): +50
   - Velocity (3+ transactions in 10 minutes): +40
   - Odd hour (01:00-05:00): +20
3. **Threshold** (default 40): transactions at or above it are flagged.
4. **Evaluation** compares flags to the known fraud labels (precision, recall, false alarms) and exports CSV reports.

## Run
```
python fraud_detector.py
python fraud_detector.py --customers 50 --days 60 --threshold 50
python test_fraud_detector.py
```
Requires Python 3.8+ and no external libraries.

## Results (default settings)
3,180 transactions, 160 injected fraud cases: caught 121, precision 91%, recall 76%, 12 false alarms.

## Limitations
- Data is synthetic, so real-world performance would differ.
- Rules are fixed thresholds, not learned from data.
- Fraud in the generator follows simple patterns that the rules were designed to catch.

## Ideas for improvement
- Compare against a scikit-learn model (e.g. Isolation Forest).
- Tune thresholds and plot precision/recall for different values.
- Add rules for merchant category and repeated small test charges.

