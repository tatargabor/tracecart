---
generated: "2026-06-06"
source: "docs/converted/client-spec/terrafurn-ugyviteli-rendszer-specifikacio.md"
chapter: 9
title: "Rendeléskezelés és megrendelői kommunikáció"
coverage:
  total: 58
  covered: 27
  partial: 17
  missing: 11
  deferred: 3
coverage_score: "80%"
---

# 9. Rendeléskezelés és megrendelői kommunikáció — Lefedettség

**Coverage: 80%** — 27 covered, 17 partial, 11 missing, 3 deferred (58 total)

---

## 9.1 Rendelési csatornák

elsődleges rendelési csatorna: B2B portál

> [!trace-deferred]
> ⏭️ `CS-9-001` Elsődleges rendelési csatorna: B2B portál — *00-overview.md §2 "Nincs benne": B2B portál M2+*

> [!trace-covered]
> ✅ `CS-9-002` B2B kontextus: nem végfelhasználói *(implicit)* — *00-overview.md §1, belsőépítészek és irodaberendezők mint partnerek*

másodlagos rendelési csatorna: e-mail

> [!trace-covered]
> ✅ `CS-9-003` Másodlagos rendelési csatorna: e-mail — *01-order-intake.md §2.1*

> [!trace-partial]
> ⚠️ `CS-9-004` Prioritási sorrend portál > email *(implicit)* — *06-data-model.md §2.4 Order.source* — a data model tartalmazza a csatornákat de nem definiál prioritást közöttük

az e-mailes megrendelést a rendszer AI-alapú feldolgozással értelmezi

> [!trace-covered]
> ✅ `CS-9-005` AI-alapú email feldolgozás — *01-order-intake.md §2.1 + 02-order-processing.md §2*

---

## 9.2 E-mail feldolgozás

e-mail feldolgozás

> [!trace-covered]
> ✅ `CS-9-006` E-mail feldolgozás képesség — *01-order-intake.md §2, 02-order-processing.md §2*

megrendelés felismerés

> [!trace-covered]
> ✅ `CS-9-007` Megrendelés felismerés — *01-order-intake.md §2.1 "megrendeles" kategória*

AI-alapú adatkinyerés

> [!trace-covered]
> ✅ `CS-9-008` AI-alapú adatkinyerés — *02-order-processing.md §2.1*

termékkód felismerés

> [!trace-covered]
> ✅ `CS-9-009` Termékkód felismerés — *02-order-processing.md §2.2 "product_code extraction"*

darabszám felismerés

> [!trace-covered]
> ✅ `CS-9-010` Darabszám felismerés — *02-order-processing.md §2.2 "quantity extraction"*

határidő felismerés

> [!trace-covered]
> ✅ `CS-9-011` Határidő felismerés — *02-order-processing.md §2.2 "deadline extraction"*

---

## 9.3 Visszaigazolás és teljesíthetőség

a rendszer automatikus visszaigazolást küldhet a megrendelőnek

> [!trace-partial]
> ⚠️ `CS-9-012` Automatikus visszaigazolás küldhet (opcionális) — *03-confirmation.md §1* — a spec "küld"-öt ír, nem "küldhet" — optionalitás nem tükröződik

a visszaigazolásnak figyelembe kell vennie a faanyag-készletet, a CNC kapacitást, a felületkezelési időt és a szállítási ütemezést

> [!trace-covered]
> ✅ `CS-9-013` Visszaigazolás: faanyag-készlet figyelembevétele — *03-confirmation.md §2.1*

> [!trace-covered]
> ✅ `CS-9-014` Visszaigazolás: CNC kapacitás figyelembevétele — *03-confirmation.md §2.2*

> [!trace-partial]
> ⚠️ `CS-9-015` Visszaigazolás: felületkezelési idő figyelembevétele — *03-confirmation.md §2.3* — csak lakkozás van említve, pácolás és olajozás nincs

> [!trace-covered]
> ✅ `CS-9-016` Visszaigazolás: szállítási ütemezés figyelembevétele — *03-confirmation.md §2.4*

készleten lévő alapanyag esetén azonnali visszaigazolás adható

> [!trace-covered]
> ✅ `CS-9-017` Készlet alapú azonnali visszaigazolás — *03-confirmation.md §3*

nem teljesíthető határidő esetén alternatív időpont ajánlása, illetve figyelmeztetés küldése a megrendelőnek

> [!trace-covered]
> ✅ `CS-9-018` Alternatív időpont ajánlása — *03-confirmation.md §4.1*

