# LanguageCRM - Agile Planning Document

## 1. Product Goal (Obiectivul Produsului)
Dezvoltarea unei aplicații web CRM (Customer Relationship Management) care permite operatorilor și managerilor să adauge, să caute și să gestioneze clienți și comenzi folosind comenzi în limbaj natural (chat conversațional asistat de AI/NLP), reducând timpul de operare manuală în formulare clasice.

---

## 2. User Stories (Format: AS A <USER>, I CAN <DO>, SO THAT <VALUE>)

* **US-01 (Adăugare client prin text):**
  * **Story:** Ca operator vânzări, pot să scriu în chat „Adaugă clientul Ion Popescu cu telefonul 0722...”, astfel încât să înregistrez rapid un client fără să completez formulare.
  * **Criterii de acceptare (Definition of Done):** 
    - [ ] Mesajul este parsat și numele + telefonul sunt extrase.
    - [ ] Clientul este salvat în baza de date SQLite.

* **US-02 (Înregistrare comandă prin limbaj natural):**
  * **Story:** Ca operator vânzări, pot să scriu „Creează o comandă de 3 laptopuri pentru Ion Popescu”, astfel încât comanda să fie asociată automat clientului existent.
  * **Criterii de acceptare:**
    - [ ] Sistemul identifică clientul în baza de date.
    - [ ] Comanda apare în tabelul de comenzi cu statusul `Nouă`.

* **US-03 (Interogare istoric în limbaj natural):**
  * **Story:** Ca manager, pot să întreb sistemul „Ce comenzi active are Ion Popescu?”, astfel încât să văd instant stadiul livrărilor fără să aplic filtre manuale.
  * **Criterii de acceptare:**
    - [ ] Sistemul returnează lista comenzilor filtrate după client.

* **US-04 (Vizualizare tabelară clasică - Dashboard):**
  * **Story:** Ca utilizator, pot să văd în paralel un tabel cu toți clienții și comenzile, astfel încât să am o confirmare vizuală a modificărilor făcute prin chat.

* **[TODO - De completat cu echipa]: US-05 (...)**

---

## 3. Product Backlog (Ordonat după Prioritate)

| ID | Nume Item (PBI) | Tip (Funcțional / Tehnic) | Prioritate (PO) | Estimare Efort (Developers) | Sprint Alocat |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **PBI-1** | Setup arhitectură Docker + Python (`uv`) + TS + SQLite | Tehnic | Critică (1) | *De estimat (ex: S / M)* | Sprint 1 |
| **PBI-2** | Definire modele SQLAlchemy (`Client`, `Order`) | Tehnic | Mare (2) | *De estimat* | Sprint 1 |
| **PBI-3** | Interfață Chat în TypeScript (trimitere/primire text) | Funcțional | Mare (3) | *De estimat* | Sprint 1 |
| **PBI-4** | Procesare limbaj natural pentru creare client (US-01) | Funcțional | Mare (4) | *De estimat* | Sprint 2 |
| **PBI-5** | Procesare limbaj natural pentru creare comandă (US-02)| Funcțional | Medie (5) | *De estimat* | Sprint 2 |
| **PBI-6** | Interogare comenzi prin chat (US-03) | Funcțional | Medie (6) | *De estimat* | Sprint 3 |