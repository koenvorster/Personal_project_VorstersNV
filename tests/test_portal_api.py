"""
Tests voor api/routers/portal.py (Wave 9).

Dekt:
- POST /api/portal/projects → 201
- POST /api/portal/projects ontbrekend veld → 422
- GET /api/portal/projects → lijst
- GET /api/portal/projects?klant_email=... → gefilterd
- GET /api/portal/projects/{id}/status → 200 / 404
- GET /api/portal/projects/{id}/rapport → 404
- GET /api/portal/forecasts → lijst met kostenramingen
"""
import uuid

# ── Helpers ───────────────────────────────────────────────────────────────────

def _nieuw_project_payload(
    project_naam: str = "Test Analyse",
    klant_naam: str = "Klant BV",
    klant_email: str = "klant@voorbeeld.be",
    project_type: str = "code_analyse",
    beschrijving: str = "Een testproject",
) -> dict:
    return {
        "project_naam": project_naam,
        "klant_naam": klant_naam,
        "klant_email": klant_email,
        "project_type": project_type,
        "beschrijving": beschrijving,
    }


# ── POST /api/portal/projects ─────────────────────────────────────────────────

class TestProjectAanmaken:
    async def test_aanmaken_retourneert_201(self, client):
        r = await client.post("/api/portal/projects", json=_nieuw_project_payload())
        assert r.status_code == 201

    async def test_aanmaken_retourneert_project_id(self, client):
        r = await client.post("/api/portal/projects", json=_nieuw_project_payload())
        assert r.status_code == 201
        body = r.json()
        assert "project_id" in body
        assert body["project_id"]

    async def test_aanmaken_retourneert_correct_project_naam(self, client):
        payload = _nieuw_project_payload(project_naam="Mijn Analyseproject")
        r = await client.post("/api/portal/projects", json=payload)
        body = r.json()
        assert body["project_naam"] == "Mijn Analyseproject"

    async def test_aanmaken_retourneert_correct_klant_naam(self, client):
        payload = _nieuw_project_payload(klant_naam="Voorbeeldbedrijf NV")
        r = await client.post("/api/portal/projects", json=payload)
        body = r.json()
        assert body["klant_naam"] == "Voorbeeldbedrijf NV"

    async def test_aanmaken_status_is_draft(self, client):
        r = await client.post("/api/portal/projects", json=_nieuw_project_payload())
        body = r.json()
        assert body["status"] == "draft"

    async def test_aanmaken_voortgang_is_nul(self, client):
        r = await client.post("/api/portal/projects", json=_nieuw_project_payload())
        body = r.json()
        assert body["voortgang_percent"] == 0

    async def test_aanmaken_retourneert_aangemaakt_op(self, client):
        r = await client.post("/api/portal/projects", json=_nieuw_project_payload())
        body = r.json()
        assert "aangemaakt_op" in body
        assert body["aangemaakt_op"]

    async def test_aanmaken_ontbrekend_project_naam_geeft_422(self, client):
        payload = {
            "klant_naam": "Klant BV",
            "klant_email": "klant@voorbeeld.be",
        }
        r = await client.post("/api/portal/projects", json=payload)
        assert r.status_code == 422

    async def test_aanmaken_ontbrekend_klant_naam_geeft_422(self, client):
        payload = {
            "project_naam": "Test",
            "klant_email": "klant@voorbeeld.be",
        }
        r = await client.post("/api/portal/projects", json=payload)
        assert r.status_code == 422

    async def test_aanmaken_ontbrekend_klant_email_geeft_422(self, client):
        payload = {
            "project_naam": "Test",
            "klant_naam": "Klant BV",
        }
        r = await client.post("/api/portal/projects", json=payload)
        assert r.status_code == 422

    async def test_aanmaken_ongeldig_email_geeft_422(self, client):
        payload = _nieuw_project_payload(klant_email="geen-geldig-email")
        r = await client.post("/api/portal/projects", json=payload)
        assert r.status_code == 422

    async def test_aanmaken_leeg_body_geeft_422(self, client):
        r = await client.post("/api/portal/projects", json={})
        assert r.status_code == 422


# ── GET /api/portal/projects ──────────────────────────────────────────────────

class TestProjectenLijst:
    async def test_lege_lijst_bij_geen_projecten(self, client):
        r = await client.get("/api/portal/projects")
        assert r.status_code == 200
        assert r.json() == []

    async def test_aangemaakt_project_verschijnt_in_lijst(self, client):
        await client.post("/api/portal/projects", json=_nieuw_project_payload())
        r = await client.get("/api/portal/projects")
        assert r.status_code == 200
        assert len(r.json()) == 1

    async def test_meerdere_projecten_in_lijst(self, client):
        for i in range(3):
            await client.post(
                "/api/portal/projects",
                json=_nieuw_project_payload(
                    project_naam=f"Project {i}",
                    klant_email=f"klant{i}@test.be",
                ),
            )
        r = await client.get("/api/portal/projects")
        assert r.status_code == 200
        assert len(r.json()) == 3

    async def test_filter_op_klant_email_retourneert_gefilterde_lijst(self, client):
        await client.post(
            "/api/portal/projects",
            json=_nieuw_project_payload(klant_email="filter@test.be"),
        )
        await client.post(
            "/api/portal/projects",
            json=_nieuw_project_payload(klant_email="andere@test.be"),
        )
        r = await client.get("/api/portal/projects?klant_email=filter@test.be")
        assert r.status_code == 200
        resultaten = r.json()
        assert len(resultaten) == 1

    async def test_filter_op_onbekend_email_retourneert_lege_lijst(self, client):
        r = await client.get("/api/portal/projects?klant_email=onbekend@test.be")
        assert r.status_code == 200
        assert r.json() == []

    async def test_lijst_bevat_verwachte_velden(self, client):
        await client.post("/api/portal/projects", json=_nieuw_project_payload())
        r = await client.get("/api/portal/projects")
        project = r.json()[0]
        verwachte_velden = {
            "project_id", "project_naam", "klant_naam",
            "status", "voortgang_percent", "geschatte_minuten",
            "rapport_beschikbaar", "aangemaakt_op", "bijgewerkt_op",
        }
        assert verwachte_velden.issubset(project.keys())

    async def test_rapport_beschikbaar_is_false_bij_nieuw_project(self, client):
        await client.post("/api/portal/projects", json=_nieuw_project_payload())
        r = await client.get("/api/portal/projects")
        assert r.json()[0]["rapport_beschikbaar"] is False


