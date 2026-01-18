from typing import Annotated

from fastapi import APIRouter, Depends

from billing_core.api.deps import get_service
from billing_core.api.schemas import InvoiceOut, LineItemOut, MoneyOut
from billing_core.application.services import BillingService

router = APIRouter(prefix="/invoices", tags=["invoices"])
SvcDep = Annotated[BillingService, Depends(get_service)]

def _to_invoice_out(inv) -> InvoiceOut:
    items = [
        LineItemOut(
            description=li.description,
            amount=MoneyOut(amount=li.amount.amount, currency=li.amount.currency),
        )
        for li in inv
    ]
    total = inv.total
    return InvoiceOut(
        invoice_id=inv.invoice_id,
        created_at=inv.created_at,
        customer_id=inv.customer_id,
        period_start=inv.period_start,
        period_end=inv.period_end,
        currency=inv.currency,
        status=inv.status.value if hasattr(inv.status, "value") else str(inv.status),
        items=items,
        total=MoneyOut(amount=total.amount, currency=total.currency),
    )



@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: str, svc: SvcDep):
    inv = svc.invoices.get(invoice_id)
    return _to_invoice_out(inv)


@router.post("/{invoice_id}/issue", response_model=InvoiceOut)
def issue_invoice(invoice_id: str, svc: SvcDep):
    inv = svc.issue_invoice(invoice_id=invoice_id)
    return _to_invoice_out(inv)


@router.post("/{invoice_id}/pay", response_model=InvoiceOut)
def pay_invoice(invoice_id: str, svc: SvcDep):
    inv = svc.pay_invoice(invoice_id=invoice_id)
    return _to_invoice_out(inv)