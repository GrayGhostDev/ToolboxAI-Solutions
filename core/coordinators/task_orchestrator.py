from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from core.coordinators.task_registry import TaskRegistry, TaskState

app = FastAPI(title="ToolboxAI Task Orchestrator", version="0.1.0")
reg = TaskRegistry()

class ClaimRequest(BaseModel):
    worker_id: str
    capability: Optional[str] = None

class TransitionRequest(BaseModel):
    task_id: str

class HeartbeatRequest(BaseModel):
    worker_id: str
    tasks: List[str] = []

@app.get("/health")
def health():
    return {"redis": reg.r.ping(), "ok": True}

@app.post("/claim")
def claim(req: ClaimRequest):
    t = reg.claim(req.worker_id, req.capability)
    return t or {}

@app.post("/start")
def start(req: TransitionRequest):
    if not reg.r.r.get(reg.k_task(req.task_id)):
        raise HTTPException(404, "task not found")
    reg.start(req.task_id); return {"ok": True}

@app.post("/complete")
def complete(req: TransitionRequest):
    if not reg.r.r.get(reg.k_task(req.task_id)):
        raise HTTPException(404, "task not found")
    reg.complete(req.task_id); return {"ok": True}

@app.post("/fail")
def fail(req: TransitionRequest):
    if not reg.r.r.get(reg.k_task(req.task_id)):
        raise HTTPException(404, "task not found")
    reg.fail(req.task_id); return {"ok": True}

@app.post("/heartbeat")
def heartbeat(req: HeartbeatRequest):
    reg.heartbeat(req.worker_id, req.tasks); return {"ok": True}

@app.get("/qstat")
def qstat():
    return reg.qstat()

@app.get("/workers")
def workers():
    return reg.list_workers()
