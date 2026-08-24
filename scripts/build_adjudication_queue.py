"""Build the frozen, blinded adjudication queue. Run ONCE.

Composition:
  * 300 items from the top of the relational detector's ranking (flagged)
  * 50 items drawn at random from items the detector did NOT flag (controls)

The two strata are shuffled together and the stratum is NOT shown during
adjudication. Without controls you can compute precision but not recall, and
prevalence cannot be estimated at all.

The queue is written once and content-hashed. Rebuilding it after labelling
starts would invalidate the labels, so the script refuses to overwrite.

Usage:  python -m scripts.build_adjudication_queue
"""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

FLAGS = Path("data/benchmark_v1_1_candidate/underspecified.json")
ITEMS = Path("data/benchmark_v1_1_candidate/clean_items.jsonl")
OUT = Path("data/benchmark_v1_1_candidate/adjudication_queue.json")

N_FLAGGED = 300
N_CONTROL = 50
SEED = 20260824


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"{OUT} already exists - refusing to rebuild a live queue")

    rep = json.loads(FLAGS.read_text())
    flagged = rep["flagged_ids"]
    all_ids = [json.loads(l)["item_id"] for l in open(ITEMS, encoding="utf-8")]
    unflagged = [i for i in all_ids if i not in set(flagged)]

    rng = random.Random(SEED)
    take_flagged = flagged[:N_FLAGGED]
    take_control = rng.sample(unflagged, min(N_CONTROL, len(unflagged)))

    queue = ([{"item_id": i, "stratum": "flagged", "rank": n}
              for n, i in enumerate(take_flagged)]
             + [{"item_id": i, "stratum": "control", "rank": None}
                for i in take_control])
    rng.shuffle(queue)

    payload = {
        "seed": SEED,
        "n_flagged_total": len(flagged),
        "n_unflagged_total": len(unflagged),
        "sampled_flagged": len(take_flagged),
        "sampled_control": len(take_control),
        "queue": queue,
    }
    body = json.dumps(payload, indent=2)
    payload["sha256"] = hashlib.sha256(body.encode()).hexdigest()
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {OUT}: {len(queue)} items "
          f"({len(take_flagged)} flagged + {len(take_control)} control, shuffled, blinded)")


if __name__ == "__main__":
    main()
