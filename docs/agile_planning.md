# LanguageCRM - Agile Planning Document

**Status:** Activ  
**Product Owner:** Pricop Alexandru  
**Echipa de dezvoltare:** Baroană Alexandru-Cătălin, Jitescu Silviu-Cristian, Taraleșca Ovidiu, Coman Tudor

---

## 1. Product Goal (Obiectivul Produsului)

> „Dezvoltarea unui sistem CRM autonom bazat pe limbaj natural, în care un chatbot preia interacțiunea directă cu clienții și automatizează fluxul de plasare a comenzilor și verificare a stocurilor, reducând intervenția umană din partea companiei la zero pentru fluxul standard.”

---

## 2. Actori

1. **Clientul final (Customer):** interacționează prin chat pentru a cumpăra produse sau a cere informații.
2. **Chatbotul autonom (AI Agent / System):** analizează mesajele, extrage entități, interoghează stocul și operează baza de date.
3. **Managerul / Administratorul (Manager):** supraveghează dashboardul, administrează stocurile și intervine în cazul alertelor sau excepțiilor.

---

## 3. Scala de estimare

Estimările folosesc scala Fibonacci: **1, 2, 3, 5, 8, 13** story points.

- **US-01 = 5 story points** și **US-02 = 8 story points**, stabilite prin Planning Poker.
- Celelalte povești sunt estimate relativ la acestea, în funcție de complexitate, incertitudine și dependențe.
- **Total backlog: 91 story points.**

Prioritățile sunt exprimate prin etichetele `p/high`, `p/medium` și `p/low`:

| Etichetă | Nivel | Semnificație |
| :--- | :--- | :--- |
| `p/high` | Mare | Blochează fluxul principal sau MVP-ul. |
| `p/medium` | Medie | Necesar pentru un flux complet, dar poate urma după MVP. |
| `p/low` | Mică | Îmbunătățire sau funcționalitate opțională. |

---

## 4. Product Backlog

| ID | PBI | User story | Modul | Prioritate | SP |
| :--- | :--- | :--- | :--- | :--- | ---: |
| US-01 | PBI-01 | Chat web cu mesaje libere în limbaj natural | Chatbot & Limbaj Natural | Mare | 5 |
| US-02 | PBI-02 | Parsarea mesajului și detectarea intenției | Chatbot & Limbaj Natural | Mare | 8 |
| US-03 | PBI-03 | Răspuns instantaneu în fereastra de chat | Chatbot & Limbaj Natural | Mare | 3 |
| US-04 | PBI-04 | Clarificări pentru mesaje ambigue sau incomplete | Chatbot & Limbaj Natural | Medie | 5 |
| US-05 | PBI-05 | Extragerea datelor de contact și crearea clientului | Clienți & CRM | Mare | 8 |
| US-06 | PBI-06 | Detectarea clienților existenți pentru evitarea duplicatelor | Clienți & CRM | Medie | 3 |
| US-07 | PBI-07 | Tabel cu clienții în dashboard | Clienți & CRM | Medie | 3 |
| US-08 | PBI-08 | Adăugarea produselor și a stocului inițial | Stocuri & Inventar | Mare | 5 |
| US-09 | PBI-09 | Interogarea automată a stocului la cerere | Stocuri & Inventar | Mare | 3 |
| US-10 | PBI-10 | Vizualizarea nivelului curent al stocurilor | Stocuri & Inventar | Medie | 3 |
| US-11 | PBI-11 | Plasarea unei comenzi complete prin chat | Automatizarea Comenzilor | Mare | 13 |
| US-12 | PBI-12 | Validarea comenzii și actualizarea atomică a stocului | Automatizarea Comenzilor | Mare | 8 |
| US-13 | PBI-13 | Refuz sau alternativă la stoc insuficient | Automatizarea Comenzilor | Medie | 5 |
| US-14 | PBI-14 | Istoricul comenzilor în dashboard | Automatizarea Comenzilor | Medie | 3 |
| US-15 | PBI-15 | Istoricul comenzilor clientului și recomandări | Automatizarea Comenzilor | Mică | 5 |
| US-16 | PBI-16 | Decizia de utilizare a tool-urilor de personalizare | Automatizarea Comenzilor | Mică | 8 |
| US-17 | PBI-17 | Alertă vizuală pentru stoc critic | Alerte & Administrare Excepții | Medie | 3 |
| US-18 | PBI-18 | Localizare/internaționalizare | Chatbot & Limbaj Natural | Medie | 3 |
| | | **Total** | | | **94** |

