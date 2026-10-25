from fastapi import Header

from enlace_digital.use_cases.services import UserService


def get_user_id(authorization: str | None = Header(default=None)) -> int | None:
    if authorization is None:
        return None

    scheme, separator, payload = authorization.partition(" ")
    if (
        not separator
        or scheme.casefold() != "bearer"
        or not payload
        or any(character.isspace() for character in payload)
    ):
        return None

    decoded_payload = UserService.decode_payload(payload)

    return decoded_payload
