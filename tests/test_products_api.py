"""
Tests voor de products API endpoints.
GET /api/products, GET /api/products/{id}, GET /api/products/slug/{slug},
GET /api/products/categorieen, PUT /api/products/{id}
"""
from decimal import Decimal

import pytest

from tests.conftest import maak_categorie, maak_product


class TestProductLijst:
    async def test_lege_lijst(self, client):
        """Zonder producten geeft de API een lege gepagineerde lijst terug."""
        r = await client.get("/api/products/")
        assert r.status_code == 200
        data = r.json()
        assert data["items"] == []
        assert data["totaal"] == 0
        assert data["pagina"] == 1

    async def test_geeft_actieve_producten(self, client, db_session):
        await maak_product(db_session, naam="Aardbei", slug="aardbei")
        await maak_product(db_session, naam="Inactief", slug="inactief", actief=False)

        r = await client.get("/api/products/")
        assert r.status_code == 200
        data = r.json()
        assert data["totaal"] == 1
        assert data["items"][0]["naam"] == "Aardbei"

    async def test_inactieve_producten_via_param(self, client, db_session):
        await maak_product(db_session, slug="p1", actief=True)
        await maak_product(db_session, naam="Inactief", slug="p2", actief=False)

        r = await client.get("/api/products/?actief=false")
        assert r.status_code == 200
        assert r.json()["totaal"] == 1
        assert r.json()["items"][0]["naam"] == "Inactief"

    async def test_zoek_op_naam(self, client, db_session):
        await maak_product(db_session, naam="Mango Haze", slug="mango-haze")
        await maak_product(db_session, naam="Blueberry Kush", slug="blueberry-kush")

        r = await client.get("/api/products/?zoek=mango")
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 1
        assert items[0]["naam"] == "Mango Haze"

    async def test_filter_op_categorie(self, client, db_session):
        cat = await maak_categorie(db_session, naam="CBD", slug="cbd")
        await maak_product(db_session, naam="CBD Olie", slug="cbd-olie", category_id=cat.id)
        await maak_product(db_session, naam="Andere", slug="andere")

        r = await client.get("/api/products/?categorie_slug=cbd")
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 1
        assert items[0]["naam"] == "CBD Olie"
        assert items[0]["category_naam"] == "CBD"

    async def test_paginatie(self, client, db_session):
        for i in range(5):
            await maak_product(db_session, naam=f"Product {i}", slug=f"product-{i}")

        r = await client.get("/api/products/?per_pagina=2&pagina=2")
        assert r.status_code == 200
        data = r.json()
        assert data["totaal"] == 5
        assert data["pagina"] == 2
        assert len(data["items"]) == 2


class TestProductDetail:
    async def test_haal_op_via_id(self, client, db_session):
        p = await maak_product(db_session, naam="Gorilla Glue", slug="gorilla-glue", prijs=Decimal("15.95"))

        r = await client.get(f"/api/products/{p.id}")
        assert r.status_code == 200
        data = r.json()
        assert data["naam"] == "Gorilla Glue"
        assert float(data["prijs"]) == pytest.approx(15.95)

    async def test_niet_gevonden_geeft_404(self, client):
        r = await client.get("/api/products/99999")
        assert r.status_code == 404

    async def test_haal_op_via_slug(self, client, db_session):
        await maak_product(db_session, naam="White Widow", slug="white-widow")

        r = await client.get("/api/products/slug/white-widow")
        assert r.status_code == 200
        assert r.json()["naam"] == "White Widow"

    async def test_slug_niet_gevonden_geeft_404(self, client):
        r = await client.get("/api/products/slug/bestaat-niet")
        assert r.status_code == 404


class TestCategorieën:
    async def test_lege_categorieën(self, client):
        r = await client.get("/api/products/categorieen")
        assert r.status_code == 200
        assert r.json() == []

    async def test_geeft_categorieën_gesorteerd(self, client, db_session):
        await maak_categorie(db_session, naam="Feminised", slug="feminised")
        await maak_categorie(db_session, naam="Autoflower", slug="autoflower")
        await maak_categorie(db_session, naam="CBD", slug="cbd")

        r = await client.get("/api/products/categorieen")
        assert r.status_code == 200
        namen = [c["naam"] for c in r.json()]
        assert namen == sorted(namen)


class TestProductBijwerken:
    async def test_prijs_bijwerken(self, admin_client, db_session):
        p = await maak_product(db_session, naam="Amnesia", slug="amnesia", prijs=Decimal("10.00"))

        r = await admin_client.put(f"/api/products/{p.id}", json={"prijs": "14.99"})
        assert r.status_code == 200
        assert float(r.json()["prijs"]) == pytest.approx(14.99)

    async def test_niet_bestaand_product_geeft_404(self, admin_client):
        r = await admin_client.put("/api/products/99999", json={"naam": "Nieuw"})
        assert r.status_code == 404

    async def test_geen_velden_geeft_400(self, admin_client, db_session):
        p = await maak_product(db_session, slug="leeg-update")
        r = await admin_client.put(f"/api/products/{p.id}", json={})
        assert r.status_code == 400
