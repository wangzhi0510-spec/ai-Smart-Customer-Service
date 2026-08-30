from uuid import uuid4
from fastapi import FastAPI,Request
from fastapi.exceptions import RequestValidationError
from backend.app.api.error_handlers import app_error_handler,http_error_handler,validation_error_handler
from backend.app.core.errors import AppError
from backend.app.core.config import Settings
def create_app(settings: Settings | None = None)->FastAPI:
    app=FastAPI(title="AI Smart Customer Service",version="0.1.0")
    app.state.settings = settings or Settings.from_env()
    app.add_exception_handler(AppError,app_error_handler); app.add_exception_handler(RequestValidationError,validation_error_handler); app.add_exception_handler(404,http_error_handler)
    @app.middleware("http")
    async def request_id_middleware(request:Request,call_next):
        request.state.request_id=request.headers.get("X-Request-ID") or str(uuid4()); response=await call_next(request); response.headers["X-Request-ID"]=request.state.request_id; return response
    @app.get("/api/v1/health/live")
    def live_health(): return {"status":"ok"}
    return app
app=create_app()
