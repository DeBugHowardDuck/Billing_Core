from datetime import date, timedelta
from decimal import Decimal

import pytest

from billing_core.domain.errors import BillingError, CurrencyMismatchError
from billing_core.domain.money import Money
from billing_core.domain.proration import proration_line_items


def _d(d: str) -> Decimal:
    return Decimal(d)


def test_proration_upgrade_mid_period_creates_credit_and_charge() -> None:
    # Период: [start, end) = 30 дней
    start = date(2026, 1, 1)
    end = start + timedelta(days=30)

    # Смена на середине (ровно 15 дней осталось)
    change = start + timedelta(days=15)

    old = Money.of("20", "EUR")  # PRO
    new = Money.of("30", "EUR")  # TEAM

    items = proration_line_items(
        old_monthly=old,
        new_monthly=new,
        period_start=start,
        period_end=end,
        change_date=change,
    )

    # Должно быть 2 позиции: кредит по старому и начисление по новому
    assert len(items) == 2

    credit, charge = items
    assert credit.amount.currency == "EUR"
    assert charge.amount.currency == "EUR"

    # Осталось 15 из 30 => 0.5
    # кредит = -20 * 0.5 = -10.00
    # начисление = +30 * 0.5 = +15.00
    assert credit.amount.amount == _d("-10.00")
    assert charge.amount.amount == _d("15.00")

    # Нетто должно быть +5.00
    total = Money.of("0", "EUR")
    for li in items:
        total = total + li.amount
    assert total.amount == _d("5.00")


def test_proration_downgrade_mid_period_can_be_negative_total() -> None:
    start = date(2026, 1, 1)
    end = start + timedelta(days=30)
    change = start + timedelta(days=15)

    old = Money.of("30", "EUR")
    new = Money.of("20", "EUR")

    items = proration_line_items(
        old_monthly=old,
        new_monthly=new,
        period_start=start,
        period_end=end,
        change_date=change,
    )

    assert len(items) == 2
    credit, charge = items

    # кредит = -30*0.5 = -15.00
    # начисление = +20*0.5 = +10.00
    assert credit.amount.amount == _d("-15.00")
    assert charge.amount.amount == _d("10.00")

    total = Money.of("0", "EUR")
    for li in items:
        total = total + li.amount
    assert total.amount == _d("-5.00")  # кредит клиенту


def test_proration_on_period_end_returns_no_items() -> None:
    start = date(2026, 1, 1)
    end = start + timedelta(days=30)
    change = end  # осталось 0 дней

    old = Money.of("20", "EUR")
    new = Money.of("30", "EUR")

    items = proration_line_items(
        old_monthly=old,
        new_monthly=new,
        period_start=start,
        period_end=end,
        change_date=change,
    )

    assert items == []


def test_proration_rejects_change_outside_period() -> None:
    start = date(2026, 1, 1)
    end = start + timedelta(days=30)

    old = Money.of("20", "EUR")
    new = Money.of("30", "EUR")

    with pytest.raises(BillingError):
        proration_line_items(
            old_monthly=old,
            new_monthly=new,
            period_start=start,
            period_end=end,
            change_date=start - timedelta(days=1),
        )


def test_proration_rejects_currency_mismatch() -> None:
    start = date(2026, 1, 1)
    end = start + timedelta(days=30)
    change = start + timedelta(days=10)

    old = Money.of("20", "EUR")
    new = Money.of("30", "USD")

    with pytest.raises(CurrencyMismatchError):
        proration_line_items(
            old_monthly=old,
            new_monthly=new,
            period_start=start,
            period_end=end,
            change_date=change,
        )