---

## 5. User Stories detaliate

### Modulul 1: Chatbot & Limbaj Natural

#### US-01 — Chat web cu mesaje libere în limbaj natural

**Modul:** Chatbot & Limbaj Natural  
**Prioritate:** Mare (`p/high`)  
**Estimare:** 5 story points

**User story:** Ca client, pot să scriu un mesaj liber în fereastra de chat, astfel încât să pot comunica cu compania fără a naviga prin meniuri complexe.

**Criterii de acceptare:**

- [ ] Există o pagină web cu câmp de text și buton de trimitere.
- [ ] Mesajul introdus este trimis către backend și afișat în fereastra de chat.
- [ ] Mesajele goale nu pot fi trimise.
- [ ] Interfața este utilizabilă pe desktop și pe mobil.

**Referințe:** CF-01

#### US-02 — Parsarea mesajului și detectarea intenției

**Modul:** Chatbot & Limbaj Natural  
**Prioritate:** Mare (`p/high`)  
**Estimare:** 8 story points

**User story:** Ca sistem (chatbot), pot parsa mesajul text primit de la client pentru a detecta intenția (comandă, interogare stoc), astfel încât să pot rula logica de business corespunzătoare.

**Criterii de acceptare:**

- [ ] Backendul clasifică textul într-o intenție: comandă, interogare stoc, salut sau necunoscut.
- [ ] Funcționează pentru formulări românești cu și fără diacritice.
- [ ] Textul ambiguu produce intenția „necunoscut” și nu modifică baza de date.
- [ ] Răspunsul include entitățile detectate: produs, cantitate și client.
- [ ] Timpul de răspuns este sub 2 secunde în mediul local Docker.

**Referințe:** CF-02, CNF-01

#### US-03 — Răspuns instantaneu în fereastra de chat

**Modul:** Chatbot & Limbaj Natural  
**Prioritate:** Mare (`p/high`)  
**Estimare:** 3 story points

**User story:** Ca client, pot să primesc un răspuns instantaneu din partea chatbotului în cadrul aceleiași ferestre de chat, astfel încât să am confirmarea interacțiunii în timp real.

**Criterii de acceptare:**

- [ ] Răspunsul apare în aceeași fereastră, fără reîncărcarea paginii.
- [ ] Un indicator de încărcare este afișat cât timp se așteaptă răspunsul.
- [ ] Mesajele și răspunsurile păstrează ordinea cronologică.
- [ ] Erorile de rețea sunt afișate clar utilizatorului.

**Referințe:** CF-01, CNF-01

#### US-04 — Clarificări pentru mesaje ambigue sau incomplete

**Modul:** Chatbot & Limbaj Natural  
**Prioritate:** Medie (`p/medium`)  
**Estimare:** 5 story points

**User story:** Ca client, pot să primesc o clarificare de la chatbot dacă mesajul meu este ambiguu sau lipsesc detalii (de exemplu, cantitatea), astfel încât comanda să poată fi corect înțeleasă.

**Criterii de acceptare:**

- [ ] Dacă lipsește cantitatea sau produsul, chatbotul cere clarificare înainte de a crea comanda.
- [ ] Contextul conversației este păstrat pe durata clarificării.
- [ ] După primirea datelor lipsă, fluxul continuă automat.
- [ ] Nu se creează comenzi parțiale în baza de date.

**Referințe:** CF-02

#### US-18 — Localizare/internaționalizare

**Modul:** Chatbot & Limbaj Natural  
**Prioritate:** Medie (`p/medium`)  
**Estimare:** 3 story points

**User story:** Ca sistem, pot să recunosc, atât mesajele în română, cât și pe cele în engleză.

**Criterii de acceptare:**

- [ ] Mesajul trimis este procesat în ambele limbi.

**Referințe:** CF-10

### Modulul 2: Clienți & CRM

#### US-05 — Extragerea datelor de contact și crearea clientului

**Modul:** Clienți & CRM  
**Prioritate:** Mare (`p/high`)  
**Estimare:** 8 story points

**User story:** Ca sistem (chatbot), pot extrage automat datele de contact (nume, telefon, email) dintr-o conversație, astfel încât să creez un profil nou de client în baza de date SQLite fără intervenție umană.

**Criterii de acceptare:**

- [ ] Se extrag numele, telefonul și emailul din conversație.
- [ ] Clientul este salvat în baza de date SQLite.
- [ ] Numele și telefonul sunt obligatorii; datele invalide produc o cerere de clarificare.
- [ ] Clientul creat apare în dashboard.

