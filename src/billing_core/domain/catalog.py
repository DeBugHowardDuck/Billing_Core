from __future__ import annotations

from dataclasses import dataclass, field

from .plans import Plan, PlanNotFoundError


@dataclass(slots=True)
class PlanCatalog:
    """Каталог планов."""

    _plans: dict[str, Plan] = field(default_factory=dict)

    def add(self, plan: Plan) -> None:
        self._plans[plan.code] = plan

    def get(self, code: str) -> Plan:
        plan = self._plans.get(code)
        if plan is None:
            raise PlanNotFoundError(code)
        return plan

    def __getitem__(self, code: str) -> Plan:
        return self.get(code)

    def __iter__(self):
        return iter(self._plans.values())

    def __len__(self) -> int:
        return len(self._plans)

    @classmethod
    def load_defaults(cls) -> PlanCatalog:
        catalog = cls()

        catalog.add(Plan.from_config("free;FREE;Free;EUR"))
        catalog.add(Plan.from_config("flat;PRO;Pro;EUR;20"))
        catalog.add(Plan.from_config("per_seat;TEAM;Team;EUR;10;5"))

        return catalog
