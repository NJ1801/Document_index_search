from typing import Any, Optional

def success_response(code:int, message:str, results:Any):
    return {"status":"success","code":code,"message":message,"results":results}

def failure_response(code:int, message:str, results:Optional[Any]=None):
    return {"status":"failure","code":code,"message":message,"results":results}
