# TerraFurn gyártástervezési modul — funkcionális specifikáció

## 1. Anyaggazdálkodás

### 1.1 Anyagszükséglet-tervezés

A megrendelés visszaigazolását követően a rendszer automatikusan elindítja az anyagszükséglet-tervezési folyamatot. A tervezés figyelembe veszi az aktuális raktárkészletet, a nyitott beszerzési rendeléseket és a minimális rendelési mennyiségeket.

### 1.2 Automatikus beszerzés

Amennyiben a szükséges alapanyag nem áll rendelkezésre a raktárban, a rendszer beszerzési javaslatot készít és továbbítja a beszerzési modulnak.

### 1.3 Beszállítói követelmények

Tölgy és bükk alapanyagok beszerzése kizárólag FSC-tanúsítvánnyal rendelkező beszállítóktól történhet.

## 2. Gyártásütemezés

### 2.1 Kapacitástervezés

A CNC gépek kapacitásának ütemezése napi bontásban történik. A felületkezelési kapacitás tervezése heti szinten valósul meg. Az ütemező algoritmus figyelembe veszi a futó megrendeléseket és az új megrendelések prioritását.

### 2.2 Kézi átütemezés

Sürgős megrendelés esetén a projektvezető jogosult kézi átütemezésre. Minden kézi beavatkozás naplózásra kerül az auditálhatóság érdekében.

### 2.3 Scope kizárások

Az automatikus ütemezés-optimalizálás nem része az M1 kiadásnak.

## 3. Minőségellenőrzés

### 3.1 Kimenő minőségellenőrzés

A késztermékeket kiszállítás előtt minőségellenőrzésnek kell alávetni. A minőségellenőrzésről jegyzőkönyv készül. Hibás termék esetén a rendszer értesítést küld a projektvezetőnek.

## 4. Szállítás

### 4.1 Szállítás egyeztetése

A kiszállítás időpontját egyeztetni kell a megrendelővel. A rendszer szállítólevelet állít elő a kiszállításhoz.
