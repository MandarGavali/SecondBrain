"""P3 experiment: stale-fact retrieval rate with and without AAM.

For each pair in memory_conflicts.jsonl (old fact, new fact, probe question):
  write old -> (reflect) -> write new -> (reflect) -> recall with the probe.
A pair is STALE if the recalled active memories still contain the old fact's distinctive
value (field "old_value") and FRESH if they contain "new_value".

  ENABLE_AAM=1: facts go through reflect_session (conflict judge + deprecation),
                recall is filtered by the Mongo status table.
  ENABLE_AAM=0: baseline -- facts are written with Mem0's own per-turn inference
                (extract_and_save_memory), recall is unfiltered.

Usage:  python -m eval.memory_drift eval/data/memory_conflicts.jsonl out/memory_drift.csv
Each line: {"id": "c01", "old": "...", "new": "...", "probe": "...", "old_value": "2 days", "new_value": "3 days"}
LLM cost per pair: ~4 Gemini calls with AAM, ~2 without -- mind the free-tier daily quota.
"""
import csv
import json
import os
import sys
import time
import uuid

from dotenv import load_dotenv
load_dotenv()


def _write(user_id: str, fact: str, aam: bool) -> None:
    from secondbrain.memory.memory_manager import get_memory_manager
    from secondbrain.memory.reflection import reflect_session

    if aam:
        reflect_session(user_id, [{"role": "user", "content": fact}])
    else:
        get_memory_manager().extract_and_save_memory(user_id=user_id, user_message=fact, assistant_message="Noted.")


def _recall(user_id: str, probe: str) -> list[str]:
    from secondbrain.memory.memory_manager import get_memory_manager
    from secondbrain.memory.reflection import filter_active

    found = get_memory_manager().get_long_term(user_id=user_id, query=probe)
    return [m.get("memory", "") for m in filter_active(found, user_id)["results"]]


def main(pairs_path, out_path):
    aam = os.getenv("ENABLE_AAM", "1").strip().lower() in {"1", "true", "yes", "on"}
    rows = [json.loads(l) for l in open(pairs_path, encoding="utf-8") if l.strip()]
    stale = fresh = 0
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "aam", "stale", "fresh", "recalled", "error"])
        for row in rows:
            user_id = f"drift-{'aam' if aam else 'base'}-{uuid.uuid4().hex[:8]}"  # isolated memory per pair
            error, recalled = "", []
            try:
                _write(user_id, row["old"], aam)
                _write(user_id, row["new"], aam)
                time.sleep(1)  # Qdrant indexing is near-instant, but give it a beat
                recalled = _recall(user_id, row["probe"])
            except Exception as e:
                error = f"{type(e).__name__}: {e}"[:300]
            text = " ".join(recalled).lower()
            is_stale = row["old_value"].lower() in text
            is_fresh = row["new_value"].lower() in text
            stale += is_stale
            fresh += is_fresh
            w.writerow([row["id"], aam, is_stale, is_fresh, " || ".join(recalled), error])
            fh.flush()
            print(f"{row['id']}: stale={is_stale} fresh={is_fresh} {error}", flush=True)

    n = len(rows) or 1
    print(f"\nENABLE_AAM={int(aam)}  stale-fact rate = {stale / n:.0%}   fresh-fact rate = {fresh / n:.0%}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
