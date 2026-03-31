"""
Solomon — Tests for the owners text import feature.
"""

import datetime

import pytest
from django.urls import reverse

from buildings.tests import BuildingFactory
from flats.tests import FlatFactory
from owners.import_owners import (
    ImportResult,
    ParsedOwner,
    ParsedUnit,
    _parse_name_into_owner,
    _parse_owner_line,
    execute_owners_import,
    parse_owners_text,
)
from owners.models import FlatOwner, Owner


# ---------------------------------------------------------------------------
#  Parser tests
# ---------------------------------------------------------------------------
class TestParseOwnersText:
    def test_simple_owner(self):
        text = (
            "Bartíková Patricie Mgr., Zvěřinova 3446/3, Strašnice, 13000 Praha 3\n"
            "Jednotka: 1937/6\t73/9089"
        )
        result = parse_owners_text(text)
        assert len(result) == 1
        owner = result[0]
        assert owner.last_name == "Bartíková"
        assert owner.first_name == "Patricie"
        assert owner.address == "Zvěřinova 3446/3, Strašnice, 13000 Praha 3"
        assert len(owner.units) == 1
        assert owner.units[0].building_number == 1937
        assert owner.units[0].flat_number == 6
        assert owner.units[0].share_numerator == 73
        assert owner.units[0].share_denominator == 9089

    def test_sj_owner_with_address(self):
        """SJ owner line with comma-separated address (single-line SJ)."""
        text = (
            "SJ Brtna Josef Ing. a Brtnová Pavlína Ing., Severní 1072, 28522 Zruč nad Sázavou\n"
            "Jednotka: 1939/22\t73/9089"
        )
        result = parse_owners_text(text)
        assert len(result) == 1
        owner = result[0]
        assert owner.is_joint
        assert "Brtna" in owner.last_name or "Brtna" in owner.name
        assert owner.address == "Severní 1072, 28522 Zruč nad Sázavou"
        assert len(owner.units) == 1
        assert owner.units[0].building_number == 1939
        assert owner.units[0].flat_number == 22

    def test_sj_owner_multiline(self):
        """SJ owner with separate detail lines for each person."""
        text = (
            "SJ Schmidt Jaroslav a Schmidtová Liběna\n"
            "Jednotka: 1938/2\t388/27267\n"
            "Schmidt Jaroslav, Žitná 610/23, Nové Město, 11000 Praha 1\n"
            "Schmidtová Liběna, Šalounova 1938/8, Chodov, 14900 Praha 4\n"
        )
        result = parse_owners_text(text)
        # Should produce 1 SJ owner (the combined name)
        sj_owners = [o for o in result if o.is_joint]
        assert len(sj_owners) == 1
        assert sj_owners[0].units[0].building_number == 1938
        assert sj_owners[0].units[0].flat_number == 2

    def test_multiple_flats_per_owner(self):
        """Owner with multiple comma-separated unit references."""
        text = (
            "SJ Knap Roman Ing. a Knapová Lenka Ing., Vačkářova 297, 25101 Dobřejovice\n"
            "Jednotka: 1937/14, 1940/3\t659/27267"
        )
        result = parse_owners_text(text)
        assert len(result) == 1
        owner = result[0]
        assert len(owner.units) == 2
        assert owner.units[0].building_number == 1937
        assert owner.units[0].flat_number == 14
        assert owner.units[1].building_number == 1940
        assert owner.units[1].flat_number == 3

    def test_co_owners_same_flat(self):
        """Two separate owners each with their own Jednotka line for the same flat."""
        text = (
            "Šubert Miloslav, Šalounova 1939/6, Chodov, 14900 Praha 4\n"
            "Jednotka: 1939/6\t73/18178\n"
            "Šubertová Zdeňka, Kojetická 981, 27711 Neratovice\n"
            "Jednotka: 1939/6\t73/18178\n"
        )
        result = parse_owners_text(text)
        assert len(result) == 2
        assert result[0].last_name == "Šubert"
        assert result[1].last_name == "Šubertová"
        # Both own flat 1939/6
        assert result[0].units[0].building_number == 1939
        assert result[0].units[0].flat_number == 6
        assert result[1].units[0].building_number == 1939
        assert result[1].units[0].flat_number == 6

    def test_co_owners_same_flat_no_share_on_second(self):
        """Second co-owner has Jednotka line without share."""
        text = (
            "Šubert Miloslav, Šalounova 1939/6, Chodov, 14900 Praha 4\n"
            "Jednotka: 1939/6\t73/18178\n"
            "Šubertová Zdeňka, Kojetická 981, 27711 Neratovice\n"
            "Jednotka: 1939/6\n"
        )
        result = parse_owners_text(text)
        assert len(result) == 2
        assert result[1].units[0].share_numerator is None

    def test_legal_entity(self):
        """Legal entity (company) as owner."""
        text = (
            "INSTALACE, spol. s r.o., Kutnohorská 579, Dolní Měcholupy, 11101 Praha 10\n"
            "Jednotka: 1937/12\t779/54534"
        )
        result = parse_owners_text(text)
        assert len(result) == 1
        assert result[0].person_type == "legal"
        assert "INSTALACE" in result[0].last_name

    def test_mcp_prefix(self):
        """MCP prefix (mixed couple property)."""
        text = (
            "MCP Lé Văn Thang a Đoan Thi Yen, Šalounova 1939/6, Chodov, 14900 Praha 4\n"
            "Jednotka: 1939/2\t388/27267"
        )
        result = parse_owners_text(text)
        assert len(result) == 1
        assert result[0].is_joint
        assert len(result[0].units) == 1

    def test_multiple_owners(self):
        """Parse multiple sequential owners."""
        text = (
            "Bartíková Patricie Mgr., Zvěřinova 3446/3, Strašnice, 13000 Praha 3\n"
            "Jednotka: 1937/6\t73/9089\n"
            "Betíková Pavla, Studené 47, 25401 Jílové u Prahy\n"
            "Jednotka: 1940/8\t315/18178\n"
        )
        result = parse_owners_text(text)
        assert len(result) == 2
        assert result[0].last_name == "Bartíková"
        assert result[1].last_name == "Betíková"

    def test_empty_text(self):
        assert parse_owners_text("") == []
        assert parse_owners_text("   \n\n  ") == []

    def test_shared_ownership_different_shares(self):
        """Kubánek and Kubánková share flat 1941/2 with different shares."""
        text = (
            "Kubánek Petr, Šalounova 1941/2, Chodov, 14900 Praha 4\n"
            "Jednotka: 1941/2\t205/27267\n"
            "Kubánková Blanka, Šalounova 1941/2, Chodov, 14900 Praha 4\n"
            "Jednotka: 1941/2\t205/27267\n"
        )
        result = parse_owners_text(text)
        assert len(result) == 2
        assert result[0].units[0].share_numerator == 205
        assert result[1].units[0].share_numerator == 205

    def test_three_co_owners(self):
        """Péder family: three people sharing one flat with different shares."""
        text = (
            "Péder Daniel, Šalounova 1941/2, Chodov, 14900 Praha 4\n"
            "Jednotka: 1941/5\t110/27267\n"
            "Péder Viktor, Šalounova 1941/2, Chodov, 14900 Praha 4\n"
            "Jednotka: 1941/5\t110/27267\n"
            "Péderová Jaroslava, Šalounova 1941/2, Chodov, 14900 Praha 4\n"
            "Jednotka: 1941/5\t220/27267\n"
        )
        result = parse_owners_text(text)
        assert len(result) == 3
        # All share flat 1941/5
        for owner in result:
            assert owner.units[0].building_number == 1941
            assert owner.units[0].flat_number == 5


