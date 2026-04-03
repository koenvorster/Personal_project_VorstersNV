# Product Beschrijving Promptboek – VorstersNV

Kant-en-klare prompts voor het genereren van productbeschrijvingen per categorie.

---

## Elektronica

```yaml
template: elektronica
system_add: |
  Leg extra nadruk op technische specificaties en garantie.
  Noem compatibiliteit met andere apparaten indien relevant.
tone_of_voice: technisch
seo_focus: specificaties + merk + model
voorbeeld_output: |
  "De {product_naam} biedt {key_spec} zodat u {gebruiksvoordeel}.
  Met {technisch_kenmerk} en {garantie} jaar garantie bent u verzekerd van kwaliteit."
```

## Mode & Kleding

```yaml
template: mode
system_add: |
  Focus op gevoel, stijl en gelegenheid.
  Noem materiaal en verzorgingsinstructies.
  Gebruik inspirerende, aspirationele taal.
tone_of_voice: vriendelijk
seo_focus: kleur + maat + seizoen + stijl
voorbeeld_output: |
  "Deze {product_naam} in {kleur} is perfect voor {gelegenheid}.
  Gemaakt van {materiaal} voor optimaal comfort gedurende de hele dag."
```

## Wonen & Interieur

```yaml
template: wonen
system_add: |
  Beschrijf de sfeer en het gevoel dat het product creëert.
  Noem afmetingen en materialen duidelijk.
  Geef stijladvies en combinatiemogelijkheden.
tone_of_voice: luxe
seo_focus: stijl + materiaal + ruimte + kleur
voorbeeld_output: |
  "Geef uw {ruimte} een warme uitstraling met de {product_naam}.
  Dit {materiaal} meubel past perfect in een {stijl} interieur."
```

## Voeding & Gezondheid

```yaml
template: voeding
system_add: |
  Noem altijd ingrediënten en allergenen.
  Benadruk gezondheidsvoordelen zonder medische claims te maken.
  Vermeld herkomst indien relevant.
tone_of_voice: professioneel
seo_focus: ingrediënten + voordelen + certificering
voorbeeld_output: |
  "Geniet van de pure smaak van {product_naam}, gemaakt van {ingrediënten}.
  {Gezondheidsvoordeel} maakt dit product een waardevolle aanvulling op uw dagelijkse routine."
```

---

## Universele SEO-checklist

Voor elke productbeschrijving:
- [ ] Primair zoekwoord in de titel
- [ ] Primair zoekwoord in de eerste zin
- [ ] 2-3 secundaire zoekwoorden verwerkt
- [ ] Meta-titel max 60 tekens
- [ ] Meta-beschrijving max 160 tekens
- [ ] Alt-tekst voor afbeeldingen beschreven
- [ ] Interne links naar gerelateerde producten
- [ ] Schema.org Product markup

---

## Kwaliteitscontrole

Voordat een beschrijving live gaat:
1. Controleer op spelfouten (taalcheck)
2. Verifieer alle technische specificaties
3. Check SEO-score (minimaal 70/100)
4. Laat beoordelen door productmanager
5. Test in preview
