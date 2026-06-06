---
generated: "2026-06-06"
source: "docs/converted/client-spec/wpc-ugyviteli-rendszer-specifikacio.md"
chapter: 9
title: "Rendeléskezelés és rendelési kommunikáció"
coverage:
  total: 58
  covered: 27
  partial: 17
  missing: 11
  deferred: 3
coverage_score: "80%"
---

# 9. Rendeléskezelés és rendelési kommunikáció — Lefedettség

**Coverage: 80%** — 27 covered, 17 partial, 11 missing, 3 deferred (58 total)

---

## 9.1 Rendelési csatornák

elsődleges rendelési csatorna: B2B webshop

> [!trace-deferred]
> ⏭️ `CS-9-001` Elsődleges rendelési csatorna: B2B webshop — *00-overview.md §2 "Nincs benne": B2B webshop M2+*

> [!trace-covered]
> ✅ `CS-9-002` B2B kontextus: nem B2C *(implicit)* — *00-overview.md §1, viszonteladók mint partnerek*

másodlagos rendelési csatorna: e-mail

> [!trace-covered]
> ✅ `CS-9-003` Másodlagos rendelési csatorna: e-mail — *01-order-intake.md §2.1*

> [!trace-partial]
> ⚠️ `CS-9-004` Prioritási sorrend webshop > email *(implicit)* — *06-data-model.md §2.4 Order.source* — a data model tartalmazza a csatornákat de nem definiál prioritást közöttük

az e-mailes rendelést a rendszer AI-alapú feldolgozással értelmezi

> [!trace-covered]
> ✅ `CS-9-005` AI-alapú email feldolgozás — *01-order-intake.md §2.1 + 02-order-processing.md §2*

---

## 9.2 E-mail feldolgozás

e-mail feldolgozás

> [!trace-covered]
> ✅ `CS-9-006` E-mail feldolgozás képesség — *01-order-intake.md §2, 02-order-processing.md §2*

rendelés felismerés

> [!trace-covered]
> ✅ `CS-9-007` Rendelés felismerés — *01-order-intake.md §2.1 "megrendeles" kategória*

AI-alapú adatkinyerés

> [!trace-covered]
> ✅ `CS-9-008` AI-alapú adatkinyerés — *02-order-processing.md §2.2 Értelmezési feladatok*

cikkszám felismerés

> [!trace-covered]
> ✅ `CS-9-009` Cikkszám felismerés — *02-order-processing.md §2.2 + §2.4 Cikkszám-struktúra*

mennyiség felismerés

> [!trace-covered]
> ✅ `CS-9-010` Mennyiség felismerés — *02-order-processing.md §2.2 (darabszám, folyóméter)*

határidő felismerés

> [!trace-covered]
> ✅ `CS-9-011` Határidő felismerés — *02-order-processing.md §2.2 → Order.requested_date*

---

## 9.3 Automatikus visszaigazolás

A rendszer automatikus visszaigazolást küldhet, de a visszaigazolásnak figyelembe kell vennie a készletet, a gyártási időt, a szállítási időt és a kapacitásokat.

> [!trace-partial]
> ⚠️ `CS-9-012` Automatikus visszaigazolás küldhet (opcionális) — *03-dijbekero.md §5* — díjbekérő email mint de facto visszaigazolás, de nincs önálló "rendelés megkaptuk" értesítés
> ⚠️ `CS-9-013` "küldhet" → döntési logika kell *(implicit)* — *US-OP-01* — a spec MINDIG manuálist ír elő (erősebb a kelleténél), nincs döntési szabályrendszer
> ⚠️ `CS-9-V001` Automatikus generálás+küldés folyamata *(verify-round)* — *03-dijbekero.md §5* — díjbekérő template létezik de önálló confirmation flow nincs

> [!trace-partial]
> ⚠️ `CS-9-014` Visszaigazolás figyelembe veszi készletet — *02-order-processing.md §3.3* — informatív, nem programmatikus: operátor látja de a díjbekérő nem faktorálja be
> ⚠️ `CS-9-019` Valós idejű készletinfo kell *(implicit)* — *06-data-model.md §2.8 StockLevel* — létezik de M1-ben csak informatív

> [!trace-missing]
> ⬜ `CS-9-015` Visszaigazolás figyelembe veszi **gyártási időt** — manufacturing_lead_days mező létezik de sehol nem használt
> ⬜ `CS-9-020` Gyártási idő figyelembevétele — duplikálja CS-9-015

