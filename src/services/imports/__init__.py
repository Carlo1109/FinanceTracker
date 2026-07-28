from __future__ import annotations

from src.services.imports.base import BankImporter, BankImporterInfo
from src.services.imports.fineco import FinecoImporter
from src.services.imports.paypal import PayPalImporter
from src.services.imports.postepay import PostePayImporter
from src.services.imports.revolut import RevolutImporter


_IMPORTERS: list[BankImporter] = [
    FinecoImporter(),
    RevolutImporter(),
    PostePayImporter(),
    PayPalImporter(),
]

_BY_LABEL = {importer.info.label: importer for importer in _IMPORTERS}


def list_importers() -> list[BankImporterInfo]:
    return [importer.info for importer in _IMPORTERS]


def get_importer_by_label(label: str) -> BankImporter:
    try:
        return _BY_LABEL[label]
    except KeyError as error:
        raise KeyError(f"Importer sconosciuto: {label}") from error