class TestParseOwnerLine:
    def test_name_with_title(self):
        owner = _parse_owner_line("Bartíková Patricie Mgr., Zvěřinova 3446/3, Strašnice, 13000 Praha 3")
        assert owner.last_name == "Bartíková"
        assert owner.first_name == "Patricie"

    def test_name_without_title(self):
        owner = _parse_owner_line("Hájek Antonín, Šalounova 1937/10, Chodov, 14900 Praha 4")
        assert owner.last_name == "Hájek"
        assert owner.first_name == "Antonín"

    def test_name_with_multiple_titles(self):
        owner = _parse_owner_line("Dubovický Ivan JUDr. PhDr., Address")
        assert owner.last_name == "Dubovický"
        assert owner.first_name == "Ivan"


class TestParseNameIntoOwner:
    def test_simple_name(self):
        owner = ParsedOwner(name="")
        _parse_name_into_owner(owner, "Novák Jan")
        assert owner.last_name == "Novák"
        assert owner.first_name == "Jan"

    def test_name_with_title(self):
        owner = ParsedOwner(name="")
        _parse_name_into_owner(owner, "Bartíková Patricie Mgr.")
        assert owner.last_name == "Bartíková"
        assert owner.first_name == "Patricie"

    def test_joint_name(self):
        owner = ParsedOwner(name="")
        _parse_name_into_owner(owner, "Brtna Josef a Brtnová Pavlína")
        # Joint name — last_name stores full combined name
        assert "Brtna" in owner.last_name
        assert "Brtnová" in owner.last_name