> [!trace-missing]
> ⬜ `CS-9-016` Visszaigazolás figyelembe veszi **szállítási időt** — teljesen hiányzik: sem mező, sem számítás
> ⬜ `CS-9-021` Szállítási idő figyelembevétele — duplikálja CS-9-016

> [!trace-deferred]
> ⏭️ `CS-9-017` Visszaigazolás figyelembe veszi kapacitásokat — *00-overview.md §2: Telephelyi kapacitáskezelés M2+*
> ⏭️ `CS-9-022` Kapacitás figyelembevétele — M2+ scope

készlet esetén visszaigazolás

> [!trace-partial]
> ⚠️ `CS-9-018` Készlet esetén visszaigazolás — *02-order-processing.md §3.3* — stock status megjelenik (IN_STOCK/PARTIAL/OUT_OF_STOCK) de nem generál automatikus visszaigazolást

gyártási idő figyelembevétele

> [!trace-missing]
> ⬜ `CS-9-020` — fentebb jelölve

szállítási idő figyelembevétele

> [!trace-missing]
> ⬜ `CS-9-021` — fentebb jelölve

kapacitás figyelembevétele

> [!trace-deferred]
> ⏭️ `CS-9-022` — fentebb jelölve

nem teljesíthető határidő esetén alternatív időpont ajánlása

> [!trace-missing]
> ⬜ `CS-9-023` Alternatív időpont ajánlás — requested_date és confirmed_date mezők léteznek de NINCS számítási logika az alternatív dátumra
> ⬜ `CS-9-024` Számítási képesség alternatív időpontra *(implicit)* — nincs algoritmus
> ⬜ `CS-9-V002` Teljesíthetőségi gate (kért dátum vs legkorábbi lehetséges) *(verify-round)* — az operátor manuálisan dönt, nincs gépi feasibility check

nem teljesíthető határidő esetén figyelmeztetés küldése

> [!trace-missing]
> ⬜ `CS-9-025` Figyelmeztetés küldése nem teljesíthető határidőnél — nincs alerting mechanizmus, sem belső sem külső
> ⬜ `CS-9-V003` Figyelmeztetés címzettje *(verify-round)* — nincs warning → nincs címzett kérdés sem

szükség esetén ügyintézői jóváhagyás kérése

> [!trace-partial]
> ⚠️ `CS-9-026` Ügyintézői jóváhagyás — *02-order-processing.md §4.1, US-OP-01* — MINDIG kötelező (erősebb mint "szükség esetén")
> ⚠️ `CS-9-027` Döntési logika mikor kell jóváhagyás *(implicit)* — *US-OP-01* — válasz: "mindig" → nincs feltételes logika

> [!trace-covered]
> ✅ `CS-9-V004` Jóváhagyási UI/eszköz *(verify-round)* — *02-order-processing.md §3+§4 osztott képernyő, approve/reject gombok*

---

## 9.4 Kommunikáció határa

A rendszerben nem lesz általános kommunikációs modul. Nem cél általános CRM-kommunikáció vagy általános e-mail választervezet készítése. A kommunikáció kizárólag a rendelésfelvételhez és a rendelések teljesítéséhez kapcsolódik.

> [!trace-covered]
> ✅ `CS-9-028` EXCLUSION: nem lesz általános kommunikációs modul — *00-overview.md §1*
> ✅ `CS-9-029` EXCLUSION: nem cél CRM-kommunikáció — *nincs CRM feature a spec-ekben*
> ✅ `CS-9-030` EXCLUSION: nem cél e-mail választervezet — *03-dijbekero.md §5: fix template, nincs editor*
> ✅ `CS-9-031` Kommunikáció kizárólag rendeléshez — *minden email a spec-ben rendelés-életciklushoz kötött*
> ✅ `CS-9-032` Rendelésen kívüli kommunikáció kizárva *(implicit)* — *00-overview.md scope*
> ✅ `CS-9-V007` Kommunikációs scope zárt *(verify-round)* — *00-overview.md §1-2*

rendelésfelvétel

> [!trace-covered]
> ✅ `CS-9-033` Rendelésfelvétel kommunikáció — *01-order-intake.md §2 + 02-order-processing.md §2-4*

rendelés pontosítása

> [!trace-partial]
> ⚠️ `CS-9-034` Rendelés pontosítása kommunikáció — *02-order-processing.md §4.2 visszadobás auto-reply* — nincs strukturált pontosítás-kérés flow, csak rejection notice

