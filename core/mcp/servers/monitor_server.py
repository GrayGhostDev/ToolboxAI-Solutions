import json
import sys
import threading

from core.coordinators.monitor import Monitor


def main():
    mon = Monitor()
    t = threading.Thread(target=mon.loop, daemon=True)
    t.start()
    for line in sys.stdin:
        try:
            req = json.loads(line)
            if req.get("method") == "ping":
                print(json.dumps({"ok": True}))
            else:
                print(json.dumps({"error": "unknown method"}))
        except Exception as e:
            print(json.dumps({"error": str(e)}))
        sys.stdout.flush()


if __name__ == "__main__":
    main()
