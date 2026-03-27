from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.db import Base, engine
from app.services.url_safety import UnsafeURLError

Base.metadata.create_all(bind=engine)

app = FastAPI(title="District Status Checker API", version="0.1.0")
app.include_router(router)


@app.exception_handler(UnsafeURLError)
def handle_unsafe_url(_: Request, exc: UnsafeURLError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(LookupError)
def handle_lookup_error(_: Request, exc: LookupError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ValueError)
def handle_value_error(_: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}
