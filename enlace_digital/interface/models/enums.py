import enum

from sqlalchemy import Enum


class Grupo(str, enum.Enum):
    VISUAL = "visual"
    MOTORA = "motora"
    INTELECTUAL = "intelectual"
    AUDITIVA = "auditiva"
    PSICOSSOCIAL = "psicossocial"


NOTA_MIN = 1
NOTA_MAX = 5

GrupoCol = Enum(
    Grupo,
    native_enum=False,
    length=20,
    values_callable=lambda grupo: [membro.value for membro in grupo],
)
