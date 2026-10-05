"""Confere evidencia serial real; nao gera nem simula mensagens do firmware."""
import argparse
import json
from pathlib import Path
import re


def check(text):
    rows = re.findall(r"replay=(\d+) test_index=(\d+).*?parity=(PASS|FAIL)", text)
    reference = Path(__file__).resolve().parents[1] / "ml/reports/replay_reference.json"
    expected_indices = json.loads(reference.read_text(encoding="utf-8"))["test_indices_zero_based"]
    seen = {int(r): (int(i), status) for r, i, status in rows}
    return (all(seen.get(i) == (expected_indices[i], "PASS") for i in range(6))
            and "REPLAY_SUMMARY passed=6 total=6 status=PASS" in text
            and not any(status == "FAIL" for _, _, status in rows))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=Path)
    args = parser.parse_args()
    success = check(args.log.read_text(encoding="utf-8", errors="replace"))
    print("Evidencia REPLAY: " + ("PASS" if success else "FAIL/incompleta"))
    raise SystemExit(0 if success else 1)


if __name__ == "__main__":
    main()
