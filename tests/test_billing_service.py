from datetime import date, timedelta

import pytest

from billing_core.application.services import BillingService
from billing_core.domain.errors import PromoNotValidError
from billing_core.domain.plans import Plan
from billing_core.domain.promo import PromoCode
from billing_core.infrastructure.memory_repos import (
    InMemoryInvoiceRepo,
    InMemoryPlanRepo,
    InMemoryPromoRepo,
    InMemorySubscriptionRepo,
)


def _service_with_default_plans() -> BillingService:
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


def test_create_paid_subscription_creates_invoice() -> None:
    svc = _service_with_default_plans()

    sub, inv = svc.create_subscription(
        customer_id="cust_1",
        plan_code="PRO",
        start_date=date(2026, 1, 1),
        trial_days=0,
    )

    assert inv is not None
    assert str(inv.total) == "20.00 EUR"
    assert sub.plan_code == "PRO"


def test_create_free_subscription_no_invoice() -> None:
    svc = _service_with_default_plans()

    sub, inv = svc.create_subscription(
        customer_id="cust_1",
        plan_code="FREE",
        start_date=date(2026, 1, 1),
    )

    assert inv is None
    assert sub.plan_code == "FREE"


def test_upgrade_subscription_creates_proration_invoice() -> None:
    svc = _service_with_default_plans()

    sub, _ = svc.create_subscription(
        customer_id="cust_1",
        plan_code="PRO",
        start_date=date(2026, 1, 1),
        seats=3,
        trial_days=0,
        period_days=30,
    )

    # PRO (20) -> TEAM seats=3 (25) на середине периода => 0.5
    # кредит = -10.00, начисление = +12.50, итого +2.50
    inv = svc.upgrade_subscription(
        sub_id=sub.id,
        new_plan_code="TEAM",
        change_date=date(2026, 1, 1) + timedelta(days=15),
    )

    assert inv is not None
    assert str(inv.total) == "2.50 EUR"


def test_change_seats_creates_proration_invoice() -> None:
    svc = _service_with_default_plans()

    sub, _ = svc.create_subscription(
        customer_id="cust_1",
        plan_code="TEAM",
        start_date=date(2026, 1, 1),
        seats=2,  # TEAM: 10 + 5*2 = 20
        trial_days=0,
        period_days=30,
    )

    # seats 2 -> 4: 20 -> 30, на середине => кредит -10, начисление +15 => +5
    inv = svc.change_seats(
        sub_id=sub.id,
        new_seats=4,
        change_date=date(2026, 1, 1) + timedelta(days=15),
    )

    assert inv is not None
    assert str(inv.total) == "5.00 EUR"


def test_apply_single_use_promo_marks_used() -> None:
    svc = _service_with_default_plans()
    svc.promos.add(PromoCode(code="ONCE10", kind="percent", percent=10, is_single_use=True))

    sub, _ = svc.create_subscription(
        customer_id="cust_1",
        plan_code="PRO",
        start_date=date(2026, 1, 1),
    )

    svc.apply_promo(sub_id=sub.id, promo_code="ONCE10", today=date(2026, 1, 2))

    with pytest.raises(PromoNotValidError):
        svc.apply_promo(sub_id=sub.id, promo_code="ONCE10", today=date(2026, 1, 2))
