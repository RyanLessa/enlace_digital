from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceResult:
    status_code: int
    content: dict[str, str]


def not_implemented(operation: str) -> ServiceResult:
    return ServiceResult(
        status_code=501,
        content={"detail": f"{operation} is not implemented yet."},
    )
