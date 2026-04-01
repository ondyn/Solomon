"""
Solomon - CUZK (Czech Cadastral Office) API client.

Provides a service layer for interacting with the REST API of the
Czech cadastral register (Katastr nemovitostí).

API docs: https://api-kn.cuzk.gov.cz/swagger/index.html
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import requests

logger = logging.getLogger(__name__)

CUZK_API_BASE_URL = "https://api-kn.cuzk.gov.cz/api/v1"


# ---------------------------------------------------------------------------
#  Data classes for parsed CUZK responses
# ---------------------------------------------------------------------------
@dataclass
class CUZKShare:
    """Ownership share (podíl na společných částech domu)."""

    numerator: int
    denominator: int

    @classmethod
    def from_api(cls, data: dict | None) -> CUZKShare | None:
        if not data:
            return None
        return cls(
            numerator=int(data.get("citatel", 0)),
            denominator=int(data.get("jmenovatel", 0)),
        )

    def __str__(self) -> str:
        return f"{self.numerator}/{self.denominator}"


@dataclass
class CUZKTitleDeed:
    """List vlastnictví (LV)."""

    id: int
    number: int
    cadastral_territory_code: int | None = None
    cadastral_territory_name: str = ""

    @classmethod
    def from_api(cls, data: dict | None) -> CUZKTitleDeed | None:
        if not data:
            return None
        ku = data.get("katastralniUzemi") or {}
        return cls(
            id=int(data.get("id", 0)),
            number=int(data.get("cislo", 0)),
            cadastral_territory_code=ku.get("kod"),
            cadastral_territory_name=ku.get("nazev", ""),
        )


@dataclass
class CUZKUnitRef:
    """Minimal unit reference from a building response."""

    id: int
    unit_number: int

    @classmethod
    def from_api(cls, data: dict) -> CUZKUnitRef:
        return cls(
            id=int(data.get("id", 0)),
            unit_number=int(data.get("cisloJednotky", 0)),
        )


@dataclass
class CUZKCityPart:
    """Part of a city (cast obce) from CUZK."""

    code: int
    name: str
    municipality_code: int | None = None
    municipality_name: str = ""
    district_name: str = ""

    @classmethod
    def from_api(cls, data: dict) -> CUZKCityPart:
        obec = data.get("obec") or {}
        return cls(
            code=int(data.get("kod", 0)),
            name=data.get("nazev", ""),
            municipality_code=obec.get("kod") or data.get("kodObce"),
            municipality_name=obec.get("nazev", ""),
        )


@dataclass
class CUZKMunicipality:
    """Municipality (obec) from CUZK."""

    code: int
    name: str
    district_code: int | None = None

    @classmethod
    def from_api(cls, data: dict) -> CUZKMunicipality:
        return cls(
            code=int(data.get("kod", 0)),
            name=data.get("nazev", ""),
            district_code=data.get("kodOkresu"),
        )


@dataclass
class CUZKUnit:
    """Full unit (jednotka) from CUZK."""

    id: int
    unit_number: int
    unit_type_code: int | None = None
    unit_type_name: str = ""
    usage_code: int | None = None
    usage_name: str = ""
    share: CUZKShare | None = None
    lv: CUZKTitleDeed | None = None
    building_id: int | None = None

    @classmethod
    def from_api(cls, data: dict) -> CUZKUnit:
        typ = data.get("typJednotky") or {}
        usage = data.get("zpusobVyuziti") or {}
        stavba = data.get("vymezenaVeStavbe") or {}
        return cls(
            id=int(data.get("id", 0)),
            unit_number=int(data.get("cisloJednotky", 0)),
            unit_type_code=typ.get("kod"),
            unit_type_name=typ.get("nazev", ""),
            usage_code=usage.get("kod"),
            usage_name=usage.get("nazev", ""),
            share=CUZKShare.from_api(data.get("podilNaSpolecnychCastechDomu")),
            lv=CUZKTitleDeed.from_api(data.get("lv")),
            building_id=int(stavba["id"]) if stavba.get("id") else None,
        )

    @property
    def house_number(self) -> int:
        """
        Extract the house number (číslo popisné) from cisloJednotky.

        cisloJednotky encodes building_number + flat_number as a compound
        integer: e.g. 19370002 means house_number=1937, flat_number=2.
        For simple unit numbers (< 10000), this returns 0 (unknown).
        """
        if self.unit_number >= 10000:
            return self.unit_number // 10000
        return 0

    @property
    def flat_number_in_building(self) -> str:
        """
        Extract the flat number within the building from cisloJednotky.

        e.g. 19370002 → "2", 19380015 → "15", 5 → "5"
        """
        if self.unit_number >= 10000:
            return str(self.unit_number % 10000)
        return str(self.unit_number)


@dataclass
class CUZKBuilding:
    """Full building (stavba) from CUZK."""

    id: int
    building_type_code: int | None = None
    building_type_name: str = ""
    house_numbers: list[int] = field(default_factory=list)
    municipality_code: int | None = None
    municipality_name: str = ""
    city_part_code: int | None = None
    city_part_name: str = ""
    usage_code: int | None = None
    usage_name: str = ""
    lv: CUZKTitleDeed | None = None
    unit_refs: list[CUZKUnitRef] = field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict) -> CUZKBuilding:
        typ = data.get("typStavby") or {}
        obec = data.get("obec") or {}
        cast = data.get("castObce") or {}
        usage = data.get("zpusobVyuziti") or {}
        jednotky = data.get("jednotky") or []
        return cls(
            id=int(data.get("id", 0)),
            building_type_code=typ.get("kod"),
            building_type_name=typ.get("nazev", ""),
            house_numbers=data.get("cislaDomovni") or [],
            municipality_code=obec.get("kod"),
            municipality_name=obec.get("nazev", ""),
            city_part_code=cast.get("kod"),
            city_part_name=cast.get("nazev", ""),
            usage_code=usage.get("kod"),
            usage_name=usage.get("nazev", ""),
            lv=CUZKTitleDeed.from_api(data.get("lv")),
            unit_refs=[CUZKUnitRef.from_api(j) for j in jednotky],
        )


def group_units_by_house_number(
    units: list[CUZKUnit],
    house_numbers: list[int],
) -> dict[int, list[CUZKUnit]]:
    """
    Group units by their house number (extracted from cisloJednotky).

    Each cisloJednotky encodes building_number * 10000 + flat_number,
    e.g. 19370002 → building 1937, flat 2.

    If units have simple numbers (< 10000), they are assigned to the first
    house number.

    Returns a dict mapping house_number → list of units.
    """
    grouped: dict[int, list[CUZKUnit]] = {hn: [] for hn in house_numbers}
    for unit in units:
        hn = unit.house_number
        if hn in grouped:
            grouped[hn].append(unit)
        elif house_numbers:
            # Simple unit numbers or unrecognized prefix → first building
            grouped[house_numbers[0]].append(unit)
    return grouped


# ---------------------------------------------------------------------------
#  API Client
# ---------------------------------------------------------------------------
class CUZKApiError(Exception):
    """Raised when the CUZK API returns a non-2xx response."""

    def __init__(self, status_code: int, detail: str = ""):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"CUZK API error {status_code}: {detail}")


class CUZKClient:
    """
    Client for the CUZK REST API (Katastr nemovitostí).

    Usage::

        client = CUZKClient()
        building = client.get_building(951290101)
        units = [client.get_unit(u.id) for u in building.unit_refs]
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        if api_key:
            self.api_key = api_key
        else:
            # django.conf.settings does not expose custom NetBox config variables,
            # so we read directly from the netbox.configuration module which uses
            # __getattr__ to resolve values across all loaded config files
            # (configuration.py, extra.py, plugins.py …).
            # Fall back to os.environ as a last resort.
            try:
                import netbox.configuration as _nb_conf
                self.api_key = _nb_conf.CUZK_API_KEY
            except Exception:
                import os
                self.api_key = os.environ.get("CUZK_API_KEY", "")
        self.base_url = base_url or CUZK_API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update(
            {
                "apikey": f"{self.api_key}",
                "Accept": "application/json",
            }
        )

    def _get(self, path: str, params: dict | None = None) -> dict[str, Any]:
        """Perform a GET request and return the JSON response."""
        url = f"{self.base_url}{path}"
        logger.debug("CUZK API GET %s params=%s", url, params)
        try:
            resp = self.session.get(url, params=params, timeout=30)
        except requests.RequestException as exc:
            raise CUZKApiError(0, str(exc)) from exc

        if resp.status_code == 404:
            raise CUZKApiError(404, "Object not found in CUZK registry")
        if resp.status_code == 401:
            raise CUZKApiError(401, "Invalid or missing CUZK API key")
        if resp.status_code == 429:
            raise CUZKApiError(429, "CUZK API rate limit exceeded")
        if not resp.ok:
            raise CUZKApiError(resp.status_code, resp.text[:500])

        return resp.json()

    # ------------------------------------------------------------------
    #  Buildings (Stavby)
    # ------------------------------------------------------------------
    def get_building(self, building_id: int) -> CUZKBuilding:
        """Fetch a single building by its ISKN identifier."""
        data = self._get(f"/Stavby/{building_id}")
        return CUZKBuilding.from_api(data.get("data", {}))

    def search_building(
        self,
        city_part_code: int,
        house_number: int,
        building_type: int = 1,
    ) -> list[CUZKBuilding]:
        """
        Search for buildings by natural identification.

        Args:
            city_part_code: Kód části obce
            house_number: Číslo popisné/evidenční
            building_type: 1 = číslo popisné, 2 = číslo evidenční
        """
        data = self._get(
            "/Stavby/Vyhledani",
            params={
                "KodCastiObce": city_part_code,
                "TypStavby": building_type,
                "CisloDomovni": house_number,
            },
        )
        results = data.get("data") or []
        return [CUZKBuilding.from_api(b) for b in results]

    # ------------------------------------------------------------------
    #  City parts (Casti obci) - via enumeration endpoints
    # ------------------------------------------------------------------
    def list_districts(self) -> dict[int, str]:
        """
        Fetch all districts (okresy) and return a code->name mapping.

        Uses /CiselnikyUzemnichJednotek/Okresy.
        """
        data = self._get("/CiselnikyUzemnichJednotek/Okresy")
        results = data.get("data") or []
        return {int(d.get("kod", 0)): d.get("nazev", "") for d in results}

    def list_municipalities(self) -> list[CUZKMunicipality]:
        """
        Fetch the full list of municipalities (obce) from CUZK.

        Uses /CiselnikyUzemnichJednotek/Obce.
        """
        data = self._get("/CiselnikyUzemnichJednotek/Obce")
        results = data.get("data") or []
        return [CUZKMunicipality.from_api(item) for item in results]

    def search_municipalities(self, query: str) -> list[CUZKMunicipality]:
        """
        Fetch all municipalities and filter by name prefix (case-insensitive).

        The CUZK API does not provide a search endpoint for municipalities,
        so we fetch all and filter client-side.
        """
        all_municipalities = self.list_municipalities()
        q = query.lower()
        return [m for m in all_municipalities if m.name.lower().startswith(q)]

    def list_city_parts(self) -> list[CUZKCityPart]:
        """
        Fetch the full list of city parts (části obcí) from CUZK.

        Uses /CiselnikyUzemnichJednotek/CastiObci.
        """
        data = self._get("/CiselnikyUzemnichJednotek/CastiObci")
        results = data.get("data") or []
        return [CUZKCityPart.from_api(item) for item in results]

    def get_city_part(self, code: int) -> CUZKCityPart:
        """Fetch a single city part by its code."""
        data = self._get(f"/CiselnikyUzemnichJednotek/CastiObci/{code}")
        return CUZKCityPart.from_api(data.get("data", {}))

    def search_city_parts(self, query: str) -> list[CUZKCityPart]:
        """
        Search city parts by name prefix (case-insensitive).

        Fetches all city parts and filters client-side because the CUZK API
        does not provide a search endpoint for city parts.
        """
        all_parts = self.list_city_parts()
        q = query.lower()
        return [p for p in all_parts if p.name.lower().startswith(q)]

    def get_city_parts_for_municipality(self, municipality_code: int) -> list[CUZKCityPart]:
        """
        Get city parts belonging to a specific municipality.

        Fetches all city parts and filters by kodObce.
        """
        all_parts = self.list_city_parts()
        return [p for p in all_parts if p.municipality_code == municipality_code]

    # ------------------------------------------------------------------
    #  Units (Jednotky)
    # ------------------------------------------------------------------
    def get_unit(self, unit_id: int) -> CUZKUnit:
        """Fetch a single unit by its ISKN identifier."""
        data = self._get(f"/Jednotky/{unit_id}")
        return CUZKUnit.from_api(data.get("data", {}))

    def search_unit(
        self,
        city_part_code: int,
        house_number: int,
        unit_number: int,
        building_type: int = 1,
    ) -> list[CUZKUnit]:
        """
        Search for units by natural identification.

        Args:
            city_part_code: Kód části obce
            house_number: Číslo popisné/evidenční
            unit_number: Číslo jednotky
            building_type: 1 = číslo popisné, 2 = číslo evidenční
        """
        data = self._get(
            "/Jednotky/Vyhledani",
            params={
                "KodCastiObce": city_part_code,
                "TypStavby": building_type,
                "CisloDomovni": house_number,
                "CisloJednotky": unit_number,
            },
        )
        results = data.get("data") or []
        return [CUZKUnit.from_api(u) for u in results]

    # ------------------------------------------------------------------
    #  Convenience: load building with all its units
    # ------------------------------------------------------------------
    def get_building_with_units(self, building_id: int) -> tuple[CUZKBuilding, list[CUZKUnit]]:
        """
        Fetch a building and all its units in detail.

        Returns:
            Tuple of (building, list_of_units)
        """
        building = self.get_building(building_id)
        units: list[CUZKUnit] = []
        for ref in building.unit_refs:
            try:
                unit = self.get_unit(ref.id)
                units.append(unit)
            except CUZKApiError:
                logger.warning("Failed to fetch unit %s from CUZK", ref.id)
        return building, units
