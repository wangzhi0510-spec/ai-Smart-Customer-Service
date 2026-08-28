from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="AI Smart Customer Service", version="0.1.0")

    @app.get("/api/v1/health/live")
    def live_health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

