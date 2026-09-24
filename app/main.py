from fastapi import FastAPI

from app.api.exceptions import value_error_handler
from app.api.router import router


app = FastAPI(
    title="Composition Engine",
    version="1.0.0",
)

app.add_exception_handler(
    ValueError,
    value_error_handler,
)

app.include_router(router)