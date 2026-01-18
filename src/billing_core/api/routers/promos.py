from typing import Annotated

from fastapi import APIRouter, Depends

from billing_core.api.deps import get_service
from billing_core.api.schemas import PromoCreate
from billing_core.application.services import BillingService
from billing_core.domain.money import Money
from billing_core.domain.promo import PromoCode

router = APIRouter(prefix="/promos", tags=["promos"])
SvcDep = Annotated[BillingService, Depends(get_service)]

@router.post("")
def create_promo(payload: PromoCreate, svc: SvcDep):
    fixed = None
    if payload.kind == "fixed":
        if not payload.fixed_amount or not payload.currency:
            return {"errors": "fixed promo requires fixed_amount and currency"}
        fixed = Money.of(payload.fixed_amount, payload.currency)

    promo = PromoCode(
        code=payload.code,
        kind=payload.kind,
        percent=payload.percent,
        fixed_discount=fixed,
        valid_until=payload.valid_until,
        is_single_use=payload.is_single_use,
    )
    svc.promos.add(promo)
    return {"status": "created", "code": promo.code}