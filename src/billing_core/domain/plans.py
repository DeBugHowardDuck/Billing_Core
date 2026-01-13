from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, ClassVar

from .errors import BillingError, InvalidAmountError
from .money import Money


class InvalidPlanConfigError(BillingError):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)


class PlanNotFoundError(BillingError):
    def __init__(self, code: str) -> None:
        super().__init__(f"Plan not found: {code!r}")
        self.code = code


@dataclass(frozen=True, slots=True)
class Plan(ABC):
    code: str
    name: str
    currency: str

    _REGISTRY: ClassVar[dict[str, type[Plan]]] = {}

    @property
    def requires_seats(self) -> bool:
        return False

    @abstractmethod
    def monthly_price_for(self, *, seats: int = 1) -> Money:
        raise NotImplementedError

    @property
    def monthly_price(self) -> Money:
        return self.monthly_price_for(seats=1)

    @classmethod
    def register(cls, plan_type: str) -> Any:
        def _wrap(subcls: type[Plan]) -> type[Plan]:
            cls._REGISTRY[plan_type] = subcls
            return subcls

        return _wrap

    @classmethod
    def from_config(cls, config: str | Mapping[str, Any]) -> Plan:
        data: Mapping[str, Any]

        if isinstance(config, str):
            raw = config.strip()
            if raw.startswith("{"):
                data = json.loads(raw)
            else:
                data = cls._parse_dsl(raw)
        else:
            data = config

        plan_type = str(data.get("type", "")).strip().lower()
        if not plan_type:
            raise InvalidPlanConfigError("Missing 'type' in plan config")

        plan_cls = cls._REGISTRY.get(plan_type)
        if plan_cls is None:
            raise InvalidPlanConfigError(f"Unknown plan type: {plan_type!r}")

        return plan_cls._from_mapping(data)

    @staticmethod
    def _parse_dsl(raw: str) -> Mapping[str, Any]:
        parts = [p.strip() for p in raw.split(";")]
        if not parts or not parts[0]:
            raise InvalidPlanConfigError("Empty plan config string")

        t = parts[0].lower()

        if t == "free":
            if len(parts) != 4:
                raise InvalidPlanConfigError("free DSL: free;CODE;NAME;CUR")
            return {"type": "free", "code": parts[1], "name": parts[2], "currency": parts[3]}

        if t == "flat":
            if len(parts) != 5:
                raise InvalidPlanConfigError("flat DSL: flat;CODE;NAME;CUR;MONTHLY_PRICE")
            return {
                "type": "flat",
                "code": parts[1],
                "name": parts[2],
                "currency": parts[3],
                "monthly_price": parts[4],
            }

        if t == "per_seat":
            if len(parts) != 6:
                raise InvalidPlanConfigError("per_seat DSL: per_seat;CODE;NAME;CUR;BASE;PER_SEAT")
            return {
                "type": "per_seat",
                "code": parts[1],
                "name": parts[2],
                "currency": parts[3],
                "base": parts[4],
                "per_seat": parts[5],
            }

        raise InvalidPlanConfigError(f"Unknown DSL plan type: {t!r}")

    @classmethod
    @abstractmethod
    def _from_mapping(cls, data: Mapping[str, Any]) -> Plan:
        raise NotImplementedError


@Plan.register("free")
@dataclass(frozen=True, slots=True)
class FreePlan(Plan):
    def monthly_price_for(self, *, seats: int = 1) -> Money:
        return Money.of("0", self.currency)

    @classmethod
    def _from_mapping(cls, data: Mapping[str, Any]) -> FreePlan:
        return cls(
            code=str(data["code"]),
            name=str(data["name"]),
            currency=str(data["currency"]),
        )


@Plan.register("flat")
@dataclass(frozen=True, slots=True)
class FlatMonthlyPlan(Plan):
    monthly: Money

    def monthly_price_for(self, *, seats: int = 1) -> Money:
        return self.monthly

    @property
    def monthly_price(self) -> Money:
        return self.monthly

    @classmethod
    def _from_mapping(cls, data: Mapping[str, Any]) -> FlatMonthlyPlan:
        cur = str(data["currency"])
        price = data.get("monthly_price")
        if price is None:
            raise InvalidPlanConfigError("flat plan requires 'monthly_price'")
        try:
            monthly = Money.of(str(price), cur)
        except InvalidAmountError as e:
            raise InvalidPlanConfigError("Invalid flat monthly_price") from e

        return cls(
            code=str(data["code"]),
            name=str(data["name"]),
            currency=cur,
            monthly=monthly,
        )


@Plan.register("per_seat")
@dataclass(frozen=True, slots=True)
class PerSeatMonthlyPlan(Plan):
    base: Money
    per_seat: Money

    @property
    def requires_seats(self) -> bool:
        return True

    def monthly_price_for(self, *, seats: int = 1) -> Money:
        if seats < 1:
            raise BillingError("seats must be >= 1")
        total = self.base
        for _ in range(seats):
            total = total + self.per_seat
        return total

    @classmethod
    def _from_mapping(cls, data: Mapping[str, Any]) -> PerSeatMonthlyPlan:
        cur = str(data["currency"])
        base = data.get("base")
        per_seat = data.get("per_seat")
        if base is None or per_seat is None:
            raise InvalidPlanConfigError("per_seat plan requires 'base' and 'per_seat'")

        try:
            base_m = Money.of(str(base), cur)
            per_seat_m = Money.of(str(per_seat), cur)
        except InvalidAmountError as e:
            raise InvalidPlanConfigError("Invalid per_seat/base amount") from e

        return cls(
            code=str(data["code"]),
            name=str(data["name"]),
            currency=cur,
            base=base_m,
            per_seat=per_seat_m,
        )
