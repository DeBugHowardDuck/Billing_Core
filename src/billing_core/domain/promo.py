from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .errors import BillingError, PromoNotValidError
from .money import Money


@dataclass(frozen=True, slots=True)
class PromoCode:
    code: str
    kind: str
    percent: int | None = None
    fixed_discount: Money | None = None
    valid_until: date | None = None
    is_single_use: bool = False

    def validate_for(self, *, today: date, customer_id: str, already_used: bool) -> None:
        if not self.code:
            raise BillingError("promo code must not be empty")
        if not customer_id:
            raise BillingError("customer id must not be empty")

        if self.valid_until is not None and today > self.valid_until:
            raise PromoNotValidError(self.code, "expired")

        if self.is_single_use and already_used:
            raise PromoNotValidError(self.code, "already used")

        if self.kind == "percent":
            if self.percent is None:
                raise PromoNotValidError(self.code, "missing percent")
            if not (0 <= self.percent <= 100):
                raise PromoNotValidError(self.code, "percent must be between 0 and 100")

        if self.kind == "fixed":
            if self.fixed_discount is None:
                raise PromoNotValidError(self.code, "missing fixed discount")

    def apply(self, *, subtotal: Money) -> Money:
        """Возвращает новую сумму после скидки"""

        if self.kind == "percent":
            assert self.percent is not None
            factor = Decimal(100 - self.percent) / Decimal(100)
            new_amount = Money.round(subtotal.amount * factor)
            result = Money(new_amount, subtotal.currency)
            return result

        if self.kind == "fixed":
            assert self.fixed_discount is not None
            if self.fixed_discount.currency != subtotal.currency:
                raise PromoNotValidError(self.code, "currency mismatch with subtotal")

            raw = subtotal - self.fixed_discount
            if raw.amount < 0:
                return Money.of("0", subtotal.currency)
            return raw

        raise PromoNotValidError(self.code, "unknown kind")