rendelés visszaigazolása

> [!trace-partial]
> ⚠️ `CS-9-035` Rendelés visszaigazolása kommunikáció — *03-dijbekero.md §5* — díjbekérő = de facto visszaigazolás, de nincs önálló "megkaptuk" email

teljesítési határidő

> [!trace-missing]
> ⬜ `CS-9-036` Teljesítési határidő kommunikálása partner felé — confirmed_date létezik a modellben de nem kommunikálódik a partnernek

készlet, gyártás vagy beszerzés alapján történő teljesíthetőség

> [!trace-partial]
> ⚠️ `CS-9-037` Teljesíthetőség kommunikáció — *02-order-processing.md §3.3* — stock status belső, nem megy ki a partnernek
> ⚠️ `CS-9-038` Háromféle teljesítési útvonal *(implicit)* — *stock + manufacturing fedve, beszerzés NEM*

> [!trace-missing]
> ⬜ `CS-9-V006` **Beszerzés mint önálló teljesítési útvonal** *(verify-round)* — supplier_id mező létezik de nincs procurement flow

szállítás vagy átvétel egyeztetése

> [!trace-partial]
> ⚠️ `CS-9-039` Szállítás/átvétel egyeztetése — *02-order-processing.md §2.2* — mód rögzítve de nincs időpont-egyeztetés kommunikáció

> [!trace-covered]
> ✅ `CS-9-040` Két kézbesítési mód: szállítás, átvétel *(implicit)* — *06-data-model.md §2.4 Order.shipping_method: PICKUP/DELIVERY*

rendelés teljesítésével kapcsolatos státuszkommunikáció

> [!trace-partial]
> ⚠️ `CS-9-041` Státuszkommunikáció — *02-order-processing.md §6* — 10 státusz belső nyomkövetéssel, de NINCS kimenő értesítés a partnernek státuszváltozáskor

> [!trace-covered]
> ✅ `CS-9-042` Rendelési státusz nyomkövetés *(implicit)* — *02-order-processing.md §6: ÚJ→...→TELJESÍTVE*

díjbekérőhöz, fizetéshez és számlázási folyamat indításához kapcsolódó rendszerüzenetek

> [!trace-covered]
> ✅ `CS-9-043` Díjbekérő/fizetés/számlázás rendszerüzenetek — *03-dijbekero.md §2+§5, 05-payment-matching.md §2+§4*
> ✅ `CS-9-044` Díjbekérő/fizetés/számlázási folyamat *(implicit)* — *teljes pipeline: proforma→payment→invoice→email*

---

## 9.5 Ügyfélkezelés / CRM értelmezése

Az ügyfélkezelés ebben a rendszerben nem klasszikus értékesítési CRM. Az általános AI-funkciókra, például következő lépés javaslatára, általános e-mail választervezetre vagy proaktív értékesítési javaslatokra nincs szükség. Az ügyféladat-kezelés a rendelésfelvételhez, rendeléskezeléshez, teljesítéshez és partneri működéshez kapcsolódik.

> [!trace-covered]
> ✅ `CS-9-045` EXCLUSION: nem klasszikus CRM — *nincs CRM feature*
> ✅ `CS-9-046` EXCLUSION: nem kell AI következő lépés — *AI csak email-értelmezésre és termékmatchingre*
> ✅ `CS-9-047` EXCLUSION: nem kell e-mail választervezet — *fix template, nincs editor*
> ✅ `CS-9-048` EXCLUSION: nem kell proaktív sales — *nincs proaktív feature*
> ✅ `CS-9-050` Ügyféladat hatókörön kívülre nem terjed *(implicit)* — *Partner entity csak rendelés-releváns mezőkkel*

> [!trace-covered]
> ✅ `CS-9-V005` Strukturálatlan szöveg → strukturált rendelés *(verify-round)* — *02-order-processing.md §2 teljes AI pipeline*

> [!trace-partial]
> ⚠️ `CS-9-049` Ügyféladat-kezelés 4 terület — *06-data-model.md §2.1 Partner entity* — adatmodell lefedi de nem enumrálja expliciten a 4 területet
> ⚠️ `CS-9-V008` 4 terület egyenkénti kezelése, partneri különösen fontos *(verify-round)* — *Partner entity implicit lefedi de nincs explicit scope*
