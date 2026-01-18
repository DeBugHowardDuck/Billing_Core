from __future__ import annotations

from fastapi import Request

from billing_core.application.services import BillingService
from billing_core.domain.plans import Plan
from billing_core.infrastructure.memory_repos import (
    InMemoryInvoiceRepo,
    InMemoryPlanRepo,
    InMemoryPromoRepo,
    InMemorySubscriptionRepo,
)


def build_service() -> BillingService:
    plans = InMemoryPlanRepo()
    for p in [
        Plan.from_config("free;FREE;Free;EUR"),
        Plan.from_config("flat;PRO;Pro;EUR;20"),
        Plan.from_config("per_seat;TEAM;Team;EUR;10;5"),
    ]:
        plans.add(p)

    return BillingService(
        plans=plans,
        subs=InMemorySubscriptionRepo(),
        invoices=InMemoryInvoiceRepo(),
        promos=InMemoryPromoRepo(),
    )

def get_service(request: Request) -> BillingService:
    return request.app.state.service