**Referințe:** CF-02, CF-03

#### US-06 — Detectarea clienților existenți pentru evitarea duplicatelor

**Modul:** Clienți & CRM  
**Prioritate:** Medie (`p/medium`)  
**Estimare:** 3 story points

**User story:** Ca sistem, pot verifica dacă un client există deja în baza de date după numărul de telefon sau nume, astfel încât să nu duplic înregistrările.

**Criterii de acceptare:**

- [ ] Căutarea se face după telefon normalizat și după nume.
- [ ] Un client existent este refolosit, fără duplicat.
- [ ] Un client inexistent este creat.
- [ ] Formatarea diferită a telefonului (07xx față de +407xx) este recunoscută.

**Referințe:** CF-03

#### US-07 — Tabel cu clienții în dashboard

**Modul:** Clienți & CRM  
**Prioritate:** Medie (`p/medium`)  
**Estimare:** 3 story points

**User story:** Ca manager, pot vizualiza lista completă a clienților înregistrați automat de chatbot într-un tabel dedicat pe dashboard, astfel încât să pot analiza baza de date a companiei.

**Criterii de acceptare:**

- [ ] Tabelul afișează id, nume, telefon și email.
- [ ] Datele provin din SQLite și se actualizează la reîncărcare.
- [ ] Există căutare după nume.
- [ ] Se afișează un mesaj când lista este goală.

**Referințe:** CF-07

### Modulul 3: Stocuri & Inventar

#### US-08 — Adăugarea produselor și a stocului inițial

**Modul:** Stocuri & Inventar  
**Prioritate:** Mare (`p/high`)  
**Estimare:** 5 story points

**User story:** Ca manager, pot adăuga produse noi și cantități inițiale în stoc prin intermediul interfeței backend/bazei de date, astfel încât chatbotul să aibă de unde scădea cantitatea produselor.

**Criterii de acceptare:**

- [ ] Există formular sau endpoint pentru produs nou: nume, preț și cantitate inițială.
- [ ] Numele este unic, iar cantitatea este mai mare sau egală cu 0.
- [ ] Produsul apare imediat în lista de stocuri.
- [ ] Cantitatea inițială este persistată în baza de date.

**Referințe:** CF-07, CF-08

#### US-09 — Interogarea automată a stocului la cerere

**Modul:** Stocuri & Inventar  
**Prioritate:** Mare (`p/high`)  
**Estimare:** 3 story points

**User story:** Ca sistem, pot interoga automat stocul unui produs în momentul în care un client solicită o cantitate prin chat, astfel încât să pot lua o decizie de validare.

**Criterii de acceptare:**

- [ ] Întrebarea „câte X aveți?” returnează cantitatea curentă.
- [ ] Răspunsul include numele produsului și disponibilitatea.
- [ ] Un produs inexistent produce un mesaj clar.
- [ ] Interogarea nu modifică stocul.

**Referințe:** CF-04

#### US-10 — Vizualizarea nivelului curent al stocurilor

**Modul:** Stocuri & Inventar  
**Prioritate:** Medie (`p/medium`)  
**Estimare:** 3 story points

**User story:** Ca manager, pot vizualiza nivelul curent al stocurilor în timp real pe dashboard, astfel încât să știu când este nevoie de reaprovizionare.

**Criterii de acceptare:**

- [ ] Tabelul afișează produs, cantitate și prag critic.
- [ ] Datele reflectă starea din baza de date.
- [ ] Stocul zero este evidențiat vizual.

**Referințe:** CF-07, CF-08

### Modulul 4: Automatizarea Comenzilor

#### US-11 — Plasarea unei comenzi complete prin chat

**Modul:** Automatizarea Comenzilor  
**Prioritate:** Mare (`p/high`)  
**Estimare:** 13 story points

**User story:** Ca client, pot plasa o comandă completă doar tastând textul dorit în chat, astfel încât procesul de cumpărare să fie complet autonom și automatizat.

**Criterii de acceptare:**

- [ ] Un mesaj de comandă creează clientul dacă lipsește, verifică stocul și creează comanda.
- [ ] Comanda este salvată cu statusul „Nouă” și cu produsele și cantitățile aferente.
- [ ] Stocul scade corespunzător.
- [ ] Confirmarea din chat include numărul comenzii și totalul.
- [ ] Fluxul se încheie fără intervenție umană.

**Referințe:** CF-05

#### US-12 — Validarea comenzii și actualizarea atomică a stocului