> [!trace-partial]
> ⚠️ `CS-9-019` Figyelmeztetés küldése megrendelőnek — *03-confirmation.md §4.2* — spec csak belső figyelmeztetést említ, megrendelő felé irányuló nem specifikált

szükség esetén projektvezetői jóváhagyás kérése

> [!trace-covered]
> ✅ `CS-9-020` Projektvezetői jóváhagyás — *03-confirmation.md §5*

> [!trace-missing]
> ⬜ `CS-9-021` Döntési logika: mikor szükséges projektvezetői jóváhagyás *(implicit)* — Not verified

---

## 9.4 Kommunikáció hatóköre

a rendszerben NEM lesz általános kommunikációs modul

> [!trace-covered]
> ✅ `CS-9-022` Nincs általános kommunikációs modul — *00-overview.md §3 scope kizárások*

nem cél általános CRM-kommunikáció vagy általános e-mail sablonszerkesztés

> [!trace-covered]
> ✅ `CS-9-023` Nem cél: általános CRM-kommunikáció — *00-overview.md §3*

> [!trace-missing]
> ⬜ `CS-9-024` Nem cél: általános e-mail sablonszerkesztés — Not verified

a kommunikáció kizárólag a megrendelés-felvételhez és a megrendelések teljesítéséhez kapcsolódik

> [!trace-covered]
> ✅ `CS-9-025` Kommunikáció scope: megrendelés-felvétel + teljesítés — *04-communication.md §1*

megengedett kommunikációs témák: megrendelés-felvétel, megrendelés pontosítása, megrendelés visszaigazolása, gyártási határidő, teljesíthetőség, szállítás/átvétel egyeztetés, státuszkommunikáció, díjbekérő/előleg/számla

> [!trace-covered]
> ✅ `CS-9-026` Téma: megrendelés-felvétel — *04-communication.md §2.1*

> [!trace-covered]
> ✅ `CS-9-027` Téma: megrendelés pontosítása (anyag, szín, méret) — *04-communication.md §2.2*

> [!trace-covered]
> ✅ `CS-9-028` Téma: megrendelés visszaigazolása — *04-communication.md §2.3*

> [!trace-covered]
> ✅ `CS-9-029` Téma: gyártási határidő — *04-communication.md §2.4*

> [!trace-partial]
> ⚠️ `CS-9-030` Téma: teljesíthetőség (alapanyag/gyártás/felületkezelés) — *04-communication.md §2.5* — csak alapanyag és gyártás van külön kezelve, felületkezelés nincs

> [!trace-covered]
> ✅ `CS-9-031` Téma: szállítás/átvétel egyeztetés — *04-communication.md §2.6*

> [!trace-covered]
> ✅ `CS-9-032` Téma: státuszkommunikáció — *04-communication.md §2.7*

> [!trace-partial]
> ⚠️ `CS-9-033` Téma: díjbekérő/előleg/számla — *04-communication.md §2.8* — díjbekérő és számla van, előlegfizetés nincs specifikálva

---

## 9.5 Ügyfélkezelés

az ügyfélkezelés nem klasszikus értékesítési CRM

> [!trace-covered]
> ✅ `CS-9-034` Nem értékesítési CRM — *05-client-management.md §1*

nincs szükség AI-funkcióra: következő lépés javaslata, általános e-mail választervezet, illetve proaktív értékesítési javaslatok

> [!trace-covered]
> ✅ `CS-9-035` AI kizárás: következő lépés javaslata — *05-client-management.md §2 scope*

> [!trace-covered]
> ✅ `CS-9-036` AI kizárás: általános e-mail választervezet — *05-client-management.md §2 scope*

> [!trace-missing]
> ⬜ `CS-9-037` AI kizárás: proaktív értékesítési javaslatok — Not verified

ügyféladat-kezelés hatóköre: megrendelés-felvétel, gyártáskövetés, kiszállítás, illetve partneri kapcsolattartás

> [!trace-covered]
> ✅ `CS-9-038` Ügyfél scope: megrendelés-felvétel — *05-client-management.md §3*

> [!trace-covered]
> ✅ `CS-9-039` Ügyfél scope: gyártáskövetés — *05-client-management.md §3*

> [!trace-partial]
> ⚠️ `CS-9-040` Ügyfél scope: kiszállítás — *05-client-management.md §3* — spec "szállítás" szót használ, nem differenciál kiszállítás vs. átvétel

> [!trace-missing]
> ⬜ `CS-9-041` Ügyfél scope: partneri kapcsolattartás — Not verified
