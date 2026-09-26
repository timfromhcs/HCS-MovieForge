"""Supervisor main entry point."""

import signal
import sys
import time
from engine.supervisor.supervisor import ProcessSupervisor


def main() -> None:
    supervisor = ProcessSupervisor()

    def handle_signal(sig, frame):
        supervisor.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    supervisor.start()

    print("[MovieForge Supervisor] Running. Press Ctrl+C or run stop.bat to terminate.")
    try:
        while supervisor.running:
            supervisor.save_state()
            time.sleep(2)
    except KeyboardInterrupt:
        supervisor.stop()


if __name__ == "__main__":
    main()
