import csv
from pathlib import Path
from typing import Any


def write_output(output_path: Path, rows: list[Any], fieldnames: list[str]):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
