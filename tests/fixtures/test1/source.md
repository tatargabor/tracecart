# TerraFurn gyártástervezés — egyeztetés jegyzőkönyve

## 1. Anyaggazdálkodás

Az anyagszükséglet-tervezés a megrendelés visszaigazolása után automatikusan elindul. A rendszernek figyelembe kell vennie a raktárkészletet, a nyitott beszerzési rendeléseket és a minimális rendelési mennyiségeket. Ha a szükséges alapanyag nincs raktáron, a rendszer automatikusan beszerzési javaslatot generál.

A tölgy és bükk alapanyagok esetén kizárólag FSC-tanúsítvánnyal rendelkező beszállítóktól rendelhető. Ez a követelmény nem vonatkozik a kiegészítő anyagokra, például csavarokra vagy ragasztóra.

## 2. Gyártásütemezés

A CNC gépek kapacitását napi szinten kell ütemezni, illetve a felületkezelési kapacitást heti szinten kell tervezni. Az ütemezés során a rendszernek figyelembe kell vennie az éppen futó megrendeléseket, az új megrendelések prioritását és a gépkarbantartási terveket.

Sürgős megrendelés esetén a projektvezetőnek lehetősége van kézi átütemezésre, de az automatikus ütemezés felülbírálata naplózásra kerül. A rendszer nem végez automatikus optimalizálást a meglévő ütemezésen — ez a funkció nem része az M1 scope-nak.

## 3. Minőségellenőrzés

A késztermékek kiszállítás előtt minőségellenőrzésen esnek át. A minőségellenőrzési jegyzőkönyvet a rendszerben kell rögzíteni. Hibás termék esetén a rendszer automatikus értesítést küldhet a projektvezetőnek.

## 4. Szállítás

A szállítási időablak egyeztetése a megrendelővel kötelező. A rendszer szállítólevelet generál a kiszállításhoz.
