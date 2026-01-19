from datetime import date, timedelta

import pytest

from billing_core.domain.errors import PromoNotValidError
from billing_core.domain.money import Money
from billing_core.domain.promo import PromoCode


def test_percent_promo_applies_discount() -> None:
    promo = PromoCode(code="P20", kind="percent", percent=20, valid_until=None, is_single_use=False)
    promo.validate_for(today=date.today(), customer_id="cust_1", already_used=False)

    subtotal = Money.of("50", "EUR")
    total = promo.apply(subtotal=subtotal)

    assert str(total) == "40.00 EUR"


def test_percent_promo_cannot_go_below_zero_but_percent_never_negative() -> None:
    promo = PromoCode(code="P100", kind="percent", percent=100)
    promo.validate_for(today=date.today(), customer_id="cust_1", already_used=False)

    subtotal = Money.of("50", "EUR")
    total = promo.apply(subtotal=subtotal)

    assert str(total) == "0.00 EUR"


def test_fixed_promo_applies_and_caps_at_zero() -> None:
    promo = PromoCode(code="F5", kind="fixed", fixed_discount=Money.of("5", "EUR"))
    promo.validate_for(today=date.today(), customer_id="cust_1", already_used=False)

    assert str(promo.apply(subtotal=Money.of("20", "EUR"))) == "15.00 EUR"
    assert str(promo.apply(subtotal=Money.of("3", "EUR"))) == "0.00 EUR"


def test_fixed_promo_currency_mismatch_rejected() -> None:
    promo = PromoCode(code="F5", kind="fixed", fixed_discount=Money.of("5", "USD"))
    promo.validate_for(today=date.today(), customer_id="cust_1", already_used=False)

    with pytest.raises(PromoNotValidError):
        promo.apply(subtotal=Money.of("20", "EUR"))


def test_promo_expired_rejected() -> None:
    promo = PromoCode(code="OLD", kind="percent", percent=10, valid_until=date.today() - timedelta(days=1))
    with pytest.raises(PromoNotValidError):
        promo.validate_for(today=date.today(), customer_id="cust_1", already_used=False)


def test_single_use_rejected_if_already_used() -> None:
    promo = PromoCode(code="ONCE", kind="percent", percent=10, is_single_use=True)
    with pytest.raises(PromoNotValidError):
        promo.validate_for(today=date.today(), customer_id="cust_1", already_used=True)


def test_invalid_percent_range_rejected() -> None:
    promo = PromoCode(code="BAD", kind="percent", percent=120)
    with pytest.raises(PromoNotValidError):
        promo.validate_for(today=date.today(), customer_id="cust_1", already_used=False)
