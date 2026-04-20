"""
Tests voor de bestellingen & betalingen API endpoints.
POST /api/bestellingen, GET /api/bestellingen/{id},
POST /api/betalingen/{id}/simuleer
"""
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from tests.conftest import maak_product


def _bestel_body(product_id: int, aantal: int = 1) -> dict:
    return {
        "items": [{"product_id": product_id, "naam": "Test", "prijs": "10.00", "aantal": aantal}],
        "klant_naam": "Koen Vorster",
        "klant_email": "koen@voorbeeld.be",
        "klant_adres": "Teststraat 1",
        "klant_stad": "Antwerpen",
        "klant_postcode": "2000",
        "klant_land": "BE",
    }


class TestBestellingAanmaken:
    async def test_happy_path(self, client, db_session):
        """Correcte bestelling met voldoende voorraad → 201 + betaallink."""
        p = await maak_product(db_session, prijs=Decimal("20.00"), voorraad=5)

        r = await client.post("/api/bestellingen", json=_bestel_body(p.id))
        assert r.status_code == 201
        data = r.json()
        assert "bestelling_id" in data
        assert data["bestelling_id"].startswith("BST-")
        assert data["status"] == "wacht_op_betaling"
        assert "betaal_url" in data
        assert float(data["totaal_excl"]) == pytest.approx(20.00)
        assert float(data["btw"]) == pytest.approx(4.20)       # 20 * 21%
        assert float(data["totaal_incl"]) == pytest.approx(24.20)

    async def test_verzendkosten_gratis_boven_50(self, client, db_session):
        """Bestelling ≥ €50 excl. BTW → gratis verzending."""
        p = await maak_product(db_session, prijs=Decimal("60.00"), voorraad=3)

        r = await client.post("/api/bestellingen", json=_bestel_body(p.id))
        assert r.status_code == 201
        # totaal_incl = 60 + 12.60 BTW = 72.60 (geen verzendkosten)
        assert float(r.json()["totaal_excl"]) == pytest.approx(60.00)

    async def test_te_weinig_voorraad_geeft_422(self, client, db_session):
        """Meer bestellen dan voorraad → 422 met voorraad_problemen."""
        p = await maak_product(db_session, voorraad=2)

        r = await client.post("/api/bestellingen", json=_bestel_body(p.id, aantal=5))
        assert r.status_code == 422
        data = r.json()
        assert "voorraad_problemen" in data["detail"]
        assert len(data["detail"]["voorraad_problemen"]) == 1

    async def test_onbekend_product_geeft_422(self, client):
        """Niet-bestaand product_id → 422."""
        r = await client.post("/api/bestellingen", json=_bestel_body(product_id=99999))
        assert r.status_code == 422
        assert "voorraad_problemen" in r.json()["detail"]

    async def test_inactief_product_geeft_422(self, client, db_session):
        """Inactief product bestellen → 422."""
        p = await maak_product(db_session, actief=False, slug="inactief-bestel")

        r = await client.post("/api/bestellingen", json=_bestel_body(p.id))
        assert r.status_code == 422

    async def test_voorraad_wordt_gereserveerd(self, client, db_session):
        """Na bestelling moet de voorraad in de DB afgenomen zijn."""
        from sqlalchemy import select
        from db.models import Product

        p = await maak_product(db_session, voorraad=10)

        await client.post("/api/bestellingen", json=_bestel_body(p.id, aantal=3))

        await db_session.refresh(p)
        assert p.voorraad == 7

    async def test_meerdere_items(self, client, db_session):
        """Bestelling met meerdere producten."""
        p1 = await maak_product(db_session, naam="P1", slug="p1", prijs=Decimal("10.00"), voorraad=5)
        p2 = await maak_product(db_session, naam="P2", slug="p2", prijs=Decimal("20.00"), voorraad=5)

        body = {
            "items": [
                {"product_id": p1.id, "naam": "P1", "prijs": "10.00", "aantal": 2},
                {"product_id": p2.id, "naam": "P2", "prijs": "20.00", "aantal": 1},
            ],
            "klant_naam": "Koen", "klant_email": "k@test.be",
            "klant_adres": "Weg 1", "klant_stad": "Gent",
            "klant_postcode": "9000", "klant_land": "BE",
        }
        r = await client.post("/api/bestellingen", json=body)
        assert r.status_code == 201
        assert float(r.json()["totaal_excl"]) == pytest.approx(40.00)  # 2×10 + 1×20


class TestBestellingStatus:
    async def test_bestaande_bestelling_ophalen(self, client, db_session):
        """Na aanmaken kan de bestelling opgezocht worden via het ID."""
        p = await maak_product(db_session, prijs=Decimal("15.00"), voorraad=5)

        post_r = await client.post("/api/bestellingen", json=_bestel_body(p.id))
        bestelling_id = post_r.json()["bestelling_id"]

        r = await client.get(f"/api/bestellingen/{bestelling_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["bestelling_id"] == bestelling_id
        assert data["klant_email"] == "koen@voorbeeld.be"
        assert len(data["items"]) == 1

    async def test_niet_bestaande_bestelling_geeft_404(self, client):
        r = await client.get("/api/bestellingen/BST-ONBEKEND")
        assert r.status_code == 404


class TestBetalingSimuleren:
    async def test_simuleer_betaald(self, client, db_session):
        """Betaling simuleren op 'paid' zet de status van de order op paid."""
        p = await maak_product(db_session, voorraad=5)

        post_r = await client.post("/api/bestellingen", json=_bestel_body(p.id))
        betaling_id = post_r.json()["betaal_url"].split("betaling_id=")[1].split("&")[0]

        r = await client.post(f"/api/betalingen/{betaling_id}/simuleer", json={"status": "paid"})
        assert r.status_code == 200
        assert r.json()["status"] == "paid"

    async def test_simuleer_geannuleerd_herstelt_voorraad(self, client, db_session):
        """Geannuleerde betaling moet de gereserveerde voorraad terugboeken."""
        from db.models import Product
        from sqlalchemy import select

        p = await maak_product(db_session, voorraad=5)

        post_r = await client.post("/api/bestellingen", json=_bestel_body(p.id, aantal=2))
        betaling_id = post_r.json()["betaal_url"].split("betaling_id=")[1].split("&")[0]

        await client.post(f"/api/betalingen/{betaling_id}/simuleer", json={"status": "cancelled"})

        await db_session.refresh(p)
        assert p.voorraad == 5  # teruggesteld naar origineel

    async def test_ongeldige_status_geeft_422(self, client, db_session):
        """Ongeldige status waarde → 422."""
        p = await maak_product(db_session, voorraad=3)
        post_r = await client.post("/api/bestellingen", json=_bestel_body(p.id))
        betaling_id = post_r.json()["betaal_url"].split("betaling_id=")[1].split("&")[0]

        r = await client.post(f"/api/betalingen/{betaling_id}/simuleer", json={"status": "onbekend"})
        assert r.status_code == 422

    async def test_onbekende_betaling_geeft_404(self, client):
        r = await client.post("/api/betalingen/PAY-ONBEKEND/simuleer", json={"status": "paid"})
        assert r.status_code == 404
