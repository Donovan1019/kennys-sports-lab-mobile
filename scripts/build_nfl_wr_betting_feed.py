"""Build a fail-closed WR betting feed from a verified upstream export.

Upstream odds/projection/simulation ingestion must populate data/nfl_wr_betting_input.json.
Never invent a line, probability or simulation.
"""
import json
from pathlib import Path
from scripts.validate_nfl_wr_betting import process

SOURCE = Path("data/nfl_wr_betting_input.json")
OUTPUT = Path("feed/nfl_wr_betting.json")

def main():
    if SOURCE.exists():
        payload = json.loads(SOURCE.read_text())
    else:
        payload = {"picks": []}
    result = process(payload)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    print("Validated", len(result["picks"]), "candidate WR betting picks")

if __name__ == "__main__":
    main()
