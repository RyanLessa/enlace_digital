import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from enlace_digital.interface.models import Group
from enlace_digital.interface.repositories import (
    NeighborhoodRepository,
    SchoolRepository,
)
from enlace_digital.settings.get_db import SessionLocal

REQUIRED_COLUMNS = {
    "nome",
    "bairro",
    "municipio",
    "endereco",
    "latitude",
    "longitude",
    "grupos",
}


@dataclass(frozen=True)
class ImportSummary:
    imported_rows: int
    errors: tuple[str, ...]


@dataclass(frozen=True)
class SchoolRow:
    name: str
    neighborhood: str
    municipality: str
    address: str | None
    latitude: float | None
    longitude: float | None


def import_schools(csv_path: Path, session: Session) -> ImportSummary:
    """Import valid CSV rows, preserving successful rows when another fails."""
    imported_rows = 0
    errors: list[str] = []
    neighborhoods = NeighborhoodRepository(session)
    schools = SchoolRepository(session)

    with csv_path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        missing_columns = REQUIRED_COLUMNS.difference(reader.fieldnames or [])
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"CSV is missing required columns: {missing}")

        for line_number, raw_row in enumerate(reader, start=2):
            try:
                row = _parse_row(raw_row)
            except ValueError as error:
                errors.append(f"Line {line_number}: {error}")
                continue

            try:
                with session.begin_nested():
                    neighborhood = neighborhoods.get_or_create(
                        row.neighborhood,
                        row.municipality,
                    )
                    schools.upsert(
                        name=row.name,
                        neighborhood_id=neighborhood.id,
                        address=row.address,
                        latitude=row.latitude,
                        longitude=row.longitude,
                    )
                    session.flush()
            except (SQLAlchemyError, ValueError) as error:
                errors.append(f"Line {line_number}: {error}")
                continue

            imported_rows += 1

    session.commit()
    return ImportSummary(imported_rows, tuple(errors))


def _parse_row(row: dict[str, str | None]) -> SchoolRow:
    name = _required_value(row, "nome")
    neighborhood = _required_value(row, "bairro")
    municipality = _required_value(row, "municipio")
    _validate_groups(row.get("grupos") or "")

    return SchoolRow(
        name=name,
        neighborhood=neighborhood,
        municipality=municipality,
        address=(row.get("endereco") or "").strip() or None,
        latitude=_parse_coordinate(row.get("latitude"), "latitude", -90, 90),
        longitude=_parse_coordinate(
            row.get("longitude"), "longitude", -180, 180
        ),
    )


def _required_value(row: dict[str, str | None], column: str) -> str:
    value = (row.get(column) or "").strip()
    if not value:
        raise ValueError(f"'{column}' is required.")
    return value


def _validate_groups(value: str) -> None:
    invalid_groups: list[str] = []
    for group_name in (item.strip() for item in value.split("|")):
        if not group_name:
            continue
        try:
            Group(group_name)
        except ValueError:
            invalid_groups.append(group_name)

    if invalid_groups:
        invalid = ", ".join(invalid_groups)
        raise ValueError(f"Unknown group value(s): {invalid}.")


def _parse_coordinate(
    value: str | None,
    field_name: str,
    minimum: float,
    maximum: float,
) -> float | None:
    if value is None or not value.strip():
        return None
    try:
        coordinate = float(value)
    except ValueError as error:
        raise ValueError(f"'{field_name}' must be a number.") from error
    if not minimum <= coordinate <= maximum:
        raise ValueError(
            f"'{field_name}' must be between {minimum} and {maximum}."
        )
    return coordinate


def _print_summary(summary: ImportSummary, output: TextIO) -> None:
    print(
        f"Imported {summary.imported_rows} row(s); "
        f"{len(summary.errors)} error(s).",
        file=output,
    )
    for error in summary.errors:
        print(error, file=output)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import schools from a CSV file."
    )
    parser.add_argument("csv_path", type=Path)
    arguments = parser.parse_args()

    try:
        with SessionLocal() as session:
            summary = import_schools(arguments.csv_path, session)
    except (OSError, ValueError, csv.Error, SQLAlchemyError) as error:
        print(f"Import failed: {error}", file=sys.stderr)
        return 2

    _print_summary(summary, sys.stdout)
    return 1 if summary.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
