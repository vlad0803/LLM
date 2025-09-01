# LLM - Book Recommendation & Hate Speech Detection

## Description
This project integrates a FastAPI backend with a book recommendation system (RAG - Retrieval Augmented Generation) and a hate speech detection module.

### Main Features
- **Book Recommendation:**
  - Uses ChromaDB and OpenAI embeddings to find relevant books based on user queries.
  - Recommendations are made only from titles present in the database context.
  - For each recommended title, the full summary is displayed.
- **Hate Speech Detection:**
  - User input is processed and classified (RandomForest model + vectorizer).
  - If the text is offensive, no recommendation is made.
- **Other Functions:**
  - Image generation with DALL-E
  - Text-to-speech and speech-to-text with OpenAI

## Project Structure
- `backend/` - FastAPI backend code, RAG modules, hate speech, book summary, ChromaDB
- `frontend/` - Web interface (if present)
- `hate_speech/` - Training/testing scripts and data for the hate speech model
- `book_summaries.txt` - Book summaries database

## Build & Run Steps
1. Install dependencies from `requirements.txt` (Python) and `package.json` (frontend)
2. Run the training script for hate speech (`train_hate.py`) if models do not exist
3. Initialize the vector store with `chroma.py` (creates ChromaDB from `book_summaries.txt`)
4. Start the backend:
   ```
   uvicorn backend.fastapi_app:app
   ```
5. (Optional) Start the frontend:
   ```
   cd frontend
   npm install
   npm run dev
   ```
6. In the frontend, enter your command or question in the designated text box, or activate audio mode to speak your query.
7. To generate an image or transform the result into audio, use the specific buttons available in the interface.

## Additional Details
- Book recommendations are made only from titles present in the database context
- The tool `get_summary_by_title()` is automatically used by the LLM to display the full summary
- If the user input is offensive, no recommendation is made
- `.pkl` models and ChromaDB database are not included if too large; use the provided scripts to generate them
- OpenAI API keys must be set as environment variables
