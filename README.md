# Transaction Fraud Detection Simulator

A rule-based fraud detection simulator written in Python. It generates **synthetic** card transactions (no real financial data), scores each one against a set of risk rules, flags the suspicious ones, and measures how well the rules catch the fraud that was injected into the data.

Built as a learning project to connect cybersecurity skills with financial technology: transaction monitoring, risk scoring, and evaluating detection quality.

## Features

- Synthetic data generator with realistic normal spending per customer
- Three injected fraud patterns with ground-truth labels
- Four explainable detection rules, each adding risk points
- Risk score and plain-English reason for every flagged transaction
- Evaluation: precision, recall, and false alarms
- CSV reports for all and flagged transactions
- Unit tests for every rule and the scoring logic
- Pure Python standard library, no installation needed

## How it works

1. **Generate** - for each customer, normal purchases are created around a personal spending level and home city. Then three kinds of fraud are injected and labelled:
   - one very large purchase
   - a burst of 5 purchases within a few minutes
   - a purchase in a different city shortly after one at home
2. **Score** - transactions are processed in time order. Each customer's history is kept, and every rule that fires adds points and a reason.
3. **Flag** - transactions at or above the threshold (default 40) are flagged for investigation.
4. **Evaluate** - flags are compared with the known fraud labels, and reports are saved as CSV files.

### Detection rules

| Rule | Triggers when | Points |
|---|---|---|
| High amount | Amount is more than 5x the customer's average (needs 10+ past transactions) | +50 |
| Impossible travel | City changes less than 2 hours after the previous transaction | +50 |
| Velocity | 3 or more transactions within 10 minutes | +40 |
| Odd hour | Transaction between 01:00 and 05:00 | +20 |

Scores add up, so a transaction that breaks several rules gets a higher risk score.

## Project structure

```
transaction-fraud-detection-simulator/
|-- fraud_detector.py        # generator, rules, scoring, evaluation, CLI
|-- test_fraud_detector.py   # unit tests (unittest)
|-- README.md
|-- .gitignore
```

## Getting started

Requires **Python 3.8 or newer**. No external libraries.

```bash
git clone https://github.com/Gl1tchRajan/transaction-fraud-detection-simulator.git
cd transaction-fraud-detection-simulator
python3 fraud_detector.py
```

### Options

```bash
python3 fraud_detector.py --customers 50 --days 60 --threshold 50 --seed 7
```

| Option | Default | Meaning |
|---|---|---|
| `--customers` | 20 | Number of synthetic customers |
| `--days` | 30 | Days of history to generate |
| `--threshold` | 40 | Risk score at or above which a transaction is flagged |
| `--seed` | 42 | Random seed (same seed gives the same data) |

### Run the tests

```bash
python3 test_fraud_detector.py
```

## Example output

Default settings (`python3 fraud_detector.py`):

```
Transactions analysed : 3180
Actual fraud (synthetic): 160
Flagged by detector    : 133
Caught 121 of 160 fraud cases | precision 91% | recall 76% | false alarms 12

Top 10 highest-risk transactions:
  #636 C003 2026-01-18 13:30    159.65 Kathmandu  score=90  3 transactions within 10 min; city changed Pokhara -> Kathmandu in 1 min
  #2855 C017 2026-01-26 08:19    650.82 Kathmandu  score=90  amount 651 is 9.9x customer average; 3 transactions within 10 min
  #151 C000 2026-01-09 21:00    270.43 Kathmandu  score=50  amount 270 is 10.3x customer average
  ...
```

Two files are written to the working directory: `all_transactions.csv` and `flagged_transactions.csv` (columns: `tx_id, customer_id, timestamp, amount, city, category, is_fraud, score, reasons`).

## Results and what they mean

| Threshold | Flagged | Caught | Precision | Recall | False alarms |
|---|---|---|---|---|---|
| 40 (default) | 133 | 121 / 160 | 91% | 76% | 12 |
| 50 | 69 | 60 / 160 | 87% | 38% | 9 |

- **Precision** = of everything flagged, how much was really fraud.
- **Recall** = of all the fraud, how much was caught.
- Raising the threshold removes some false alarms but misses much more fraud. Choosing a threshold is a trade-off between investigator workload and missed fraud.
- Some fraud, such as the first transactions in a burst, looks normal when it happens, so a simple rule-based detector cannot catch it.

## Limitations

- The data is synthetic, so these numbers show that the method works, **not** real-world accuracy.
- The fraud patterns in the generator are the ones the rules were designed to catch, so results are optimistic.
- Rules use fixed thresholds and are not learned from data.
- Only amount, time, and city are used. There is no device, merchant, or customer-profile information.

## Future improvements

- Compare against a machine learning model (for example, Isolation Forest in scikit-learn)
- Plot precision and recall for different thresholds
- Add rules for merchant category and repeated small "test" charges
- Add per-customer adaptive thresholds

## Disclaimer

Educational project. All data is randomly generated and no real people, accounts, or transactions are involved.

## Author

Rajan Kumar Mahato Tharu - cybersecurity student interested in financial technology and financial cybersecurity.
