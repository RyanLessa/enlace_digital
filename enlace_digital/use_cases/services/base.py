from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ServiceResult:
    status_code: int
    content: Any
