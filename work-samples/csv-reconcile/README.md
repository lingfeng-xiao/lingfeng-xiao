# Two exports. What doesn't match?

A small local utility for comparing order, settlement, or other CSV exports by a unique key and amount. Built as an independent work sample, with synthetic example data. No packages to install and no external service receives the data.

## Run

Requires Python 3.9 or later. From this directory:

```sh
python reconcile.py examples/orders.csv examples/settlements.csv
```

Expected CSV output:

```csv
key,status,left_amount,right_amount,right_minus_left
ORDER-002,amount_mismatch,49.90,45.90,-4.00
ORDER-003,missing_right,80.00,,
ORDER-004,missing_left,,30.00,
```

For your own exports, choose columns and an optional absolute tolerance:

```sh
python reconcile.py left.csv right.csv --key invoice_id --amount total --tolerance 0.01
```

Exit status is `0` for matching exports, `1` for differences, and `2` for invalid input. The summary goes to stderr; CSV output goes to stdout. An empty report contains the header only. Exit `1` is expected when running the example above.

## Deliberate limits

- Keys are case-sensitive after trimming whitespace. Duplicate or empty keys are input errors, not silently aggregated records.
- Both files must use the same currency and amount units. This tool does not convert currency or decide accounting policy.
- Amounts use decimal arithmetic, up to 18 significant digits and exponents from -6 to 6. Missing, non-finite, and invalid amounts are rejected. Differences at or below the tolerance are accepted.
- UTF-8 CSV, including a BOM, is supported. Headers must be unique. Commas inside amounts, such as `1,000.00`, are not accepted as numeric values.
- Files are loaded into memory; this is intended for modest exports, not database-scale workloads.
- Treat exported values as data. Spreadsheet software may interpret untrusted keys beginning with formula characters; inspect such data before opening the output in a spreadsheet.

## Verify

```sh
python -m unittest -v
```

The tests cover missing records, amount mismatches, decimal equality, tolerance, duplicate keys, malformed input, BOM handling, and CLI exit codes.

Possible client extensions include composite keys, explicit duplicate aggregation rules, or an XLSX report. Those require an agreed input contract and scope.
