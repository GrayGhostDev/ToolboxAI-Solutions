import sys, json
from core.coordinators.policies import check_no_stubs, check_tests, check_coverage, check_lint, check_typecheck

def main():
    for line in sys.stdin:
        try:
            req=json.loads(line)
            if req.get("method")=="review":
                ok1,msg1=check_tests()
                ok2,msg2=check_coverage()
                ok3,msg3=check_lint()
                ok4,msg4=check_typecheck()
                ok5,msg5=check_no_stubs(req.get("diff",""))
                ok= all([ok1,ok2,ok3,ok4,ok5])
                resp={"ok":ok,"checks":[msg1,msg2,msg3,msg4,msg5]}
            else:
                resp={"error":"unknown method"}
        except Exception as e:
            resp={"error":str(e)}
        print(json.dumps(resp)); sys.stdout.flush()

if __name__=="__main__": main()
