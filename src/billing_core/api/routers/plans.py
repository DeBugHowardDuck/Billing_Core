from typing import Annotated

from fastapi import APIRouter, Depends

from billing_core.api.deps import get_service
from billing_core.api.schemas import MoneyOut, PlanCreate, PlanOut
from billing_core.application.services import BillingService
from billing_core.domain.plans import Plan

router = APIRouter(prefix="/plans", tags=["plans"])
SvcDep = Annotated[BillingService, Depends(get_service)]


def _to_plan_out(p: Plan) -> PlanOut:
    price = p.monthly_price
    return PlanOut(
        code=p.code,
        name=p.name,
        currency=p.currency,
        monthly_price=MoneyOut(amount=price.amount, currency=price.currency),
        requires_seats=p.requires_seats,
    )


@router.post("", response_model=PlanOut)
def create_plan(payload: PlanCreate, svc: SvcDep):
    plan = Plan.from_config(payload.model_dump())
    svc.plans.add(plan)
    return _to_plan_out(plan)


@router.get("", response_model=list[PlanOut])
def list_plans(svc: SvcDep):
    return [_to_plan_out(p) for p in svc.plans.list()]


@router.get("/{code}", response_model=PlanOut)
def get_plan(code: str, svc: SvcDep):
    plan = svc.plans.get(code)
    return _to_plan_out(plan)
