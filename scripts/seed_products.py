"""
Seed script: laadt demo cannabis zaden producten in de PostgreSQL DB.
Gebruik: python3 scripts/seed_products.py
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from db.models.models import Base, Category, Product

DB_URL = os.environ.get(
    "DB_URL",
    "postgresql+psycopg2://vorstersNV:dev-password-change-me@localhost:5432/vorstersNV",
)

engine = create_engine(DB_URL)

CATEGORIES = [
    {"naam": "Feminised", "slug": "feminised", "omschrijving": "Gefeminiseerde cannabis zaden – 99% vrouwelijke planten gegarandeerd."},
    {"naam": "Autoflower", "slug": "autoflower", "omschrijving": "Automatisch bloeiende zaden – ideaal voor beginners en snelle oogsten."},
    {"naam": "CBD", "slug": "cbd", "omschrijving": "High-CBD, low-THC zaden – voor medicinaal en wellness gebruik."},
]

PRODUCTS = [
    # Feminised
    {
        "naam": "White Widow Feminised",
        "slug": "white-widow-feminised",
        "korte_beschrijving": "Klassieke Europese winnaar met hars-rijke toppen.",
        "beschrijving": "White Widow is een van de meest bekende cannabis strains ter wereld. Deze feminised versie garandeert vrouwelijke planten met indrukwekkende harsproductie. THC: 20%, bloeitijd: 60 dagen.",
        "prijs": "12.95",
        "voorraad": 150,
        "category_slug": "feminised",
        "afbeelding_url": "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=400",
        "kenmerken": {"thc": "20%", "cbd": "0.1%", "bloeitijd": "60 dagen", "opbrengst": "500g/m²"},
        "tags": ["bestseller", "indoor", "sativa-dominant"],
    },
    {
        "naam": "Northern Lights Feminised",
        "slug": "northern-lights-feminised",
        "korte_beschrijving": "Legendarische indica met diepe ontspanning.",
        "beschrijving": "Northern Lights is een pure indica die bekendstaat om zijn kalmerende en pijnstillende eigenschappen. Eenvoudig te kweken, zelfs voor beginners. THC: 18%, bloeitijd: 55 dagen.",
        "prijs": "14.50",
        "voorraad": 89,
        "category_slug": "feminised",
        "afbeelding_url": "https://images.unsplash.com/photo-1585664811087-47f65abbad64?w=400",
        "kenmerken": {"thc": "18%", "cbd": "0.2%", "bloeitijd": "55 dagen", "opbrengst": "450g/m²"},
        "tags": ["indica", "indoor", "relaxing"],
    },
    {
        "naam": "OG Kush Feminised",
        "slug": "og-kush-feminised",
        "korte_beschrijving": "Iconische West-Coast strain met aardse, pijnboom aroma.",
        "beschrijving": "OG Kush is de moeder van vele moderne hybriden. Complexe terpenenprofile met aardse, houtachtige en citrustonen. THC: 22%, bloeitijd: 63 dagen.",
        "prijs": "16.95",
        "voorraad": 62,
        "category_slug": "feminised",
        "afbeelding_url": "https://images.unsplash.com/photo-1603909223429-69bb7101d36a?w=400",
        "kenmerken": {"thc": "22%", "cbd": "0.1%", "bloeitijd": "63 dagen", "opbrengst": "400g/m²"},
        "tags": ["hybrid", "premium", "aroma"],
    },
    {
        "naam": "Blue Dream Feminised",
        "slug": "blue-dream-feminised",
        "korte_beschrijving": "Sativa-dominant met fruitige bosbessen tonen.",
        "beschrijving": "Blue Dream combineert de beste eigenschappen van Blueberry en Haze. Creatief en energiek effect met zoete bosbessen geur. THC: 21%, bloeitijd: 67 dagen.",
        "prijs": "15.50",
        "voorraad": 45,
        "category_slug": "feminised",
        "afbeelding_url": "https://images.unsplash.com/photo-1542281286-9e0a16bb7366?w=400",
        "kenmerken": {"thc": "21%", "cbd": "0.1%", "bloeitijd": "67 dagen", "opbrengst": "600g/m²"},
        "tags": ["sativa", "fruitig", "creatief"],
    },
    # Autoflower
    {
        "naam": "Critical Auto",
        "slug": "critical-auto",
        "korte_beschrijving": "Snelle autoflower met massieve opbrengst in 70 dagen.",
        "beschrijving": "Critical Auto is de bestseller onder autoflowers. Van zaad tot oogst in slechts 70 dagen. Ideaal voor outdoor kweken in België. THC: 14%, CBD: 0.5%.",
        "prijs": "11.95",
        "voorraad": 200,
        "category_slug": "autoflower",
        "afbeelding_url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
        "kenmerken": {"thc": "14%", "cbd": "0.5%", "bloeitijd": "70 dagen", "opbrengst": "400g/m²"},
        "tags": ["bestseller", "outdoor", "snel"],
    },
    {
        "naam": "Amnesia Haze Auto",
        "slug": "amnesia-haze-auto",
        "korte_beschrijving": "Haze-genot zonder lichtsturing nodig.",
        "beschrijving": "Amnesia Haze Auto brengt de klassieke Haze ervaring in autoflower formaat. Helder, cerebraal effect met citrus en aardse noten. THC: 16%, bloeitijd: 75 dagen.",
        "prijs": "13.95",
        "voorraad": 78,
        "category_slug": "autoflower",
        "afbeelding_url": "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?w=400",
        "kenmerken": {"thc": "16%", "cbd": "0.2%", "bloeitijd": "75 dagen", "opbrengst": "350g/m²"},
        "tags": ["sativa", "haze", "cerebraal"],
    },
    {
        "naam": "Gorilla Glue Auto",
        "slug": "gorilla-glue-auto",
        "korte_beschrijving": "Krachtige autoflower met extreem harsgehalte.",
        "beschrijving": "Gorilla Glue Auto produceert enorme hoeveelheden kristalachtige hars. Krachtig en langdurig effect. THC: 20%, bloeitijd: 77 dagen.",
        "prijs": "14.95",
        "voorraad": 55,
        "category_slug": "autoflower",
        "afbeelding_url": "https://images.unsplash.com/photo-1416339442236-8ceb164046f8?w=400",
        "kenmerken": {"thc": "20%", "cbd": "0.1%", "bloeitijd": "77 dagen", "opbrengst": "450g/m²"},
        "tags": ["hybrid", "hars", "krachtig"],
    },
    # CBD
    {
        "naam": "Charlotte's Angel CBD",
        "slug": "charlottes-angel-cbd",
        "korte_beschrijving": "High-CBD voor medicaal gebruik, nauwelijks psychoactief.",
        "beschrijving": "Charlotte's Angel is een premium CBD strain met zeer laag THC-gehalte. Ideaal voor dagelijks gebruik zonder psychoactieve effecten. THC: <0.2%, CBD: 15%.",
        "prijs": "18.95",
        "voorraad": 40,
        "category_slug": "cbd",
        "afbeelding_url": "https://images.unsplash.com/photo-1515377905703-c4788e51af15?w=400",
        "kenmerken": {"thc": "<0.2%", "cbd": "15%", "bloeitijd": "65 dagen", "opbrengst": "350g/m²"},
        "tags": ["medicaal", "wellness", "legal"],
    },
    {
        "naam": "Stress Killer Auto CBD",
        "slug": "stress-killer-auto-cbd",
        "korte_beschrijving": "Autoflower CBD met kalmerende eigenschappen.",
        "beschrijving": "Stress Killer Auto CBD combineert het gemak van autoflower met therapeutische CBD-waarden. Citrus aroma, kalmerend effect. THC: 0.8%, CBD: 11%.",
        "prijs": "13.50",
        "voorraad": 95,
        "category_slug": "cbd",
        "afbeelding_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400",
        "kenmerken": {"thc": "0.8%", "cbd": "11%", "bloeitijd": "70 dagen", "opbrengst": "300g/m²"},
        "tags": ["autoflower", "kalmerend", "citrus"],
    },
    {
        "naam": "Royal Medic CBD",
        "slug": "royal-medic-cbd",
        "korte_beschrijving": "Medische topkwaliteit met 12% CBD.",
        "beschrijving": "Royal Medic is speciaal gekweekt voor medicinaal gebruik. Hoge CBD-waarden gecombineerd met een rijke terpenenprofile voor het entourage-effect. THC: 1%, CBD: 12%.",
        "prijs": "21.95",
        "voorraad": 30,
        "category_slug": "cbd",
        "afbeelding_url": "https://images.unsplash.com/photo-1550159930-40066082a4fc?w=400",
        "kenmerken": {"thc": "1%", "cbd": "12%", "bloeitijd": "63 dagen", "opbrengst": "400g/m²"},
        "tags": ["premium", "medicaal", "entourage"],
    },
]


def seed():
    with Session(engine) as session:
        # Categorieën
        cat_map = {}
        for c in CATEGORIES:
            existing = session.execute(
                text("SELECT id FROM categories WHERE slug = :s"), {"s": c["slug"]}
            ).fetchone()
            if existing:
                cat_map[c["slug"]] = existing[0]
                print(f"  ↩ Categorie bestaat: {c['naam']}")
            else:
                cat = Category(**c)
                session.add(cat)
                session.flush()
                cat_map[c["slug"]] = cat.id
                print(f"  ✅ Categorie: {c['naam']}")

        # Producten
        for p in PRODUCTS:
            slug = p["slug"]
            existing = session.execute(
                text("SELECT id FROM products WHERE slug = :s"), {"s": slug}
            ).fetchone()
            if existing:
                print(f"  ↩ Product bestaat: {p['naam']}")
                continue
            cat_slug = p.pop("category_slug")
            product = Product(**p, category_id=cat_map[cat_slug])
            session.add(product)
            print(f"  ✅ Product: {p['naam']} (€{p['prijs']})")

        session.commit()
        print("\n🌱 Seed voltooid!")


if __name__ == "__main__":
    seed()
