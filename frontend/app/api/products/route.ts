import { NextResponse } from 'next/server'

const FASTAPI_URL = process.env.FASTAPI_URL ?? 'http://localhost:8000'

const MOCK_PRODUCTS = [
  { id: 1, naam: 'Premium Hoodie', slug: 'premium-hoodie', korte_beschrijving: 'Comfortabele hoodie met luxe afwerking en warme voering.', beschrijving: 'Een prachtige premium hoodie gemaakt van 100% biologisch katoen. Ideaal voor koele avonden en casualwear.', prijs: 59.99, voorraad: 25, actief: true, afbeelding_url: null, category_id: 1, category_naam: 'Kleding', kenmerken: null, tags: ['nieuw'], seo_titel: null, seo_omschrijving: null },
  { id: 2, naam: 'Klassiek T-Shirt', slug: 'klassiek-t-shirt', korte_beschrijving: 'Tijdloos T-shirt in hoogwaardig katoen.', beschrijving: 'Het klassieke VorstersNV T-shirt — stevig, comfortabel en duurzaam. Verkrijgbaar in meerdere kleuren.', prijs: 29.99, voorraad: 50, actief: true, afbeelding_url: null, category_id: 1, category_naam: 'Kleding', kenmerken: null, tags: null, seo_titel: null, seo_omschrijving: null },
  { id: 3, naam: 'Canvas Rugzak', slug: 'canvas-rugzak', korte_beschrijving: 'Duurzame canvas rugzak met laptopvak.', beschrijving: 'Stijlvolle en functionele canvas rugzak met verstevigde schouderbanden en een apart laptopvak tot 15 inch.', prijs: 89.99, voorraad: 12, actief: true, afbeelding_url: null, category_id: 2, category_naam: 'Accessoires', kenmerken: null, tags: ['populair'], seo_titel: null, seo_omschrijving: null },
  { id: 4, naam: 'Leren Riem', slug: 'leren-riem', korte_beschrijving: 'Handgemaakte leren riem met bronzen gesp.', beschrijving: 'Vakkundig handgemaakte riem van vol-nerf rundleder. Tijdloos en duurzaam — een aankoop voor het leven.', prijs: 49.99, voorraad: 8, actief: true, afbeelding_url: null, category_id: 2, category_naam: 'Accessoires', kenmerken: null, tags: null, seo_titel: null, seo_omschrijving: null },
  { id: 5, naam: 'Wollen Muts', slug: 'wollen-muts', korte_beschrijving: 'Extra warme muts van merinowol.', beschrijving: 'Zachte muts gestrickt van 100% merinowol. Licht, warm en krasvrij op de huid.', prijs: 24.99, voorraad: 3, actief: true, afbeelding_url: null, category_id: 1, category_naam: 'Kleding', kenmerken: null, tags: null, seo_titel: null, seo_omschrijving: null },
  { id: 6, naam: 'Notitieblok A5', slug: 'notitieblok-a5', korte_beschrijving: 'Premium notitieboek met harde kaft.', beschrijving: 'Gerecycled papier, harde linnen kaft en een lintbladwijzer. Perfect voor dagelijkse notities en ideeën.', prijs: 14.99, voorraad: 0, actief: true, afbeelding_url: null, category_id: 3, category_naam: 'Kantoor', kenmerken: null, tags: ['uitverkocht'], seo_titel: null, seo_omschrijving: null },
]

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const params = new URLSearchParams()
  for (const [k, v] of searchParams.entries()) params.set(k, v)

  try {
    const res = await fetch(`${FASTAPI_URL}/api/products?${params}`, {
      next: { revalidate: 60 },
    })
    if (!res.ok) return NextResponse.json(buildMockList(searchParams))
    return NextResponse.json(await res.json())
  } catch {
    return NextResponse.json(buildMockList(searchParams))
  }
}

function buildMockList(params: URLSearchParams) {
  const zoek = params.get('zoek')?.toLowerCase()
  const cat = params.get('categorie_slug')
  let items = MOCK_PRODUCTS
  if (zoek) items = items.filter(p => p.naam.toLowerCase().includes(zoek) || p.korte_beschrijving.toLowerCase().includes(zoek))
  if (cat) items = items.filter(p => p.category_naam?.toLowerCase() === cat)
  return { items, totaal: items.length, pagina: 1, per_pagina: 20 }
}