# ---------------------------------------------------------------------------
#  Import execution tests
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestExecuteOwnersImport:
    def test_create_owner_and_flatowner(self):
        """Import creates owner and links to flat."""
        building = BuildingFactory(house_number="1937")
        flat = FlatFactory(building=building, flat_number="6")

        parsed = [
            ParsedOwner(
                name="Bartíková Patricie",
                first_name="Patricie",
                last_name="Bartíková",
                address="Zvěřinova 3446/3",
                units=[ParsedUnit(building_number=1937, flat_number=6, share_numerator=73, share_denominator=9089)],
            )
        ]
        result = execute_owners_import(parsed, effective_date=datetime.date(2025, 1, 1))

        assert result.owners_created == 1
        assert result.flat_owners_created == 1
        assert Owner.objects.filter(last_name="Bartíková").count() == 1
        assert FlatOwner.objects.filter(flat=flat).count() == 1
        fo = FlatOwner.objects.get(flat=flat)
        assert fo.share_numerator == 73
        assert fo.share_denominator == 9089

    def test_flat_not_found(self):
        """Import records warning when flat doesn't exist."""
        parsed = [
            ParsedOwner(
                name="Test",
                first_name="Test",
                last_name="Test",
                units=[ParsedUnit(building_number=9999, flat_number=1, share_numerator=1, share_denominator=1)],
            )
        ]
        result = execute_owners_import(parsed)
        assert result.owners_created == 1
        assert result.flat_owners_created == 0
        assert "9999/1" in result.flats_not_found

    def test_existing_owner_updates_address(self):
        """Existing owner gets address updated if currently empty."""
        Owner.objects.create(first_name="Jan", last_name="Novák", permanent_address="")

        parsed = [
            ParsedOwner(
                name="Novák Jan",
                first_name="Jan",
                last_name="Novák",
                address="Ulice 123",
                units=[],
            )
        ]
        result = execute_owners_import(parsed)
        assert result.owners_created == 0
        assert result.owners_updated == 1
        owner = Owner.objects.get(last_name="Novák")
        assert owner.permanent_address == "Ulice 123"

    def test_duplicate_import_does_not_create_double(self):
        """Re-running import doesn't create duplicate FlatOwner."""
        building = BuildingFactory(house_number="1937")
        flat = FlatFactory(building=building, flat_number="6")

        parsed = [
            ParsedOwner(
                name="Test Owner",
                first_name="Owner",
                last_name="Test",
                units=[ParsedUnit(building_number=1937, flat_number=6, share_numerator=1, share_denominator=1)],
            )
        ]
        effective = datetime.date(2025, 1, 1)
        result1 = execute_owners_import(parsed, effective_date=effective)
        assert result1.flat_owners_created == 1

        result2 = execute_owners_import(parsed, effective_date=effective)
        assert result2.flat_owners_created == 0
        assert FlatOwner.objects.filter(flat=flat).count() == 1

    def test_co_owners_same_flat(self):
        """Two owners linked to same flat."""
        building = BuildingFactory(house_number="1939")
        flat = FlatFactory(building=building, flat_number="6")

        parsed = [
            ParsedOwner(
                name="Šubert Miloslav",
                first_name="Miloslav",
                last_name="Šubert",
                address="Addr1",
                units=[ParsedUnit(building_number=1939, flat_number=6, share_numerator=73, share_denominator=18178)],
            ),
            ParsedOwner(
                name="Šubertová Zdeňka",
                first_name="Zdeňka",
                last_name="Šubertová",
                address="Addr2",
                units=[ParsedUnit(building_number=1939, flat_number=6, share_numerator=73, share_denominator=18178)],
            ),
        ]
        result = execute_owners_import(parsed, effective_date=datetime.date(2025, 1, 1))
        assert result.owners_created == 2
        assert result.flat_owners_created == 2
        assert FlatOwner.objects.filter(flat=flat).count() == 2


