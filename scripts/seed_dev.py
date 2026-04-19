"""Seed-data voor lokale ontwikkeling: categorieën en testproducten."""
import psycopg2
import os

DB = os.environ.get(
    "DB_URL",
    "postgresql://vorstersNV:dev-password-change-me@localhost:5432/vorstersNV",
).replace("postgresql+asyncpg://", "postgresql://").replace("postgresql+psycopg2://", "postgresql://")

conn = psycopg2.connect(DB)
cur = conn.cursor()

# Categorieën
cur.execute("""
    INSERT INTO categories (naam, slug, aangemaakt_op) VALUES
      ('Kleding', 'kleding', NOW()),
      ('Accessoires', 'accessoires', NOW()),
      ('Kantoor', 'kantoor', NOW())
    ON CONFLICT (slug) DO NOTHING
""")

# Producten
producten = [
    ("VorstersNV Hoodie",    "vorstersNV-hoodie",  "Premium hoodie in zwart",           59.99, 25, "kleding",      '["nieuw","populair"]'),
    ("VorstersNV T-shirt",   "vorstersNV-tshirt",  "Comfortabel katoenen t-shirt",       24.99, 50, "kleding",      '["populair"]'),
    ("Rugzak Pro",           "rugzak-pro",          "Stevige rugzak 30L met laptopvak",   89.99, 15, "accessoires",  '["nieuw"]'),
    ("Leren Riem",           "leren-riem",          "Handgemaakte leren riem",            34.99, 30, "accessoires",  '[]'),
    ("Notitieboek A5",       "notitieboek-a5",      "Hoogwaardig hardcover notitieboek",  14.99, 100, "kantoor",     '[]'),
    ("Pennenset Luxe",       "pennenset-luxe",      "Set van 5 premium balpennen",        19.99, 40, "kantoor",      '["populair"]'),
]

for naam, slug, beschr, prijs, voorraad, cat_slug, tags in producten:
    cur.execute("""
        INSERT INTO products
          (naam, slug, korte_beschrijving, prijs, voorraad, laag_voorraad_drempel, actief, category_id, aangemaakt_op, bijgewerkt_op, tags)
        SELECT %s, %s, %s, %s, %s, 5, true,
               (SELECT id FROM categories WHERE slug = %s),
               NOW(), NOW(), %s::json
        ON CONFLICT (slug) DO NOTHING
    """, (naam, slug, beschr, prijs, voorraad, cat_slug, tags))

conn.commit()
cur.close()
conn.close()
print("✅ Seed data geladen: 3 categorieën, 6 producten")
