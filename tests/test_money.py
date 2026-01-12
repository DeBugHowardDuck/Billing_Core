from decimal import Decimal

import pytest

from billing_core.domain.errors import (
    CurrencyMismatchError,
    InvalidAmountError,
    InvalidCurrencyError,
)
from billing_core.domain.money import Money


def test_money_normalizes_currency_and_rounds_amount() -> None:
    m = Money.of("10.005", "eur")
    assert m.currency == "EUR"
    assert m.amount == Decimal("10.01")


def test_money_str_and_repr() -> None:
    m = Money.of("2.50", "EUR")
    assert str(m) == "2.50 EUR"
    assert "Money(" in repr(m)
    assert "EUR" in repr(m)


def test_money_bool() -> None:
    assert bool(Money.of("0", "EUR")) is False
    assert bool(Money.of("0.00", "EUR")) is False
    assert bool(Money.of("0.01", "EUR")) is True


def test_add_same_currency() -> None:
    a = Money.of("10.00", "EUR")
    b = Money.of("2.50", "EUR")
    assert (a + b).amount == Decimal("12.50")
    assert (a + b).currency == "EUR"


def test_sub_same_currency() -> None:
    a = Money.of("10.00", "EUR")
    b = Money.of("2.50", "EUR")
    assert (a - b).amount == Decimal("7.50")


def test_add_different_currency_raises() -> None:
    a = Money.of("10.00", "EUR")
    b = Money.of("1.00", "USD")
    with pytest.raises(CurrencyMismatchError):
        _ = a + b


def test_invalid_currency_raises() -> None:
    with pytest.raises(InvalidCurrencyError):
        _ = Money.of("10.00", "EU")

    with pytest.raises(InvalidCurrencyError):
        _ = Money.of("10.00", "12$")


def test_invalid_amount_rejects_float_and_garbage() -> None:
    with pytest.raises(InvalidAmountError):
        _ = Money.of(1.23, "EUR")

    with pytest.raises(InvalidAmountError):
        _ = Money.of("abc", "EUR")
