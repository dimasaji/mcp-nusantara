"""Print recorded verification outcomes, keeping subtests separate."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folders", nargs="+", type=Path)
    parser.add_argument("--failures", action="store_true")
    args = parser.parse_args()
    for folder in args.folders:
        data = json.loads((folder / "results.json").read_text(encoding="utf-8"))
        print(folder.name, data.get("outcome_counts"), "exit", data["exit_code"])
        if args.failures:
            for report in data["reports"]:
                if report["outcome"] == "failed":
                    print(report["nodeid"], report["detail"][-450:].replace("\n", " "))


if __name__ == "__main__":
    main()
