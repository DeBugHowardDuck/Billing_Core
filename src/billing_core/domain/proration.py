from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .errors import BillingError, CurrencyMismatchError
from .invoice import LineItem
from .money import Money


@dataclass(frozen=True, slots=True)
class ChangeDateInPeriodRule:
    def __call__(self, *, period_start: date, period_end: date, change_date: date) -> None:
        if period_end < period_start:
            raise BillingError("period_end must be before period_start")
        if change_date < period_start or change_date > period_end:
            raise BillingError("change_date must be within period_start and period_end")


_RULE = ChangeDateInPeriodRule()


def proration_line_items(
    *,
    old_monthly: Money,
    new_monthly: Money,
    period_start: date,
    period_end: date,
    change_date: date,
) -> list[LineItem]:
    _RULE(period_start=period_start, period_end=period_end, change_date=change_date)

    if old_monthly.currency != new_monthly.currency:
        raise CurrencyMismatchError(old_monthly.currency, new_monthly.currency)

    full_days = (period_end - period_start).days
    remaining_days = (period_end - change_date).days

    if remaining_days <= 0:
        return []

    fraction = Decimal(remaining_days) / Decimal(full_days)

    credit_amount = _pro_rate(old_monthly, fraction)
    charge_amount = _pro_rate(new_monthly, fraction)

    credit = Money(Decimal("0") - credit_amount.amount, credit_amount.currency)

    items: list[LineItem] = []
    if credit:
        items.append(LineItem("Proration credit (unused old plan)", credit))
    if charge_amount:
        items.append(LineItem("Proration charge (remaining new plan)", charge_amount))

    return items


def _pro_rate(monthly: Money, fraction: Decimal) -> Money:
    amount = monthly.amount * fraction
    amount = Money.round(amount)
    return Money(amount, monthly.currency)
