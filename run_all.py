"""Start the four implemented OzAgriMate services locally.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

SERVICES = [
    ("Farm and Device Management Service", "services.farm_device_management_service.main:app", 8001),
    ("Telemetry Ingestion Service", "services.telemetry_ingestion_service.main:app", 8002),
    ("Monitoring and Alert Service", "services.monitoring_alert_service.main:app", 8003),
    ("Irrigation Control Service", "services.irrigation_control_service.main:app", 8004),
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--keep-events", action="store_true", help="keep previous local event-bus logs")
    args = parser.parse_args()

    bus = Path(os.environ.get("OZAGRIMATE_EVENT_BUS_DIR", ROOT / ".local_event_bus"))
    if bus.exists() and not args.keep_events:
        shutil.rmtree(bus)
    env = {**os.environ, "OZAGRIMATE_EVENT_BUS_DIR": str(bus), "PYTHONPATH": str(ROOT)}

    processes = []
    for name, target, port in SERVICES:
        cmd = [sys.executable, "-m", "uvicorn", target, "--port", str(port), "--log-level", "warning"]
        processes.append(subprocess.Popen(cmd, cwd=ROOT, env=env))
        print(f"  {name:<38} http://localhost:{port}/docs")
    print("\nAll services started. Local event bus:", bus)
    print("Press Ctrl+C to stop.\n")

    try:
        while all(p.poll() is None for p in processes):
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for p in processes:
            if p.poll() is None:
                p.terminate()
        for p in processes:
            p.wait(timeout=10)
        print("All services stopped.")


if __name__ == "__main__":
    main()
