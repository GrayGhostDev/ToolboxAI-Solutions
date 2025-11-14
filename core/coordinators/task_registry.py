import json
import os
import time
import uuid
from enum import Enum
from typing import Any, Optional

from .adapters.redis import RedisAdapter

# Use a distinct prefix to avoid any collisions with existing Redis usages
KEY_PREFIX = os.environ.get("TERMQ_PREFIX", "termq")
CLAIM_TTL_SEC = int(os.environ.get("TERMQ_CLAIM_TTL_SEC", "300"))
HEARTBEAT_TTL_SEC = int(os.environ.get("TERMQ_HEARTBEAT_TTL_SEC", "30"))
MAX_RETRIES = int(os.environ.get("TERMQ_MAX_RETRIES", "3"))


class TaskState(str, Enum):
    QUEUED = "queued"
    CLAIMED = "claimed"
    IN_PROGRESS = "in_progress"
    NEEDS_REVIEW = "needs_review"
    NEEDS_FIX = "needs_fix"
    BLOCKED = "blocked"
    COMPLETE = "complete"
    FAILED = "failed"


class TaskRegistry:
    """Redis-backed task queue with claim locks and heartbeats.
    Keys are namespaced under KEY_PREFIX to avoid collisions.
    """

    def __init__(self, r: Optional[RedisAdapter] = None):
        self.r = r or RedisAdapter()

    def _k(self, *parts: str) -> str:
        return ":".join([KEY_PREFIX, *parts])

    def k_task(self, tid):
        return self._k("task", tid)

    def k_state(self, state):
        return self._k("tasks", "state", state)

    def k_lock(self, tid):
        return self._k("task", "lock", tid)

    def k_claim(self, tid):
        return self._k("task", "claim", tid)

    def k_worker_hb(self, wid):
        return self._k("worker", "hb", wid)

    def enqueue(
        self,
        payload: dict[str, Any],
        priority: float = 1.0,
        idempotency_key: Optional[str] = None,
    ) -> str:
        tid = idempotency_key or str(uuid.uuid4())
        now = time.time()
        task = {
            "id": tid,
            "state": TaskState.QUEUED.value,
            "priority": priority,
            "created_at": now,
            "updated_at": now,
            "retries": 0,
            "claimed_by": "",
            "payload": payload,
        }
        pipe = self.r.r.pipeline()
        pipe.set(self.k_task(tid), json.dumps(task))
        # Keep a zset per state for quick visibility (score=newest updated_at)
        pipe.zadd(self.k_state(TaskState.QUEUED.value), {tid: now})
        pipe.execute()
        return tid

    def claim(self, worker_id: str, capability: Optional[str] = None) -> Optional[dict[str, Any]]:
        # Try first N tasks from QUEUED and match capability if provided
        tids = [
            tid
            for tid, _ in self.r.r.zrange(
                self.k_state(TaskState.QUEUED.value), 0, 49, withscores=True
            )
        ]
        for tid in tids:
            raw = self.r.r.get(self.k_task(tid))
            task = json.loads(raw) if raw else None
            if not task:
                self.r.r.zrem(self.k_state(TaskState.QUEUED.value), tid)
                continue
            if capability and task["payload"].get("capability") not in [
                capability,
                "*",
                None,
            ]:
                continue
            # Acquire lock (NX with TTL)
            if self.r.r.set(self.k_lock(tid), worker_id, nx=True, ex=CLAIM_TTL_SEC):
                task["state"] = TaskState.CLAIMED.value
                task["claimed_by"] = worker_id
                task["updated_at"] = time.time()
                pipe = self.r.r.pipeline()
                pipe.set(self.k_task(tid), json.dumps(task))
                pipe.zrem(self.k_state(TaskState.QUEUED.value), tid)
                pipe.set(self.k_claim(tid), worker_id, ex=CLAIM_TTL_SEC)
                pipe.execute()
                return task
        return None

    def heartbeat(self, worker_id: str, tasks: list[str]):
        pipe = self.r.r.pipeline()
        pipe.set(self.k_worker_hb(worker_id), int(time.time()), ex=HEARTBEAT_TTL_SEC)
        for tid in tasks:
            if self.r.r.get(self.k_lock(tid)) == worker_id:
                pipe.expire(self.k_lock(tid), CLAIM_TTL_SEC)
                pipe.expire(self.k_claim(tid), CLAIM_TTL_SEC)
        pipe.execute()

    def start(self, tid: str):
        raw = self.r.r.get(self.k_task(tid))
        t = json.loads(raw) if raw else None
        if not t:
            return
        t["state"] = TaskState.IN_PROGRESS.value
        t["updated_at"] = time.time()
        self.r.r.set(self.k_task(tid), json.dumps(t))
        self.r.r.zadd(self.k_state(TaskState.IN_PROGRESS.value), {tid: t["updated_at"]})

    def complete(self, tid: str):
        raw = self.r.r.get(self.k_task(tid))
        t = json.loads(raw) if raw else None
        if not t:
            return
        t["state"] = TaskState.COMPLETE.value
        t["updated_at"] = time.time()
        pipe = self.r.r.pipeline()
        pipe.set(self.k_task(tid), json.dumps(t))
        pipe.delete(self.k_lock(tid))
        pipe.delete(self.k_claim(tid))
        pipe.zadd(self.k_state(TaskState.COMPLETE.value), {tid: t["updated_at"]})
        pipe.execute()

    def fail(self, tid: str, requeue: bool = True):
        raw = self.r.r.get(self.k_task(tid))
        t = json.loads(raw) if raw else None
        if not t:
            return
        t["retries"] = int(t.get("retries", 0)) + 1
        self.r.r.set(self.k_task(tid), json.dumps(t))
        if requeue and t["retries"] <= MAX_RETRIES:
            self.requeue(tid)
        else:
            t["state"] = TaskState.FAILED.value
            t["updated_at"] = time.time()
            self.r.r.set(self.k_task(tid), json.dumps(t))
            self.r.r.zadd(self.k_state(TaskState.FAILED.value), {tid: t["updated_at"]})

    def requeue(self, tid: str):
        raw = self.r.r.get(self.k_task(tid))
        t = json.loads(raw) if raw else None
        if not t:
            return
        t["state"] = TaskState.QUEUED.value
        t["claimed_by"] = ""
        t["updated_at"] = time.time()
        pipe = self.r.r.pipeline()
        pipe.set(self.k_task(tid), json.dumps(t))
        pipe.zadd(self.k_state(TaskState.QUEUED.value), {tid: t["updated_at"]})
        pipe.delete(self.k_lock(tid))
        pipe.delete(self.k_claim(tid))
        pipe.execute()

    def qstat(self) -> dict[str, int]:
        states = [s.value for s in TaskState]
        return {s: self.r.r.zcard(self.k_state(s)) for s in states}

    def list_workers(self) -> list[dict[str, Any]]:
        keys = self.r.r.keys(self._k("worker", "hb", "*"))
        out = []
        now = int(time.time())
        for k in keys:
            wid = k.split(":")[-1]
            try:
                ts = int(self.r.r.get(k) or 0)
            except Exception:
                ts = 0
            out.append({"worker_id": wid, "last_seen": ts, "age": now - ts})
        return out
