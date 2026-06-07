# Belső projektmenedzsment — kickoff egyeztetés

## 1. Feladatkezelés

A feladatokat projekt szinten kell kezelni. Minden feladatnak legyen címe, leírása, felelőse és határideje. A feladatokat lehessen priorizálni: sürgős, normál és alacsony szinteken.

A feladatok státusza: nyitott, folyamatban, elakadt, kész. Státuszváltáskor a rendszer értesítse az érintetteket. Ha egy feladat elakadt státuszba kerül, a projektvezető kapjon külön értesítést.

Alfeladatok kellenek: egy feladat alatt legyen lehetőség részfeladatok létrehozására. Az alfeladatok saját státusszal rendelkeznek, de a szülő feladat automatikusan lezárul ha minden alfeladat kész.

## 2. Jogosultságok

Három szerepkör: admin, projektvezető, csapattag. Az admin mindent lát és módosíthat. A projektvezető a saját projektjeit kezeli. A csapattag csak a hozzárendelt feladatait látja és módosíthatja.

A jogosultságkezelés RBAC alapú legyen. Egyedi jogosultságokat nem tervezünk az M1-ben — ez a funkció nem része az első kiadásnak.

## 3. Értesítések

Az értesítések e-mailben és alkalmazáson belül is megjelenjenek. A felhasználó beállíthassa, milyen értesítéseket kap. Legalább a következő eseményekre: feladat hozzárendelés, határidő közeledik, státuszváltás, megjegyzés.

A határidő-figyelmeztetés 24 órával a lejárat előtt automatikusan kiküldendő.
