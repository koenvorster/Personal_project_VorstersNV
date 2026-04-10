"""
VorstersNV Products API Router — verbonden met PostgreSQL.
"""
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
import os

DB_URL = os.environ.get("DB_URL", "postgresql+psycopg2://vorstersNV:dev-password-change-me@localhost:5432/vorstersNV")
engine = create_engine(DB_URL, pool_pre_ping=True)

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class ProductResponse(BaseModel):
    id: int
    naam: str
    slug: str
    korte_beschrijving: str | None = None
    beschrijving: str | None = None
    prijs: Decimal
    voorraad: int
    afbeelding_url: str | None = None
    kenmerken: dict | None = None
    tags: list | None = None
    actief: bool
    category_id: int | None = None
    category_naam: str | None = None

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    totaal: int
    pagina: int
    per_pagina: int


class ProductUpdate(BaseModel):
    naam: str | None = None
    korte_beschrijving: str | None = None
    beschrijving: str | None = None
    prijs: Decimal | None = None
    voorraad: int | None = None
    actief: bool | None = None
    kenmerken: dict | None = None
    tags: list[str] | None = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/categorieen", summary="Alle categorieën")
async def list_categories():
    """Haal alle productcategorieën op."""
    with Session(engine) as db:
        rows = db.execute(text("SELECT id, naam, slug, omschrijving FROM categories ORDER BY naam")).fetchall()
        return [{"id": r.id, "naam": r.naam, "slug": r.slug, "omschrijving": r.omschrijving} for r in rows]


@router.get("/", response_model=ProductListResponse, summary="Lijst van producten")
async def list_products(
    pagina: int = Query(1, ge=1),
    per_pagina: int = Query(20, ge=1, le=100),
    categorie_slug: str | None = Query(None, description="Filter op categorie slug (feminised/autoflower/cbd)"),
    zoek: str | None = Query(None),
    actief: bool = Query(True),
):
    """Haal gepagineerde lijst van producten op met optionele filters."""
    with Session(engine) as db:
        where = ["p.actief = :actief"]
        params: dict = {"actief": actief, "offset": (pagina - 1) * per_pagina, "limit": per_pagina}

        if zoek:
            where.append("(p.naam ILIKE :zoek OR p.korte_beschrijving ILIKE :zoek)")
            params["zoek"] = f"%{zoek}%"
        if categorie_slug:
            where.append("c.slug = :cat_slug")
            params["cat_slug"] = categorie_slug

        where_sql = " AND ".join(where)
        count_params = {k: v for k, v in params.items() if k not in ("offset", "limit")}

        rows = db.execute(text(f"""
            SELECT p.id, p.naam, p.slug, p.korte_beschrijving, p.beschrijving,
                   p.prijs, p.voorraad, p.afbeelding_url, p.kenmerken, p.tags,
                   p.actief, p.category_id, c.naam as category_naam
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE {where_sql}
            ORDER BY p.id
            LIMIT :limit OFFSET :offset
        """), params).fetchall()

        total = db.execute(text(f"""
            SELECT COUNT(*) FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE {where_sql}
        """), count_params).scalar()

        items = [ProductResponse(
            id=r.id, naam=r.naam, slug=r.slug,
            korte_beschrijving=r.korte_beschrijving, beschrijving=r.beschrijving,
            prijs=r.prijs, voorraad=r.voorraad, afbeelding_url=r.afbeelding_url,
            kenmerken=r.kenmerken, tags=r.tags, actief=r.actief,
            category_id=r.category_id, category_naam=r.category_naam,
        ) for r in rows]

        return ProductListResponse(items=items, totaal=total or 0, pagina=pagina, per_pagina=per_pagina)


@router.get("/slug/{slug}", response_model=ProductResponse, summary="Product via slug")
async def get_product_by_slug(slug: str):
    """Haal een product op via de URL-slug."""
    with Session(engine) as db:
        r = db.execute(text("""
            SELECT p.id, p.naam, p.slug, p.korte_beschrijving, p.beschrijving,
                   p.prijs, p.voorraad, p.afbeelding_url, p.kenmerken, p.tags,
                   p.actief, p.category_id, c.naam as category_naam
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.slug = :slug
        """), {"slug": slug}).fetchone()
        if not r:
            raise HTTPException(status_code=404, detail=f"Product '{slug}' niet gevonden")
        return ProductResponse(**r._mapping)


@router.get("/{product_id}", response_model=ProductResponse, summary="Product detail")
async def get_product(product_id: int):
    """Haal een specifiek product op via ID."""
    with Session(engine) as db:
        r = db.execute(text("""
            SELECT p.id, p.naam, p.slug, p.korte_beschrijving, p.beschrijving,
                   p.prijs, p.voorraad, p.afbeelding_url, p.kenmerken, p.tags,
                   p.actief, p.category_id, c.naam as category_naam
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = :id
        """), {"id": product_id}).fetchone()
        if not r:
            raise HTTPException(status_code=404, detail=f"Product {product_id} niet gevonden")
        return ProductResponse(**r._mapping)


@router.put("/{product_id}", response_model=ProductResponse, summary="Product bijwerken")
async def update_product(product_id: int, update: ProductUpdate):
    """Werk een bestaand product bij (admin)."""
    with Session(engine) as db:
        existing = db.execute(text("SELECT id FROM products WHERE id = :id"), {"id": product_id}).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail=f"Product {product_id} niet gevonden")

        updates = {k: v for k, v in update.model_dump().items() if v is not None}
        if not updates:
            raise HTTPException(status_code=400, detail="Geen velden om bij te werken")

        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        updates["id"] = product_id
        db.execute(text(f"UPDATE products SET {set_clause} WHERE id = :id"), updates)
        db.commit()

    return await get_product(product_id)
