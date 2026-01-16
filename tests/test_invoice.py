from datetime import date, timedelta

import pytest

from billing_core.domain.errors import InvalidStateTransitionError
from billing_core.domain.invoice import (
    InvalidInvoiceLineItemError,
    Invoice,
    InvoiceStatus,
    LineItem,
)
from billing_core.domain.money import Money


def test_invoice_total_len_iter() -> None:
    inv = Invoice(
        customer_id="cust_1",
        period_start=date.today(),
        period_end=date.today() + timedelta(days=30),
        currency="eur",
    )

    assert inv.currency == "EUR"
    assert inv.status == InvoiceStatus.DRAFT
    assert len(inv) == 0
    assert str(inv.total) == "0.00 EUR"

    inv.add_line_item(LineItem("Subscription charge", Money.of("20", "EUR")))
    inv.add_line_item(LineItem("Upgrade proration", Money.of("5.50", "EUR")))

    assert len(inv) == 2
    assert [li.description for li in inv] == ["Subscription charge", "Upgrade proration"]
    assert str(inv.total) == "25.50 EUR"


def test_invoice_rejects_wrong_lineitem_currency() -> None:
    inv = Invoice(
        customer_id="cust_1",
        period_start=date.today(),
        period_end=date.today() + timedelta(days=30),
        currency="EUR",
    )

    with pytest.raises(InvalidInvoiceLineItemError):
        inv.add_line_item(LineItem("Bad currency", Money.of("1", "USD")))


def test_invoice_issue_and_pay_transitions() -> None:
    inv = Invoice(
        customer_id="cust_1",
        period_start=date.today(),
        period_end=date.today() + timedelta(days=30),
        currency="EUR",
    )

    with pytest.raises(InvalidStateTransitionError):
        inv.pay()

    inv.issue()
    assert inv.status == InvoiceStatus.ISSUED

    with pytest.raises(InvalidStateTransitionError):
        inv.add_line_item(LineItem("Late add", Money.of("1", "EUR")))

    inv.pay()
    assert inv.status == InvoiceStatus.PAID

    with pytest.raises(InvalidStateTransitionError):
        inv.issue()
