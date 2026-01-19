from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from billing_core.domain.errors import PromoCodeNotFoundError
from billing_core.domain.invoice import Invoice, LineItem
from billing_core.domain.proration import proration_line_items
from billing_core.domain.subscription import Subscription

from .repositories import InvoiceRepository, PlanRepository, PromoRepository, SubscriptionRepository
from .tx import billing_transaction


@dataclass(slots=True)
class BillingService:
    """application service - окрестрирует доменные сущности."""

    plans: PlanRepository
    subs: SubscriptionRepository
    invoices: InvoiceRepository
    promos: PromoRepository

    def create_subscription(
        self,
        *,
        customer_id: str,
        plan_code: str,
        start_date: date,
        seats: int = 1,
        trial_days: int = 0,
        period_days: int = 30,
    ) -> tuple[Subscription, Invoice | None]:
        with billing_transaction("create_subscription"):
            plan = self.plans.get(plan_code)

            sub = Subscription.create(
                customer_id=customer_id,
                plan_code=plan_code,
                start_date=start_date,
                period_days=period_days,
                trial_days=trial_days,
                seats=seats,
            )
            self.subs.save(sub)

            if trial_days > 0:
                return sub, None

            monthly = plan.monthly_price_for(seats=sub.seats)

            if not monthly:
                return sub, None

            inv = Invoice(
                customer_id=sub.customer_id,
                period_start=sub.current_period_start,
                period_end=sub.current_period_end,
                currency=monthly.currency,
            )
            inv.add_line_item(LineItem("Subscription charge", monthly))

            self.invoices.save(inv)
            return sub, inv

    def cancel_subscription(self, *, sub_id: str) -> Subscription:
        with billing_transaction("cancel_subscription"):
            sub = self.subs.get(sub_id)
            sub.cancel()
            self.subs.save(sub)
            return sub

    def upgrade_subscription(
        self,
        *,
        sub_id: str,
        new_plan_code: str,
        change_date: date,
    ) -> Invoice | None:
        with billing_transaction("upgrade_subscription"):
            sub = self.subs.get(sub_id)

            old_plan = self.plans.get(sub.plan_code)
            new_plan = self.plans.get(new_plan_code)

            old_monthly = old_plan.monthly_price_for(seats=sub.seats)
            new_monthly = new_plan.monthly_price_for(seats=sub.seats)

            items = proration_line_items(
                old_monthly=old_monthly,
                new_monthly=new_monthly,
                period_start=sub.current_period_start,
                period_end=sub.current_period_end,
                change_date=change_date,
            )

            sub.change_plan(new_plan_code)
            self.subs.save(sub)

            if not items:
                return None

            inv = Invoice(
                customer_id=sub.customer_id,
                period_start=sub.current_period_start,
                period_end=sub.current_period_end,
                currency=old_monthly.currency,
            )
            for li in items:
                inv.add_line_item(li)

            self.invoices.save(inv)
            return inv

    def change_seats(
        self,
        *,
        sub_id: str,
        new_seats: int,
        change_date: date,
    ) -> Invoice | None:
        with billing_transaction("change_seats"):
            sub = self.subs.get(sub_id)
            plan = self.plans.get(sub.plan_code)

            old_monthly = plan.monthly_price_for(seats=sub.seats)
            sub.change_seats(new_seats)
            self.subs.save(sub)

            new_monthly = plan.monthly_price_for(seats=sub.seats)

            items = proration_line_items(
                old_monthly=old_monthly,
                new_monthly=new_monthly,
                period_start=sub.current_period_start,
                period_end=sub.current_period_end,
                change_date=change_date,
            )

            if not items:
                return None

            inv = Invoice(
                customer_id=sub.customer_id,
                period_start=sub.current_period_start,
                period_end=sub.current_period_end,
                currency=old_monthly.currency,
            )
            for li in items:
                inv.add_line_item(li)

            self.invoices.save(inv)
            return inv

    def issue_invoice(self, *, invoice_id: str) -> Invoice:
        with billing_transaction("issue_invoice"):
            inv = self.invoices.get(invoice_id)
            inv.issue()
            self.invoices.save(inv)
            return inv

    def pay_invoice(self, *, invoice_id: str) -> Invoice:
        with billing_transaction("pay_invoice"):
            inv = self.invoices.get(invoice_id)
            inv.pay()
            self.invoices.save(inv)
            return inv

    def apply_promo(
        self,
        *,
        sub_id: str,
        promo_code: str,
        today: date,
    ) -> Subscription:
        with billing_transaction("apply_promo"):
            sub = self.subs.get(sub_id)

            try:
                promo = self.promos.get(promo_code)
            except PromoCodeNotFoundError:
                raise

            already_used = self.promos.is_used_by_customer(code=promo_code, customer_id=sub.customer_id)
            promo.validate_for(today=today, customer_id=sub.customer_id, already_used=already_used)

            sub.apply_promo(promo_code)
            self.subs.save(sub)

            if promo.is_single_use:
                self.promos.mark_used(code=promo_code, customer_id=sub.customer_id)

            return sub
