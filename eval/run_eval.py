"""Usage: python -m eval.run_eval eval/data/queries.jsonl out/results.csv [config ...]"""
import csv
import json
import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

CONFIGS = {
    "A_naive":      {"GRAPH_MODE": "adaptive", "FORCE_ROUTE": "simple", "ENABLE_VERIFY": "0", "ENABLE_LOMCP": "0", "ENABLE_AAM": "0"},
    "B_agentic":    {"GRAPH_MODE": "adaptive", "FORCE_ROUTE": "complex", "ENABLE_VERIFY": "0", "ENABLE_LOMCP": "0", "ENABLE_AAM": "0"},
    "full":         {"GRAPH_MODE": "adaptive", "FORCE_ROUTE": "", "ENABLE_ROUTER": "1", "ENABLE_VERIFY": "1", "ENABLE_LOMCP": "1", "ENABLE_AAM": "1"},
    "full_no_router": {"GRAPH_MODE": "adaptive", "FORCE_ROUTE": "complex", "ENABLE_VERIFY": "1", "ENABLE_LOMCP": "1", "ENABLE_AAM": "1"},
    "full_no_lomcp":  {"GRAPH_MODE": "adaptive", "FORCE_ROUTE": "", "ENABLE_VERIFY": "1", "ENABLE_LOMCP": "0", "ENABLE_AAM": "1"},
    "full_no_verify": {"GRAPH_MODE": "adaptive", "FORCE_ROUTE": "", "ENABLE_VERIFY": "0", "ENABLE_LOMCP": "1", "ENABLE_AAM": "1"},
    "full_no_aam":    {"GRAPH_MODE": "adaptive", "FORCE_ROUTE": "", "ENABLE_VERIFY": "1", "ENABLE_LOMCP": "1", "ENABLE_AAM": "0"},
}
KEYS = ["GRAPH_MODE", "FORCE_ROUTE", "ENABLE_ROUTER", "ENABLE_VERIFY", "ENABLE_LOMCP", "ENABLE_AAM"]
COLUMNS = ["config", "id", "label_gold", "answerable", "route", "latency_ms", "confidence", "confidence_score",
           "abstained", "grounded", "retries", "tools_selected", "schema_tokens_full",
           "schema_tokens_selected", "n_sources", "error", "answer"]


def main(queries_path, out_path, names):
    from secondbrain.agent.service import run_turn   # import after dotenv so settings see the env

    unknown = [n for n in names if n not in CONFIGS]
    if unknown:
        sys.exit(f"Unknown config(s): {unknown}. Choose from {list(CONFIGS)}")

    rows = [json.loads(l) for l in open(queries_path, encoding="utf-8") if l.strip()]
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(COLUMNS)
        for name in names:
            for k in KEYS:
                os.environ.pop(k, None)
            os.environ.update(CONFIGS[name])
            for i, row in enumerate(rows, start=1):
                print(f"[{name}] {i}/{len(rows)} {row['id']}", flush=True)
                # fresh thread per query so conversation history never leaks between runs
                try:
                    r = run_turn(row["query"], thread_id=f"eval-{name}-{uuid.uuid4().hex[:8]}",
                                 user_id=f"eval-{name}")
                    error = ""
                except Exception as e:  # one failing query must not lose the whole run
                    r = {"route": None, "confidence": None, "confidence_score": None, "abstained": None,
                         "grounded": None, "sources": [], "metrics": {}, "answer": ""}
                    error = f"{type(e).__name__}: {e}"[:300]
                m = r["metrics"]
                w.writerow([name, row["id"], row.get("label"), row.get("answerable", True), r["route"],
                            m.get("latency_ms"), r["confidence"], r["confidence_score"], r["abstained"],
                            r["grounded"], m.get("retries"), "|".join(m.get("tools_selected") or []),
                            m.get("schema_tokens_full"), m.get("schema_tokens_selected"),
                            len(r["sources"]), error, r["answer"][:400]])
                fh.flush()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:] or list(CONFIGS))
