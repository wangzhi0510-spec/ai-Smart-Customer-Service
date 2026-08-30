from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from backend.app.core.errors import AppError,error_envelope
def request_id_for(request): return getattr(request.state,"request_id",request.headers.get("X-Request-ID",""))
async def app_error_handler(request:Request, exc:AppError): return JSONResponse(status_code=exc.status_code, content=error_envelope(exc,request_id_for(request)))
async def http_error_handler(request:Request, exc:HTTPException):
    e=AppError("NOT_FOUND" if exc.status_code==404 else "HTTP_ERROR",str(exc.detail),exc.status_code)
    return JSONResponse(status_code=exc.status_code, content=error_envelope(e,request_id_for(request)))
async def validation_error_handler(request:Request, exc:RequestValidationError): return JSONResponse(status_code=422, content=error_envelope(AppError("VALIDATION_ERROR","请求参数无效",422,{"errors":[{"loc":e.get("loc"),"msg":e.get("msg"),"type":e.get("type")} for e in exc.errors()]}),request_id_for(request)))
