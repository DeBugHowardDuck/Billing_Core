from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class MoneyOut(BaseModel):
    amount: Decimal
    currency: str


class PlanCreate(BaseModel):
    type: str = Field(..., description="free | flat | per_seat")
    code: str
    name: str
    currency: str
    monthly_price: str | None = None
    base: str | None = None
    per_seat: str | None = None


class PlanOut(BaseModel):
    code: str
    name: str
    currency: str
    monthly_price: MoneyOut
    requires_seats: bool


class SubscriptionCreate(BaseModel):
    customer_id: str
    plan_code: str
    start_date: date
    seats: int = 1
    trial_days: int = 0
    period_days: int = 30


class SubscriptionOut(BaseModel):
    id: str
    created_at: datetime
    customer_id: str
    plan_code: str
    status: str
    start_date: date
    current_period_start: date
    current_period_end: date
    seats: int
    promo_code: str | None
    is_active: bool
    days_left_in_period: int


class CreateSubscriptionResponse(BaseModel):
    subscription: SubscriptionOut
    invoice_id: str | None


class UpgradeRequest(BaseModel):
    new_plan_code: str
    change_date: date


class ChangeSeatsRequest(BaseModel):
    new_seats: int
    change_date: date


class ApplyPromoRequest(BaseModel):
    promo_code: str


class LineItemOut(BaseModel):
    description: str
    amount: MoneyOut


class InvoiceOut(BaseModel):
    invoice_id: str
    created_at: datetime
    customer_id: str
    period_start: date
    period_end: date
    currency: str
    status: str
    items: list[LineItemOut]
    total: MoneyOut


class PromoCreate(BaseModel):
    code: str
    kind: str
    percent: int | None = None
    fixed_amount: str | None = None
    currency: str | None = None
    valid_until: date | None = None
    is_single_use: bool = False
