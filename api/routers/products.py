"""
VorstersNV Products API Router — async SQLAlchemy + ORM.
"""
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.auth.jwt import TokenData, require_admin
from db.database import get_db
from db.models import Category, Product

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
async def list_categories(db: AsyncSession = Depends(get_db)):
    """Haal alle productcategorieën op."""
    result = await db.execute(select(Category).order_by(Category.naam))
    cats = result.scalars().all()
    return [{"id": c.id, "naam": c.naam, "slug": c.slug, "omschrijving": c.omschrijving} for c in cats]


@router.get("/", response_model=ProductListResponse, summary="Lijst van producten")
async def list_products(
    pagina: int = Query(1, ge=1),
    per_pagina: int = Query(20, ge=1, le=100),
    categorie_slug: str | None = Query(None, description="Filter op categorie slug"),
    zoek: str | None = Query(None),
    actief: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """Haal gepagineerde lijst van producten op met optionele filters."""
    stmt = (
        select(Product)
        .options(selectinload(Product.category))
        .where(Product.actief == actief)
    )

    if zoek:
        stmt = stmt.where(
            Product.naam.ilike(f"%{zoek}%") | Product.korte_beschrijving.ilike(f"%{zoek}%")
        )
    if categorie_slug:
        stmt = stmt.join(Category).where(Category.slug == categorie_slug)

    count_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    totaal = count_result.scalar() or 0

    stmt = stmt.order_by(Product.id).limit(per_pagina).offset((pagina - 1) * per_pagina)
    result = await db.execute(stmt)
    products = result.scalars().all()

    items = [_to_response(p) for p in products]
    return ProductListResponse(items=items, totaal=totaal, pagina=pagina, per_pagina=per_pagina)


@router.get("/slug/{slug}", response_model=ProductResponse, summary="Product via slug")
async def get_product_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    """Haal een product op via de URL-slug."""
    result = await db.execute(
        select(Product).options(selectinload(Product.category)).where(Product.slug == slug)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product '{slug}' niet gevonden")
    return _to_response(product)


@router.get("/{product_id}", response_model=ProductResponse, summary="Product detail")
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Haal een specifiek product op via ID."""
    result = await db.execute(
        select(Product).options(selectinload(Product.category)).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} niet gevonden")
    return _to_response(product)


@router.put("/{product_id}", response_model=ProductResponse, summary="Product bijwerken")
async def update_product(
    product_id: int,
    body: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    _: TokenData = Depends(require_admin),
):
    """Werk een bestaand product bij (admin)."""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Geen velden om bij te werken")

    result = await db.execute(select(Product).where(Product.id == product_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Product {product_id} niet gevonden")

    await db.execute(update(Product).where(Product.id == product_id).values(**updates))
    await db.commit()

    return await get_product(product_id, db)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_response(p: Product) -> ProductResponse:
    return ProductResponse(
        id=p.id, naam=p.naam, slug=p.slug,
        korte_beschrijving=p.korte_beschrijving, beschrijving=p.beschrijving,
        prijs=p.prijs, voorraad=p.voorraad, afbeelding_url=p.afbeelding_url,
        kenmerken=p.kenmerken, tags=p.tags, actief=p.actief,
        category_id=p.category_id,
        category_naam=p.category.naam if p.category else None,
    )
