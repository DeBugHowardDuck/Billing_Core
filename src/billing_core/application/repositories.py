from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from billing_core.domain.invoice import Invoice
from billing_core.domain.plans import Plan
from billing_core.domain.promo import PromoCode
from billing_core.domain.subscription import Subscription


class PlanRepository(ABC):
    @abstractmethod
    def add(self, plan: Plan) -> None: ...

    @abstractmethod
    def get(self, code: str) -> Plan: ...

    @abstractmethod
    def list(self) -> Iterable[Plan]: ...


class SubscriptionRepository(ABC):
    @abstractmethod
    def save(self, sub_id: str) -> Subscription: ...


class InvoiceRepository(ABC):
    @abstractmethod
    def get(self, invoice_id: str) -> Invoice: ...


class PromoRepository(ABC):
    @abstractmethod
    def add(self, promo: PromoCode) -> PromoCode: ...

    @abstractmethod
    def get(self, code: str) -> PromoCode: ...

    @abstractmethod
    def is_used_by_customer(self, *, code: str, customer_id: str) -> bool: ...

    @abstractmethod
    def mark_used(self, *, code: str, customer_id: str) -> bool: ...