**Modul:** Automatizarea Comenzilor  
**Prioritate:** Mare (`p/high`)  
**Estimare:** 8 story points

**User story:** Ca sistem, pot valida automat comanda dacă produsul există în stocul cerut, actualizând (scăzând) stocul din baza de date SQLite, astfel încât inventarul să rămână corect.

**Criterii de acceptare:**

- [ ] Comanda este validă doar dacă stocul este suficient.
- [ ] Crearea comenzii și scăderea stocului se fac în aceeași tranzacție.
- [ ] La eșec nu rămâne nicio modificare parțială.
- [ ] Comenzile concurente nu vând același stoc.

**Referințe:** CF-04, CF-05, CNF-05

#### US-13 — Refuz sau alternativă la stoc insuficient

**Modul:** Automatizarea Comenzilor  
**Prioritate:** Medie (`p/medium`)  
**Estimare:** 5 story points

**User story:** Ca client, pot să primesc un mesaj automat de refuz sau alternativă în chat dacă stocul este insuficient, astfel încât să știu că produsul nu este momentan disponibil.

**Criterii de acceptare:**

- [ ] Comanda nu este creată când stocul este insuficient.
- [ ] Chatbotul comunică disponibilul curent.
- [ ] Chatbotul propune o cantitate alternativă sau un produs similar.
- [ ] Stocul rămâne neschimbat.

**Referințe:** CF-05

#### US-14 — Istoricul comenzilor în dashboard

**Modul:** Automatizarea Comenzilor  
**Prioritate:** Medie (`p/medium`)  
**Estimare:** 3 story points

**User story:** Ca manager, pot vedea istoricul tuturor comenzilor generate automat de chatbot într-un tabel centralizat, astfel încât să pot urmări vânzările companiei.

**Criterii de acceptare:**

- [ ] Tabelul afișează id, client, produse, cantitate, status și dată.
- [ ] Sunt afișate toate comenzile create prin chat.
- [ ] Există filtrare după status și client.
- [ ] Comenzile sunt ordonate descrescător după dată.

**Referințe:** CF-07

#### US-15 — Istoricul comenzilor clientului și recomandări

**Modul:** Automatizarea Comenzilor  
**Prioritate:** Mică (`p/low`)  
**Estimare:** 5 story points

**User story:** Ca sistem, pot vedea istoricul comenzilor clientului, astfel încât să pot personaliza experiența cu clientul și să recomand produse asemănătoare.

**Criterii de acceptare:**

- [ ] La cerere, sistemul returnează comenzile clientului.
- [ ] Istoricul este folosit pentru recomandări de produse similare.
- [ ] Recomandările nu repetă produsele din comanda curentă.
- [ ] Un client fără istoric primește un mesaj neutru.

**Referințe:** CF-08

#### US-16 — Decizia de utilizare a tool-urilor de personalizare

**Modul:** Automatizarea Comenzilor  
**Prioritate:** Mică (`p/low`)  
**Estimare:** 8 story points

**User story:** Ca sistem, pot decide când să folosesc tool-urile de personalizare a interacțiunii cu clientul, astfel încât să pot menține o comunicare eficientă în funcție de necesități.

**Criterii de acceptare:**

- [ ] Agentul alege tool-ul potrivit în funcție de intenție: istoric, recomandări sau stoc.
- [ ] Dacă datele sunt insuficiente, cere clarificare sau răspunde generic.
- [ ] Tool-urile apelate sunt înregistrate pentru depanare.
- [ ] Mesajele simple nu declanșează tool-uri inutile.

**Referințe:** CF-02, CF-08

### Modulul 5: Alerte & Administrare Excepții

#### US-17 — Alertă vizuală pentru stoc critic

**Modul:** Alerte & Administrare Excepții  
**Prioritate:** Medie (`p/medium`)  
**Estimare:** 3 story points

**User story:** Ca manager, pot vizualiza o alertă în dashboard atunci când stocul unui produs scade sub o limită critică, astfel încât să pot interveni prompt.

**Criterii de acceptare:**

- [ ] Pragul critic este configurabil per produs.
- [ ] Produsele sub prag apar vizual în dashboard.
- [ ] Alerta include numele produsului și cantitatea rămasă.
- [ ] Alerta dispare după reaprovizionare.

**Referințe:** CF-06

---

## 6. Legătura cu cerințele

Cerințele funcționale și nefuncționale sunt definite în [`requirements_document.md`](requirements_document.md). Fiecare user story face referire la cerințele pe care le acoperă (CF-01 … CF-09, CNF-01 … CNF-05).
