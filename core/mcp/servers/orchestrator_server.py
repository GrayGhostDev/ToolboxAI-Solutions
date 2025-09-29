import sys, json
from core.coordinators.task_registry import TaskRegistry

def main():
    reg = TaskRegistry()
    for line in sys.stdin:
        try:
            req=json.loads(line)
            method=req.get("method")
            if method=="health":
                resp={"ok": reg.r.ping()}
            elif method=="claim":
                resp=reg.claim(req["worker_id"], req.get("capability"))
            elif method=="start":
                reg.start(req["task_id"]); resp={"ok":True}
            elif method=="complete":
                reg.complete(req["task_id"]); resp={"ok":True}
            elif method=="fail":
                reg.fail(req["task_id"]); resp={"ok":True}
            elif method=="qstat":
                resp=reg.qstat()
            else:
                resp={"error":"unknown method"}
        except Exception as e:
            resp={"error":str(e)}
        sys.stdout.write(json.dumps(resp)+"\n"); sys.stdout.flush()

if __name__=="__main__": main()
