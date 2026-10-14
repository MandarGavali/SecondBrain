"""Print top-1 retrieval-score distributions for answerable vs unanswerable queries.
Usage:  python -m eval.calibrate eval/data/queries.jsonl
Each line: {"query": "...", "answerable": true}
"""
import json
import statistics
import sys

from dotenv import load_dotenv
load_dotenv()

from secondbrain.rag.services.retrieval_service import retrieve_with_scores


def pct(values, p):
    values = sorted(values)
    return values[min(len(values) - 1, int(p * len(values)))]


def main(path):
    ans, unans = [], []
    for line in open(path, encoding="utf-8"):
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("label") == "no_search":
            continue  # chit-chat never reaches retrieval
        pairs = retrieve_with_scores(row["query"], k=4)
        top = pairs[0][1] if pairs else 0.0
        (ans if row.get("answerable", True) else unans).append(top)
    if not ans:
        sys.exit("No answerable queries found in the dataset.")
    print(f"answerable   n={len(ans)}  median={statistics.median(ans):.3f}  p10={pct(ans, .10):.3f}")
    if unans:
        print(f"unanswerable n={len(unans)}  median={statistics.median(unans):.3f}  p90={pct(unans, .90):.3f}")
        print(f"suggested CONF_SCORE_REL_MIN ~ {(statistics.median(unans) + pct(ans, .10)) / 2:.2f}")


if __name__ == "__main__":
    main(sys.argv[1])
