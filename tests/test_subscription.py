from datetime import date, timedelta

import pytest

from billing_core.domain.errors import BillingError, InvalidStateTransitionError
from billing_core.domain.subscription import Subscription, SubscriptionStatus


def test_create_active_subscription_defaults() -> None:
    today = date.today()
    s = Subscription.create(customer_id="cust_1", plan_code="PRO", start_date=today, period_days=30)

    assert s.customer_id == "cust_1"
    assert s.plan_code == "PRO"
    assert s.status == SubscriptionStatus.ACTIVE
    assert s.is_active is True
    assert s.seats == 1

    assert s.current_period_start == today
    assert s.current_period_end == today + timedelta(days=30)
    assert s.full_period_days == 30


def test_create_trial_subscription() -> None:
    today = date.today()
    s = Subscription.create(customer_id="cust_1", plan_code="PRO", start_date=today, trial_days=7)

    assert s.status == SubscriptionStatus.TRIALING
    assert s.is_active is True
    assert s.current_period_end == today + timedelta(days=7)


def test_days_left_is_non_negative() -> None:
    today = date.today()
    s = Subscription.create(customer_id="cust_1", plan_code="PRO", start_date=today, period_days=1)

    assert s.days_left_in_period in (0, 1)


def test_cancel_and_invalid_cancel() -> None:
    s = Subscription.create(customer_id="cust_1", plan_code="PRO", start_date=date.today())

    s.cancel()
    assert s.status == SubscriptionStatus.CANCELED
    assert s.is_active is False

    with pytest.raises(InvalidStateTransitionError):
        s.cancel()


def test_activate_only_from_trialing() -> None:
    s = Subscription.create(customer_id="cust_1", plan_code="PRO", start_date=date.today())

    with pytest.raises(InvalidStateTransitionError):
        s.activate()

    t = Subscription.create(
        customer_id="cust_2", plan_code="PRO", start_date=date.today(), trial_days=3
    )
    t.activate()
    assert t.status == SubscriptionStatus.ACTIVE


def test_change_plan_and_change_seats() -> None:
    s = Subscription.create(customer_id="cust_1", plan_code="PRO", start_date=date.today(), seats=2)

    old_plan = s.change_plan("TEAM")
    assert old_plan == "PRO"
    assert s.plan_code == "TEAM"

    old_seats = s.change_seats(5)
    assert old_seats == 2
    assert s.seats == 5


def test_change_seats_rejects_invalid() -> None:
    s = Subscription.create(customer_id="cust_1", plan_code="TEAM", start_date=date.today())

    with pytest.raises(BillingError):
        s.change_seats(0)


def test_actions_forbidden_when_canceled() -> None:
    s = Subscription.create(customer_id="cust_1", plan_code="PRO", start_date=date.today())
    s.cancel()

    with pytest.raises(InvalidStateTransitionError):
        s.change_plan("TEAM")

    with pytest.raises(InvalidStateTransitionError):
        s.change_seats(2)

    with pytest.raises(InvalidStateTransitionError):
        s.apply_promo("PROMO20")


def test_mixins_generate_id_and_created_at() -> None:
    s = Subscription.create(customer_id="cust_1", plan_code="PRO", start_date=date.today())
    assert isinstance(s.id, str) and len(s.id) > 10
    assert s.created_at is not None
