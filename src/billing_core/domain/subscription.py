from __future__ import annotations

from datetime import date, timedelta
from enum import Enum

from .errors import BillingError, InvalidStateTransitionError
from .mixins import AuditMixin, TimestampMixin


class SubscriptionStatus(str, Enum):
    TRIALING = "trialing"
    ACTIVE = "active"
    CANCELED = "canceled"


class Subscription(AuditMixin, TimestampMixin):
    __slots__ = (
        "_id",
        "_created_at",
        "_customer_id",
        "_plan_code",
        "_status",
        "_start_date",
        "_current_period_start",
        "_current_period_end",
        "_seats",
        "_promo_code",
    )

    def __init__(
        self,
        *,
        customer_id: str,
        plan_code: str,
        start_date: date,
        current_period_start: date,
        current_period_end: date,
        status: SubscriptionStatus,
        seats: int = 1,
        promo_code: str | None = None,
    ) -> None:
        super().__init__()

        if not customer_id:
            raise BillingError("customer_id must be non-empty")
        if not plan_code:
            raise BillingError("plan_code must be non-empty")
        if seats < 1:
            raise BillingError("seats must be >= 1")
        if current_period_end <= current_period_start:
            raise BillingError("current_period_end must be after current_period_start")

        self._customer_id = customer_id
        self._plan_code = plan_code
        self._status = status

        self._start_date = start_date
        self._current_period_start = current_period_start
        self._current_period_end = current_period_end

        self._seats = seats
        self._promo_code = promo_code

    @classmethod
    def create(
        cls,
        *,
        customer_id: str,
        plan_code: str,
        start_date: date,
        period_days: int = 30,
        trial_days: int = 0,
        seats: int = 1,
    ) -> Subscription:
        if period_days < 1:
            raise BillingError("period_days must be >= 1")
        if trial_days < 0:
            raise BillingError("trial_days must be >= 0")

        status = SubscriptionStatus.TRIALING if trial_days > 0 else SubscriptionStatus.ACTIVE
        current_start = start_date
        current_end = start_date + timedelta(days=trial_days or period_days)

        return cls(
            customer_id=customer_id,
            plan_code=plan_code,
            start_date=start_date,
            current_period_start=current_start,
            current_period_end=current_end,
            status=status,
            seats=seats,
        )

    @property
    def customer_id(self) -> str:
        return self._customer_id

    @property
    def plan_code(self) -> str:
        return self._plan_code

    @property
    def status(self) -> SubscriptionStatus:
        return self._status

    @property
    def start_date(self) -> date:
        return self._start_date

    @property
    def current_period_start(self) -> date:
        return self._current_period_start

    @property
    def current_period_end(self) -> date:
        return self._current_period_end

    @property
    def seats(self) -> int:
        return self._seats

    @property
    def promo_code(self) -> str | None:
        return self._promo_code

    @property
    def is_active(self) -> bool:
        return self._status in {SubscriptionStatus.TRIALING, SubscriptionStatus.ACTIVE}

    @property
    def full_period_days(self) -> int:
        return (self._current_period_end - self._current_period_start).days

    @property
    def days_left_in_period(self) -> int:
        today = date.today()
        left = (self._current_period_end - today).days
        return max(0, left)

    def cancel(self) -> None:
        if self._status == SubscriptionStatus.CANCELED:
            raise InvalidStateTransitionError("Subscription", self._status.value, "canceled")
        self._status = SubscriptionStatus.CANCELED

    def activate(self) -> None:
        if self._status != SubscriptionStatus.TRIALING:
            raise InvalidStateTransitionError("Subscription", self._status.value, "active")
        self._status = SubscriptionStatus.ACTIVE

    def change_plan(self, new_plan_code: str) -> str:
        if self._status == SubscriptionStatus.CANCELED:
            raise InvalidStateTransitionError("Subscription", self._status.value, "change_plan")
        if not new_plan_code:
            raise BillingError("new_plan_code must be non-empty")

        old = self._plan_code
        self._plan_code = new_plan_code
        return old

    def change_seats(self, new_seats: int) -> int:
        if self._status == SubscriptionStatus.CANCELED:
            raise InvalidStateTransitionError("Subscription", self._status.value, "change_seats")
        if new_seats < 1:
            raise BillingError("new_seats must be >= 1")

        old = self._seats
        self._seats = new_seats
        return old

    def apply_promo(self, promo_code: str | None) -> None:
        if self._status == SubscriptionStatus.CANCELED:
            raise InvalidStateTransitionError("Subscription", self._status.value, "apply_promo")
        self._promo_code = promo_code
