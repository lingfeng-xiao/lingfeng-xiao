"""Compare two CSV exports without sending their contents to a service."""

import argparse
import csv
import sys
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path


def load_export(path, key_column, amount_column):
    records = {}
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        columns = reader.fieldnames or []
        if len(columns) != len(set(columns)):
            raise ValueError(f"{path}: duplicate column names")
        for column in (key_column, amount_column):
            if column not in columns:
                raise ValueError(f"{path}: missing column {column!r}")
        for row in reader:
            line = reader.line_num
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{path}:{line}: row has the wrong number of fields")
            key = row[key_column].strip()
            if not key:
                raise ValueError(f"{path}:{line}: empty key")
            if key in records:
                raise ValueError(f"{path}:{line}: duplicate key {key!r}")
            try:
                amount = Decimal(row[amount_column].strip())
            except InvalidOperation as error:
                raise ValueError(f"{path}:{line}: invalid amount for {key!r}") from error
            if not amount.is_finite():
                raise ValueError(f"{path}:{line}: amount must be finite for {key!r}")
            # Bound input precision; compare() allows enough precision for the full range.
            if len(amount.as_tuple().digits) > 18 or not -6 <= amount.as_tuple().exponent <= 6:
                raise ValueError(f"{path}:{line}: amount exceeds supported precision")
            records[key] = amount
    return records


def compare(left, right, tolerance):
    differences = []
    for key in sorted(left.keys() | right.keys()):
        if key not in left:
            differences.append((key, "missing_left", "", str(right[key]), ""))
        elif key not in right:
            differences.append((key, "missing_right", str(left[key]), "", ""))
        else:
            with localcontext() as context:
                context.prec = 40
                delta = right[key] - left[key]
            if delta.copy_abs() > tolerance:
                differences.append(
                    (key, "amount_mismatch", str(left[key]), str(right[key]), str(delta))
                )
    return differences


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--key", default="order_id")
    parser.add_argument("--amount", default="amount")
    parser.add_argument("--tolerance", default="0")
    args = parser.parse_args(argv)
    try:
        tolerance = Decimal(args.tolerance)
        if not tolerance.is_finite() or tolerance < 0:
            raise ValueError("tolerance must be a finite non-negative number")
        left = load_export(args.left, args.key, args.amount)
        right = load_export(args.right, args.key, args.amount)
        differences = compare(left, right, tolerance)
    except (OSError, UnicodeError, csv.Error, ValueError, InvalidOperation) as error:
        print(f"Input error: {error}", file=sys.stderr)
        return 2
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(("key", "status", "left_amount", "right_amount", "right_minus_left"))
    writer.writerows(differences)
    print(
        f"Left: {len(left)} rows; right: {len(right)} rows; differences: {len(differences)}",
        file=sys.stderr,
    )
    return 1 if differences else 0


if __name__ == "__main__":
    sys.exit(main())