# ── GET /api/portal/projects/{id}/status ─────────────────────────────────────

class TestProjectStatus:
    async def test_bestaand_project_retourneert_200(self, client):
        create_r = await client.post(
            "/api/portal/projects", json=_nieuw_project_payload()
        )
        project_id = create_r.json()["project_id"]
        r = await client.get(f"/api/portal/projects/{project_id}/status")
        assert r.status_code == 200

    async def test_status_response_bevat_project_id(self, client):
        create_r = await client.post(
            "/api/portal/projects", json=_nieuw_project_payload()
        )
        project_id = create_r.json()["project_id"]
        r = await client.get(f"/api/portal/projects/{project_id}/status")
        assert r.json()["project_id"] == project_id

    async def test_status_nieuw_project_is_draft(self, client):
        create_r = await client.post(
            "/api/portal/projects", json=_nieuw_project_payload()
        )
        project_id = create_r.json()["project_id"]
        r = await client.get(f"/api/portal/projects/{project_id}/status")
        assert r.json()["status"] == "draft"

    async def test_onbekend_project_id_retourneert_404(self, client):
        onbekend_id = str(uuid.uuid4())
        r = await client.get(f"/api/portal/projects/{onbekend_id}/status")
        assert r.status_code == 404

    async def test_404_bevat_detail_veld(self, client):
        onbekend_id = str(uuid.uuid4())
        r = await client.get(f"/api/portal/projects/{onbekend_id}/status")
        assert "detail" in r.json()


# ── GET /api/portal/projects/{id}/rapport ────────────────────────────────────

class TestProjectRapport:
    async def test_onbekend_id_retourneert_404(self, client):
        onbekend_id = str(uuid.uuid4())
        r = await client.get(f"/api/portal/projects/{onbekend_id}/rapport")
        assert r.status_code == 404

    async def test_nieuw_project_zonder_rapport_retourneert_404(self, client):
        create_r = await client.post(
            "/api/portal/projects", json=_nieuw_project_payload()
        )
        project_id = create_r.json()["project_id"]
        r = await client.get(f"/api/portal/projects/{project_id}/rapport")
        # Rapport is nog niet aangemaakt → 404
        assert r.status_code == 404


# ── GET /api/portal/forecasts ─────────────────────────────────────────────────

class TestKostenSchattingen:
    async def test_forecasts_retourneert_200(self, client):
        r = await client.get("/api/portal/forecasts")
        assert r.status_code == 200

    async def test_forecasts_bevat_project_type(self, client):
        r = await client.get("/api/portal/forecasts")
        body = r.json()
        assert "project_type" in body

    async def test_forecasts_bevat_geschatte_tokens(self, client):
        r = await client.get("/api/portal/forecasts")
        body = r.json()
        assert "geschatte_tokens" in body
        # CostForecaster kan 0 retourneren bij lege bestandenlijst — veld moet aanwezig zijn
        assert isinstance(body["geschatte_tokens"], int)

    async def test_forecasts_bevat_geschatte_minuten(self, client):
        r = await client.get("/api/portal/forecasts")
        body = r.json()
        assert "geschatte_minuten" in body
        assert isinstance(body["geschatte_minuten"], int)

    async def test_forecasts_bevat_betrouwbaarheid(self, client):
        r = await client.get("/api/portal/forecasts")
        body = r.json()
        assert "betrouwbaarheid_percent" in body

    async def test_forecasts_lokale_ollama_kosten_zijn_nul(self, client):
        r = await client.get("/api/portal/forecasts?project_type=code_analyse")
        body = r.json()
        # Lokale Ollama heeft geen kosten
        assert body["geschatte_kosten_eur"] == 0.0

    async def test_forecasts_met_project_type_param(self, client):
        r = await client.get("/api/portal/forecasts?project_type=bedrijfsproces")
        assert r.status_code == 200
        body = r.json()
        assert body["project_type"] == "bedrijfsproces"

    async def test_forecasts_met_bestanden_aantal(self, client):
        r = await client.get("/api/portal/forecasts?bestanden_aantal=20")
        assert r.status_code == 200
        body = r.json()
        # CostForecaster retourneert 0 bij lege bestanden — veld moet wel aanwezig zijn
        assert "geschatte_tokens" in body
        assert isinstance(body["geschatte_tokens"], int)

    async def test_forecasts_default_project_type_is_code_analyse(self, client):
        r = await client.get("/api/portal/forecasts")
        body = r.json()
        assert body["project_type"] == "code_analyse"
