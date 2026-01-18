from datetime import date as dt_date
from typing import Annotated

from fastapi import APIRouter, Depends

from billing_core.api.deps import get_service
from billing_core.api.schemas import (
    CreateSubscriptionResponse,
    SubscriptionCreate,
    SubscriptionOut,
)
from billing_core.application.services import BillingService

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

SvcDep = Annotated[BillingService, Depends(get_service)]


def _to_sub_out(s) -> SubscriptionOut:
    return SubscriptionOut(
        id=s.id,
        created_at=s.created_at,
        customer_id=s.customer_id,
        plan_code=s.plan_code,
        status=s.status.value if hasattr(s.status, "value") else str(s.status),
        start_date=s.start_date,
        current_period_start=s.current_period_start,
        current_period_end=s.current_period_end,
        seats=s.seats,
        promo_code=s.promo_code,
        is_active=s.is_active,
        days_left_in_period=s.days_left_in_period,
    )


@router.post("", response_model=CreateSubscriptionResponse)
def create_subscription(payload: SubscriptionCreate, svc: SvcDep):
    sub, inv = svc.create_subscription(
        customer_id=payload.customer_id,
        plan_code=payload.plan_code,
        start_date=payload.start_date,
        seats=payload.seats,
        trial_days=payload.trial_days,
        period_days=payload.period_days,
    )
    return CreateSubscriptionResponse(
        subscription=_to_sub_out(sub),
        invoice_id=inv.invoice_id if inv else None,
    )


@router.get("/{sub_id}", response_model=SubscriptionOut)
def get_subscription(sub_id: str, svc: SvcDep):
    sub = svc.subs.get(sub_id)
    return _to_sub_out(sub)


@router.post("/{sub_id}/cancel", response_model=SubscriptionOut)
def cancel_subscription(sub_id: str, svc: SvcDep):
    sub = svc.cancel_subscription(sub_id=sub_id)
    return _to_sub_out(sub)


@router.post("/{sub_id}/upgrade")
def upgrade_subscription(sub_id: str, payload: SubscriptionCreate, svc: SvcDep):
    inv = svc.upgrade_subscription(
        sub_id=sub_id,
        new_plan_code=payload.new_plan_code,
        change_date=payload.change_date,
    )
    return {"invoice_id": inv.invoice_id if inv else None}


@router.post("/{sub_id}/change-seats")
def change_seats(sub_id: str, payload: SubscriptionCreate, svc: SvcDep):
    inv = svc.change_seats(
        sub_id=sub_id,
        new_seats=payload.new_seats,
        change_date=payload.change_date,
    )
    return {"invoice_id": inv.invoice_id if inv else None}


@router.post("/{sub_id}/apply-promo", response_model=SubscriptionOut)
def apply_promo(sub_id: str, payload: SubscriptionCreate, svc: SvcDep):
    sub = svc.apply_promo(sub_id=sub_id, promo_code=payload.promo_code, today=dt_date.today())
    return _to_sub_out(sub)
