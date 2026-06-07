# Jogosultságkezelő modul — funkcionális specifikáció

## 1. Szerepkörök

### 1.1 Szerepkör-hierarchia

A rendszer három beépített szerepkört támogat: admin, projektvezető, csapattag.

### 1.2 Admin

Az admin felhasználó teljes hozzáféréssel rendelkezik minden projekthez és beállításhoz.

### 1.3 Projektvezető

A projektvezető a saját projektjeit kezeli. Jogosult vendég felhasználókat meghívni a projektekbe.

### 1.4 Csapattag

A csapattag a hozzá rendelt feladatokat látja és módosítja.

### 1.5 Vendég

Vendég felhasználók olvasási hozzáféréssel rendelkeznek. Módosítási jogosultságuk nincs.

## 2. Hozzáférés-szabályozás

### 2.1 RBAC modell

A jogosultságkezelés szerepkör-alapú hozzáférés-szabályozáson (RBAC) alapul.

### 2.2 Scope kizárás

Egyedi, felhasználó-szintű jogosultságok konfigurálása nem része az M1 kiadásnak.

## 3. Értesítések

### 3.1 Értesítési csatornák

Az értesítések e-mailben és alkalmazáson belül jelennek meg.

### 3.2 Értesítési beállítások

A felhasználó kiválaszthatja, mely eseménytípusokra kap értesítést.

### 3.3 Automatikus figyelmeztetések

A határidő lejárata előtt 24 órával a rendszer automatikus figyelmeztetést küld.
