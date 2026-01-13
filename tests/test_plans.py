from decimal import Decimal

import pytest

from billing_core.domain.catalog import PlanCatalog
from billing_core.domain.errors import BillingError
from billing_core.domain.plans import (
    FlatMonthlyPlan,
    FreePlan,
    PerSeatMonthlyPlan,
    Plan,
    PlanNotFoundError,
)


def test_from_config_dict_free() -> None:
    p = Plan.from_config({"type": "free", "code": "FREE", "name": "Free", "currency": "EUR"})
    assert isinstance(p, FreePlan)
    assert p.monthly_price.amount == Decimal("0.00")


def test_from_config_dsl_flat() -> None:
    p = Plan.from_config("flat;PRO;Pro;EUR;20")
    assert isinstance(p, FlatMonthlyPlan)
    assert str(p.monthly_price) == "20.00 EUR"


def test_from_config_dsl_per_seat() -> None:
    p = Plan.from_config("per_seat;TEAM;Team;EUR;10;5")
    assert isinstance(p, PerSeatMonthlyPlan)
    assert p.requires_seats is True
    assert str(p.monthly_price_for(seats=1)) == "15.00 EUR"  # 10 + 5*1
    assert str(p.monthly_price_for(seats=3)) == "25.00 EUR"  # 10 + 5*3


def test_per_seat_rejects_invalid_seats() -> None:
    p = Plan.from_config("per_seat;TEAM;Team;EUR;10;5")
    with pytest.raises(BillingError):
        _ = p.monthly_price_for(seats=0)


def test_catalog_getitem_and_not_found() -> None:
    cat = PlanCatalog.load_defaults()
    assert cat["FREE"].code == "FREE"
    assert len(cat) == 3

    with pytest.raises(PlanNotFoundError):
        _ = cat["NOPE"]
