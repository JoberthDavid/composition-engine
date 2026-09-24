from fastapi import Request
from fastapi.responses import JSONResponse


async def value_error_handler(
    request: Request,
    exc: ValueError,
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "detail": str(exc),
        },
    )