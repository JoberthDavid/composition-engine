from fastapi import FastAPI

from app.api.exceptions import value_error_handler
from app.api.router import router


app = FastAPI(
    title="Composition Engine",
    version="1.0.0",
    description=(
        "API para resolução, explosão e cálculo de "
        "composições de custos de engenharia."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_exception_handler(
    ValueError,
    value_error_handler,
)

app.include_router(router)