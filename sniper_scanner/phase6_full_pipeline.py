import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


STEPS = [
    ("PHASE3_SIGNAL_ENGINE", ["python", "sniper_scanner/phase3_signal_engine.py"]),
    ("PHASE4_RANKING", ["python", "sniper_scanner/phase4_rank_opportunities.py"]),
    ("PHASE5_EXECUTION_REPORT", ["python", "sniper_scanner/phase5_execution_report.py"]),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_step(name, cmd):
    print(f"=== {name} ===", flush=True)
    proc = subprocess.run(cmd, text=True)
    return {
        "name": name,
        "cmd": cmd,
        "returncode": proc.returncode,
    }


def main():
    results = []
    failed = False

    for name, cmd in STEPS:
        result = run_step(name, cmd)
        results.append(result)
        if result["returncode"] != 0:
            failed = True
            break

    summary = {
        "timestamp_utc": utc_now(),
        "steps": results,
        "stop_condition": "PASS_PHASE6_FULL_PIPELINE_COMPLETE" if not failed else "STOP_PHASE6_PIPELINE_FAILED",
    }

    Path("phase6_pipeline_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
