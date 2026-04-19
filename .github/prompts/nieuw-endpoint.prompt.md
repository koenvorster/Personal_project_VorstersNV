---
mode: agent
description: Maak een compleet nieuw FastAPI endpoint aan voor VorstersNV, inclusief Pydantic schema, router, service-laag en Pytest test.
---

# Nieuw FastAPI Endpoint Generator

Maak een volledig, productieklaar FastAPI endpoint aan voor VorstersNV.

## Gevraagde informatie
- **Bounded context**: [Catalog / Orders / Inventory / Customer / Payments]
- **Resource naam**: [bijv. "product", "order", "klant"]
- **HTTP methode**: [GET / POST / PUT / DELETE]
- **Beschrijving**: [wat doet dit endpoint?]

## Wat te genereren

### 1. Pydantic Schema (`api/schemas/<resource>.py`)
```python
from pydantic import BaseModel, Field
from uuid import UUID
from decimal import Decimal

class <Resource>Create(BaseModel):
    # input velden

class <Resource>Response(BaseModel):
    id: UUID
    # output velden
    
    model_config = {"from_attributes": True}
```

### 2. SQLAlchemy Model check (`db/models/<resource>.py`)
Controleer of model bestaat. Zo niet — maak aan inclusief `TimestampMixin`.

### 3. Router (`api/routers/<resource>.py`)
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db

router = APIRouter(prefix="/<resources>", tags=["<Resource>"])

@router.get("/{id}", response_model=<Resource>Response)
async def get_<resource>(id: UUID, db: AsyncSession = Depends(get_db)):
    ...
```

### 4. Registreer in `api/main.py`
```python
from api.routers.<resource> import router as <resource>_router
app.include_router(<resource>_router, prefix="/api/v1")
```

### 5. Pytest Test (`tests/test_<resource>_router.py`)
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_<resource>_success(client: AsyncClient):
    response = await client.get("/api/v1/<resources>/test-id")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_<resource>_not_found(client: AsyncClient):
    response = await client.get("/api/v1/<resources>/nonexistent")
    assert response.status_code == 404
```

## Regels
- Altijd type hints (geen `Any`)
- Altijd `async def` voor database operaties  
- HTTPException met correcte statuscodes (404, 422, 409)
- Logs via `logger = logging.getLogger(__name__)`
- Geen `print()` statements
