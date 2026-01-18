from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from billing_core.api.deps import build_service
from billing_core.domain.errors import BillingError

from .routers.health import router as health_router
from .routers.invoices import router as invoices_router
from .routers.plans import router as plans_router
from .routers.promos import router as promos_router
from .routers.subscriptions import router as subs_router


def create_app() -> FastAPI:
    app = FastAPI(title="Billing Core API", version="0.0.9")

    app.state.service = build_service()

    app.include_router(health_router)
    app.include_router(plans_router)
    app.include_router(subs_router)
    app.include_router(invoices_router)
    app.include_router(promos_router)

    @app.exception_handler(BillingError)
    def handle_billing_error(_: Request, exc: BillingError):
        return JSONResponse(status_code=400,
                            content={"error": exc.__class__.__name__, "message": str(exc)})

    return app

app = create_app()