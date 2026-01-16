from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from .errors import BillingError, InvalidStateTransitionError
from .mixins import AuditMixin, TimestampMixin
from .money import Money


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    PAID = "paid"


class InvalidInvoiceLineItemError(BillingError):
    """некорректная строка инвойса"""

    def __init__(self, msg: str) -> None:
        super().__init__(msg)


@dataclass(frozen=True, slots=True)
class LineItem:
    description: str
    amount: Money


class Invoice(AuditMixin, TimestampMixin):
    __slots__ = (
        "_id",
        "_created_at",
        "_customer_id",
        "_period_start",
        "_period_end",
        "_currency",
        "_status",
        "_items",
    )

    def __init__(
        self,
        *,
        customer_id: str,
        period_start: date,
        period_end: date,
        currency: str,
        status: InvoiceStatus = InvoiceStatus.DRAFT,
        items: list[LineItem] | None = None,
    ) -> None:
        super().__init__()

        if not customer_id:
            raise BillingError("customer_id must be non-empty")
        if period_end <= period_start:
            raise BillingError("period_end must be after period_start")
        currency_norm = (currency or "").strip().upper()
        if len(currency_norm) != 3 or not currency_norm.isalpha():
            raise BillingError("currency must be a 3-letter code")

        self._customer_id = customer_id
        self._period_start = period_start
        self._period_end = period_end
        self._currency = currency_norm
        self._status = status
        self._items: list[LineItem] = []

        if items:
            for li in items:
                self.add_line_item(li)

    @property
    def invoice_id(self) -> str:
        return self._customer_id

    @property
    def customer_id(self) -> str:
        return self._customer_id

    @property
    def period_start(self) -> date:
        return self._period_start

    @property
    def period_end(self) -> date:
        return self._period_end

    @property
    def currency(self) -> str:
        return self._currency

    @property
    def status(self) -> InvoiceStatus:
        return self._status

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def add_line_item(self, item: LineItem) -> None:
        if self._status != InvoiceStatus.DRAFT:
            raise InvalidStateTransitionError("Invoice", self._status.value, "add_line_item")

        if item.amount.currency != self._currency:
            raise InvalidInvoiceLineItemError(
                f"LineItem currency {item.amount.currency!r} "
                f"does not match invoice currency {self._currency!r}"
            )

        self._items.append(item)

    @property
    def total(self) -> Money:
        total = Money.of("0", self._currency)
        for li in self._items:
            total = total + li.amount
        return total

    def issue(self) -> None:
        if self._status != InvoiceStatus.DRAFT:
            raise InvalidStateTransitionError("Invoice", self._status.value, "issued")
        self._status = InvoiceStatus.ISSUED

    def pay(self) -> None:
        if self._status != InvoiceStatus.ISSUED:
            raise InvalidStateTransitionError("Invoice", self._status.value, "paid")
        self._status = InvoiceStatus.PAID
