import os, time
from core.coordinators.task_registry import TaskRegistry, TaskState

CHECK_INTERVAL = int(os.environ.get("MONITOR_CHECK_SEC","10"))
STALE_WORKER_SEC = int(os.environ.get("STALE_WORKER_SEC","90"))

class Monitor:
    def __init__(self):
        self.reg = TaskRegistry()

    def loop(self):
        while True:
            self.check(); time.sleep(CHECK_INTERVAL)

    def check(self):
        stale = [w for w in self.reg.list_workers() if w["age"] > STALE_WORKER_SEC]
        if stale:
            print(f"[monitor] stale workers: {stale}")
        qstat = self.reg.qstat()
        if qstat.get(TaskState.QUEUED.value,0) > 100:
            print(f"[monitor] backlog high: {qstat}")

if __name__ == "__main__":
    Monitor().loop()
