import contextlib
import io
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from reconcile import compare, load_export, main


class ReconciliationTests(unittest.TestCase):
    def test_decimal_equality(self):
        self.assertEqual(compare({"A": Decimal("0.30")}, {"A": Decimal(".3")}, Decimal(0)), [])

    def test_missing_and_mismatch(self):
        actual = compare(
            {"A": Decimal(10), "B": Decimal(2)}, {"A": Decimal(12), "C": Decimal(3)}, Decimal(0)
        )
        self.assertEqual(
            [row[1] for row in actual], ["amount_mismatch", "missing_right", "missing_left"]
        )
        self.assertEqual(actual[0][-1], "2")

    def test_tolerance_is_inclusive(self):
        self.assertEqual(compare({"A": Decimal(1)}, {"A": Decimal("1.01")}, Decimal(".01")), [])

    def test_supported_precision_range(self):
        actual = compare(
            {"A": Decimal("999999999999999999e6")}, {"A": Decimal(".000001")}, Decimal(0)
        )
        self.assertEqual(actual[0][-1], "-999999999999999998999999.999999")

    def test_invalid_inputs_are_rejected(self):
        cases = [
            "order_id,amount\nA,1\nA,2\n",
            "order_id,amount\n,1\n",
            "order_id,amount\nA,NaN\n",
            "order_id,amount\nA,Infinity\n",
            "order_id,amount\nA,abc\n",
            "order_id,amount\nA\n",
            "order_id,amount\nA,1,extra\n",
            "wrong,amount\nA,1\n",
            "order_id,amount,amount\nA,1,2\n",
            "order_id,amount\nA,1e100\n",
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.csv"
            for content in cases:
                with self.subTest(content=content):
                    path.write_text(content, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_export(path, "order_id", "amount")

    def test_bom_and_whitespace(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.csv"
            path.write_text("\ufefforder_id,amount\n A , 1.20 \n", encoding="utf-8")
            self.assertEqual(load_export(path, "order_id", "amount"), {"A": Decimal("1.20")})

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            left, right = Path(directory) / "left.csv", Path(directory) / "right.csv"
            left.write_text("order_id,amount\nA,1\n", encoding="utf-8")
            right.write_text("order_id,amount\nA,2\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
                io.StringIO()
            ):
                self.assertEqual(main([str(left), str(left)]), 0)
                self.assertEqual(main([str(left), str(right)]), 1)
                self.assertEqual(main([str(left), str(right), "--tolerance", "-1"]), 2)
                self.assertEqual(main([str(left), str(right), "--tolerance", "NaN"]), 2)


if __name__ == "__main__":
    unittest.main()
