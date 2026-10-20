# Requirements Document - LanguageCRM

**Status:** În curs de revizuire / Schiță  
**Product Owner:** Pricop Alexandru 
**Echipa de Dezvoltare:** Baroană Alexandru-Cătălin, Jitescu Silviu-Cristian, Taraleșca Ovidiu, Coman Tudor

---

## 1. Descrierea problemei abordate
În mod tradițional, gestionarea relației cu clienții (CRM) și plasarea comenzilor presupun un efort manual intens din partea operatorilor umani ai unei companii, care trebuie să citească mesaje, să extragă date, să verifice stocurile și să introducă informațiile în sistem. Acest flux este lent, repetitiv și predispus la erori umane.

**Soluția propusă (LanguageCRM cu Agent Conversațional Autonom):** O platformă inteligentă centrată pe un **chatbot autonom în limbaj natural**. Chatbotul preia dialogul direct cu clienții finali, înțelege intențiile acestora (plasare de comenzi, interogare stocuri, detalii despre produse), verifică automat disponibilitatea în baza de date SQLite, înregistrează comenzile și actualizează stocurile fără a necesita intervenția manuală a operatorilor companiei.

---

## 2. Descrierea utilizatorilor și a principalelor categorii
Sistemul deservește trei categorii principale de utilizatori (inclusiv actori autonomi):

1. **Clientul Final (Customer):**
   * **Rol:** Interacționează prin intermediul chat-ului cu sistemul pentru a achiziționa produse sau a cere informații.
   * **Nevoi:** Comunicare naturală, rapidă, fără formulare stufoase și confirmare instantanee a comenzilor.
2. **Chatbotul Autonom (AI Agent / System):**
   * **Rol:** Analizează mesajele clienților, extrage entitățile (nume produs, cantitate, date client), interoghează stocul și operează automat baza de date.
3. **Managerul / Administratorul (Manager):**
   * **Rol:** Supraveghează sistemul global, vizualizează rapoartele din dashboard, administrează stocurile și intervine doar în cazul alertelor sau excepțiilor.

---

## 3. Product Goal (Obiectivul Produsului)
> „Dezvoltarea unui sistem CRM autonom bazat pe limbaj natural, în care un chatbot preia interacțiunea directă cu clienții și automatizează fluxul de plasare a comenzilor și verificare a stocurilor, reducând intervenția umană din partea companiei la zero pentru fluxul standard.”

---

## 4. Cerințe Funcționale și Nefuncționale

### 4.1. Cerințe Funcționale (Functional Requirements)
* **CF-01 (Chat Conversațional):** Sistemul trebuie să ofere o interfață web de tip chat prin care utilizatorii pot comunica în limbaj natural.
* **CF-02 (Extragerea entităților):** Backend-ul trebuie să proceseze textul primit și să identifice automat datele clientului și produsele dorite.
* **CF-03 (Gestionarea automată a clienților):** Sistemul înregistrează sau actualizează automat clienții noi în baza de date SQLite.
* **CF-04 (Verificarea automată a stocului):** Sistemul interoghează stocul disponibil înainte de validarea oricărei comenzi cerute prin chat.
* **CF-05 (Plasarea automată a comenzii):** Dacă stocul este suficient, comanda este plasată automat de chatbot, iar stocul se actualizează (scade).
* **CF-06 (Alertare stoc epuizat):** Managerul este notificat vizual în dashboard dacă un produs atinge un nivel critic sau zero în stoc.
* **CF-07 (Dashboard de vizualizare):** O pagină secundară afișează tabelele clasice cu clienți, comenzi și stocuri pentru monitorizarea generală.
* **CF-08 (Rapoarte stoc):** Managerul poate vizualiza rapoarte legate de datele relevante din baza de date a produselor, la fel si date sau metrici despre utilizatori.
* **CF-09 (Vizualizare produse):** Utilizatorul poate vizualiza produsele disponibile, la fel si vizibilitatea lor in functie de stoc.

### 4.2. Cerințe Nefuncționale (Non-Functional Requirements)
* **CNF-01 (Performanță):** Timpul de răspuns al chatbotului la o comandă text nu trebuie să depășească 2 secunde în mediul local Docker.
* **CNF-02 (Portabilitate):** Aplicația trebuie să ruleze identic pe orice sistem de operare folosind containere Docker și `docker-compose`.
* **CNF-03 (Securitate):** Datele sensibile și cheile API nu vor fi niciodată expuse sau urcate în repository-ul public (protejate prin `.gitignore`).
* **CNF-04 (Lizibilitate):** Aplicația trebuie să fie usor de vizualizat pentru utilizatori.
* **CNF-05 (Gestionarea):** Aplicatia trebuie sa poata gestiona comenzi concurente.
---

## 5. Use Case Diagram (Reprezentare UML / Mermaid)

Diagrama de mai jos ilustrează interacțiunile dintre actorii sistemului și principalele funcționalități:

```mermaid
graph TD
    Client[Client Final] -->|Trimite mesaj text| ChatBot[Chatbot Autonom]
    Client -->|Cere detalii comandă| ChatBot
    
    ChatBot -->|Extrage date client| DB[(Bază de date SQLite)]
    ChatBot -->|Verifică stoc produs| DB
    ChatBot -->|Plasează comandă și actualizează stoc| DB

    Manager[Manager Companie] -->|Monitorizează dashboard-ul| Dashboard[Interfață Web / Dashboard]
    Manager -->|Gestionează stocul și produsele| DB
```

---

## 6. Product Backlog

User stories, prioritățile, estimările și criteriile de acceptare sunt menținute în [`docs/agile_planning.md`](agile_planning.md), ca sursă unică de adevăr pentru backlog (US-01 … US-17).