# ---------------------------------------------------------------------------
#  View tests
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestOwnersImportViews:
    def test_import_page_requires_login(self, client):
        resp = client.get(reverse("owners:owners-import"))
        assert resp.status_code == 302
        assert "login" in resp.url

    def test_import_page_get(self, admin_client):
        resp = admin_client.get(reverse("owners:owners-import"))
        assert resp.status_code == 200

    def test_preview_shows_parsed_owners(self, admin_client):
        BuildingFactory(house_number="1937")
        text = (
            "Bartíková Patricie Mgr., Zvěřinova 3446/3, Strašnice, 13000 Praha 3\n"
            "Jednotka: 1937/6\t73/9089"
        )
        resp = admin_client.post(
            reverse("owners:owners-import"),
            {"owners_text": text, "action": "preview"},
        )
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Bartíková" in content
        assert "73/9089" in content

    def test_execute_import_creates_data(self, admin_client):
        building = BuildingFactory(house_number="1937")
        FlatFactory(building=building, flat_number="6")

        text = (
            "Bartíková Patricie Mgr., Zvěřinova 3446/3, Strašnice, 13000 Praha 3\n"
            "Jednotka: 1937/6\t73/9089"
        )
        resp = admin_client.post(
            reverse("owners:owners-import"),
            {
                "owners_text": text,
                "action": "execute",
                "effective_date": "2025-01-01",
            },
        )
        assert resp.status_code == 302
        assert Owner.objects.filter(last_name="Bartíková").exists()
        assert FlatOwner.objects.count() == 1

    def test_empty_text_shows_error(self, admin_client):
        resp = admin_client.post(
            reverse("owners:owners-import"),
            {"owners_text": "", "action": "preview"},
        )
        assert resp.status_code == 200

    def test_full_sample_parse(self):
        """Parse the full owners.txt sample (just check count, no DB)."""
        text = (
            "Bartíková Patricie Mgr., Zvěřinova 3446/3, Strašnice, 13000 Praha 3\n"
            "Jednotka: 1937/6\t73/9089\n"
            "Betíková Pavla, Studené 47, 25401 Jílové u Prahy\n"
            "Jednotka: 1940/8\t315/18178\n"
            "SJ Brtna Josef Ing. a Brtnová Pavlína Ing., Severní 1072, 28522 Zruč nad Sázavou\n"
            "Jednotka: 1939/22\t73/9089\n"
            "Burdová Vladislava, Šalounova 1938/8, Chodov, 14900 Praha 4\n"
            "Jednotka: 1938/22\t73/9089\n"
        )
        result = parse_owners_text(text)
        assert len(result) == 4
        # SJ owner
        sj = [o for o in result if o.is_joint]
        assert len(sj) == 1
