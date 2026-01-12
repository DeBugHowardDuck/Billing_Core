from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import ClassVar

from .errors import CurrencyMismatchError, InvalidAmountError, InvalidCurrencyError

AmountLike = Decimal | int | str


@dataclass(frozen=True, slots=True)
class Money:
    """Money is a value object: amount (Decimal) + currency (str)."""

    _amount: Decimal
    _currency: str

    _DEFAULT_QUANT: ClassVar[Decimal] = Decimal("0.01")

    def __post_init__(self) -> None:
        currency = (self._currency or "").strip().upper()
        if len(currency) != 3 or not currency.isalpha():
            raise InvalidCurrencyError(self._currency)

        amount = self._to_decimal(self._amount)
        amount = self.round(amount, quant=self._DEFAULT_QUANT)

        object.__setattr__(self, "_amount", amount)
        object.__setattr__(self, "_currency", currency)

    @property
    def amount(self) -> Decimal:
        """Public read-only access to amount."""
        return self._amount

    @property
    def currency(self) -> str:
        """Public read-only access to currency."""
        return self._currency

    def __bool__(self) -> bool:
        """Money(0) is falsy, any non-zero amount is truthy."""
        return self._amount != 0

    def __repr__(self) -> str:
        return f"Money(amount=Decimal({str(self._amount)!r}), currency={self._currency!r})"

    def __str__(self):
        return f"{self._amount} {self._currency}"

    def __add__(self, other: Money) -> Money:
        self._assert_same_currency(other)
        return Money(self._amount + other._amount, self._currency)

    def __sub__(self, other: Money) -> Money:
        self._assert_same_currency(other)
        return Money(self._amount - other._amount, self._currency)

    def _assert_same_currency(self, other: Money) -> None:
        if self._currency != other._currency:
            raise CurrencyMismatchError(self._currency, other._currency)

    @classmethod
    def of(cls, amount: AmountLike, currency: str) -> Money:
        """Named constructor: helps readability in code and tests."""
        return cls(amount, currency)

    @staticmethod
    def round(value: Decimal, *, quant: Decimal = Decimal("0.01")) -> Decimal:
        """Decimal rounding helper (HALF_UP) with quantization."""
        return value.quantize(quant, rounding=ROUND_HALF_UP)

    @staticmethod
    def _to_decimal(value: object) -> Decimal:
        """Strict conversion to Decimal."""
        if isinstance(value, Decimal):
            dec = value
        elif isinstance(value, int):
            dec = Decimal(value)
        elif isinstance(value, str):
            try:
                dec = Decimal(value)
            except Exception as e:
                raise InvalidAmountError(value) from e
        elif isinstance(value, float):
            raise InvalidAmountError(value)
        else:
            raise InvalidAmountError(value)

        if not dec.is_finite():
            raise InvalidAmountError(value)

        return dec
