# Feladatkezelő modul — funkcionális specifikáció

## 1. Feladat alapadatok

### 1.1 Feladat létrehozása

Feladat létrehozásakor kötelező megadni a címet és a felelőst. A leírás és a határidő opcionális mezők.

### 1.2 Prioritás

A feladatok háromszintű priorizálást kapnak: sürgős, normál, alacsony. Az alapértelmezett prioritás: normál.

### 1.3 Címkék

A feladatokhoz szabadon rendelhető címkék tartoznak. A címkék színkódoltak, a színt a felhasználó választja ki.

## 2. Státuszkezelés

### 2.1 Állapotgép

A feladatok lehetséges állapotai: nyitott, folyamatban, kész. Státuszváltáskor a rendszer értesítést küld a feladat felelősének.

### 2.2 Alfeladatok

Feladatokhoz alfeladatok hozhatók létre. Az alfeladatok saját státusszal rendelkeznek. A szülő feladat automatikusan kész állapotba kerül, ha minden alfeladatja lezárult.

## 3. Szűrés és megjelenítés

### 3.1 Szűrők

A feladatlista szűrhető felelős, státusz, prioritás és címke alapján.

### 3.2 Exportálás

A szűrt feladatlista exportálható Excel formátumban.

## 4. Függőségek

### 4.1 Feladatok közötti kapcsolat

Feladatok között blokkoló függőség definiálható. Ha egy feladat blokkolva van, a rendszer vizuálisan jelzi.

## 5. Időkövetés

### 5.1 Időrögzítés

A feladatokhoz időbejegyzés rögzíthető: felhasználó, dátum, időtartam. Az időkövetés projektenként kapcsolható.

### 5.2 Riportozás

Havi bontású összesítő riport generálható az időbejegyzésekből.
