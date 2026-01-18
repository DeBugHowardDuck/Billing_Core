from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from billing_core.application.repositories import (
    InvoiceRepository,
    PlanRepository,
    PromoRepository,
    SubscriptionRepository,
)
from billing_core.domain.errors import (
    InvoiceNotFoundError,
    PromoCodeNotFoundError,
    SubscriptionNotFoundError,
)
from billing_core.domain.invoice import Invoice
from billing_core.domain.plans import Plan, PlanNotFoundError
from billing_core.domain.promo import PromoCode
from billing_core.domain.subscription import Subscription


@dataclass(slots=True)
class InMemoryPlanRepo(PlanRepository):
    _plans: dict[str, Plan] = field(default_factory=dict)

    def add(self, plan: Plan) -> None:
        self._plans[plan.code] = plan

    def get(self, code: str) -> Plan:
        plan = self._plans.get(code)
        if plan is None:
            raise PlanNotFoundError(code)
        return plan

    def list(self) -> Iterable[Plan]:
        return self._plans.values()


@dataclass(slots=True)
class InMemorySubscriptionRepo(SubscriptionRepository):
    _subs: dict[str, Subscription] = field(default_factory=dict)

    def save(self, sub: Subscription) -> None:
        self._subs[sub.id] = sub

    def get(self, sub_id: str) -> Subscription:
        sub = self._subs.get(sub_id)
        if sub is None:
            raise SubscriptionNotFoundError(sub_id)
        return sub


@dataclass(slots=True)
class InMemoryInvoiceRepo(InvoiceRepository):
    _invoices: dict[str, Invoice] = field(default_factory=dict)

    def save(self, invoice: Invoice) -> None:
        self._invoices[invoice.invoice_id] = invoice

    def get(self, invoice_id: str) -> Invoice:
        inv = self._invoices.get(invoice_id)
        if inv is None:
            raise InvoiceNotFoundError(invoice_id)
        return inv


@dataclass(slots=True)
class InMemoryPromoRepo(PromoRepository):
    _promos: dict[str, PromoCode] = field(default_factory=dict)
    _used: set[tuple[str, str]] = field(default_factory=set)  # (code, customer_id)

    def add(self, promo: PromoCode) -> None:
        self._promos[promo.code] = promo

    def get(self, code: str) -> PromoCode:
        promo = self._promos.get(code)
        if promo is None:
            raise PromoCodeNotFoundError(code)
        return promo

    def is_used_by_customer(self, *, code: str, customer_id: str) -> bool:
        return (code, customer_id) in self._used

    def mark_used(self, *, code: str, customer_id: str) -> None:
        self._used.add((code, customer_id))
