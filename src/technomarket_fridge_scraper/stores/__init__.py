from __future__ import annotations

from . import technomarket, technopolis, zora

STORE_BACKENDS = {
    "technomarket": technomarket,
    "technopolis": technopolis,
    "zora": zora,
}
