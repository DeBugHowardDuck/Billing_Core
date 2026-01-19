from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from billing_core.domain.errors import (
    BillingError,
    InvalidStateTransitionError,
    InvoiceNotFoundError,
    PromoCodeNotFoundError,
    PromoNotValidError,
    SubscriptionNotFoundError,
)
from billing_core.domain.plans import PlanNotFoundError


def billing_error_handler(_: Request, exc: BillingError) -> JSONResponse:
    # 404
    if isinstance(
        exc, (PlanNotFoundError, SubscriptionNotFoundError, InvoiceNotFoundError, PromoCodeNotFoundError, PromoNotValidError)
    ):
        return JSONResponse(status_code=404, content={"error": exc.__class__.__name__, "message": str(exc)})

    # 409
    if isinstance(exc, InvalidStateTransitionError):
        return JSONResponse(status_code=409, content={"error": exc.__class__.__name__, "message": str(exc)})

    # 400
    if isinstance(exc, PromoCodeNotFoundError):
        return JSONResponse(status_code=400, content={"error": exc.__class__.__name__, "message": str(exc)})

    return JSONResponse(status_code=400, content={"error": exc.__class__.__name__, "message": str(exc)})
