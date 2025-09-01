# Proiect LLM - Book Recommendation & Hate Speech Detection

## Descriere
Acest proiect integrează un backend FastAPI cu un sistem de recomandare de cărți (RAG - Retrieval Augmented Generation) și un modul de detecție hate speech.

### Funcționalități principale
- **Recomandare de cărți:**
  - Folosește ChromaDB și embeddings OpenAI pentru a găsi cărți relevante pe baza întrebării utilizatorului.
  - Recomandarea se face doar din titlurile prezente în contextul bazei de date.
  - Pentru fiecare titlu recomandat, se afișează sumarul complet.
- **Detecție hate speech:**
  - Textul introdus de utilizator este procesat și clasificat (model RandomForest + vectorizer).
  - Dacă textul este ofensator, nu se face recomandare.
- **Alte funcții:**
  - Generare imagine cu DALL-E
  - Text-to-speech și speech-to-text cu OpenAI

## Structură proiect
- `backend/` - Codul backend FastAPI, modulele de RAG, hate speech, sumar cărți, ChromaDB
- `frontend/` - Interfață web (dacă există)
- `hate_speech/` - Scripturi de antrenare/testare și date pentru modelul hate speech
- `book_summaries.txt` - Baza de date cu rezumate de cărți

## Pași de build și rulare
1. Instalează dependențele din `requirements.txt` (Python) și `package.json` (frontend)
2. Rulează scriptul de antrenare pentru hate speech (`train_hate.py`) dacă nu există modelele
3. Inițializează vector store-ul cu `chroma.py` (creează ChromaDB din `book_summaries.txt`)
4. Pornește backend-ul cu:
   ```
   uvicorn backend.fastapi_app:app
   ```
5. (Opțional) Pornește frontend-ul cu:
   ```
   cd frontend
   npm install
   npm run dev
   ```

## Detalii suplimentare
- Recomandarea de carte se face doar din titlurile prezente în contextul bazei de date
- Tool-ul `get_summary_by_title()` este folosit automat de LLM pentru a afișa sumarul complet
- Dacă textul introdus de utilizator este ofensator, nu se face recomandare
- Modelele `.pkl` și baza ChromaDB nu sunt incluse dacă sunt prea mari; folosește scripturile de generare
- Cheile API OpenAI trebuie setate ca variabile de mediu