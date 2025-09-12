# SPDX-FileCopyrightText: 2025 Dalibo
#
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from ..models import PostgreSQLInstance
from . import impl
from .impl import available as available
from .impl import get_settings as get_settings
from .models import build


async def pg_hba_config(instance: PostgreSQLInstance) -> list[str]:
    settings = get_settings(instance._settings)
    patroni = build.Patroni.get(instance.qualname, settings)
    r = await impl.api_request(patroni, "GET", "config")
    hba = r.json().get("postgresql", {}).get("pg_hba", [])
    assert isinstance(hba, list)
    return hba


async def configure_pg_hba(instance: PostgreSQLInstance, hba: list[str]) -> None:
    settings = get_settings(instance._settings)
    patroni = build.Patroni.get(instance.qualname, settings)
    await impl.api_request(
        patroni, "PATCH", "config", json={"postgresql": {"pg_hba": hba}}
    )
