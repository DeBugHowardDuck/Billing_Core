class BillingError(Exception):
    """Base class for all billing errors."""


class CurrencyMismatchError(BillingError):
    """Raised when trying to operate on Money objects with different currencies."""

    def __init__(self, left: str, right: str) -> None:
        super().__init__(f"Currency mismatch: {left!r} vs {right!r}")
        self.left = left
        self.right = right


class InvalidCurrencyError(BillingError):
    """Raised when currency code is invalid (e.g., not a 3-letter code)."""

    def __init__(self, currency: str) -> None:
        super().__init__(f"Invalid currency: {currency!r}")
        self.currency = currency


class InvalidAmountError(BillingError):
    """Raised when amount can't be parsed/used as Decimal safely."""

    def __init__(self, amount: object) -> None:
        super().__init__(f"Invalid amount: {amount!r}")
        self.amount = amount


class InvalidStateTransitionError(BillingError):
    """Raised when an entity is moved to an invalid state."""

    def __init__(self, entity: str, from_state: str, to_state: str) -> None:
        super().__init__(f"Invalid state transition for {entity}: {from_state} -> {to_state}")
        self.entity = entity
        self.from_state = from_state
        self.to_state = to_state


class PromoNotValidError(BillingError):
    def __init__(self, code: str, reason: str) -> None:
        super().__init__(f"Promo {code!r} not valid: {reason}")
        self.code = code
        self.reason = reason
