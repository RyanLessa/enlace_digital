import enum

from sqlalchemy import Enum


class Group(str, enum.Enum):
    VISUAL = "visual"
    MOTORA = "motora"
    INTELECTUAL = "intelectual"
    AUDITIVA = "auditiva"
    PSICOSSOCIAL = "psicossocial"


NOTA_MIN = 1
NOTA_MAX = 5

GroupCol = Enum(
    Group,
    native_enum=False,
    length=20,
    values_callable=lambda group: [member.value for member in group],
)
