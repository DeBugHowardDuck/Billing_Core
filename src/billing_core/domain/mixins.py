from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4


class AuditMixin:
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__()
        self._id = uuid4().hex

    @property
    def id(self) -> str:
        return self._id


class TimestampMixin:
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__()
        self._created_at = datetime.now(UTC)

    @property
    def created_at(self) -> datetime:
        return self._created_at
