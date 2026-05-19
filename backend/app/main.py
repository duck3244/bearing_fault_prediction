"""FastAPI entry point for the bearing-fault-prediction service."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import analyze, bearing, health, model, sample
from app.settings import settings
from app.state import state

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
log = logging.getLogger('app')


@asynccontextmanager
async def lifespan(app: FastAPI):
    state.bootstrap_classifier()
    yield


app = FastAPI(
    title='Bearing Fault Prediction API',
    version='0.2.0',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_: Request, exc: StarletteHTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        body = detail
    else:
        body = {'error': detail}
    return JSONResponse(status_code=exc.status_code, content=body)


app.include_router(health.router)
app.include_router(analyze.router)
app.include_router(sample.router)
app.include_router(bearing.router)
app.include_router(model.router)
