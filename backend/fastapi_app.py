from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import re
import os
import joblib
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from backend.get_summary_by_file import get_summary_by_title
from langchain.tools import StructuredTool
from langchain_core.messages import HumanMessage, ToolMessage

# --- NLP + Hate Speech Model Setup (self-contained) ---
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))
stemmer = PorterStemmer()

def preprocess_text(text: str) -> str:
    text = re.sub(r'http\S+|www\S+|https\S+', '', text)
    text = re.sub(r'@\w+|#', '', text)
    text = re.sub(r'[^A-Za-z\\s]', '', text)
    words = text.split()
    # Remove stopwords case-insensitive
    words = [w for w in words if w.lower() not in stop_words]
    # Stemming only for non-capitalized words
    words = [stemmer.stem(w) if not w[:1].isupper() else w for w in words]
    return ' '.join(words)


rf_path = r"C:\Users\vlamuresan\OneDrive - ENDAVA\Desktop\Proiect LLM\hate_speech\rf_hate_speech.pkl"
vectorizer_path = r"C:\Users\vlamuresan\OneDrive - ENDAVA\Desktop\Proiect LLM\hate_speech\vectorizer.pkl"
rf = joblib.load(rf_path)
vectorizer = joblib.load(vectorizer_path)

def predict_label(text: str):
    clean = preprocess_text(text)
    X = vectorizer.transform([clean])
    return rf.predict(X)[0]

# --- RAG Components ---
embedding = OpenAIEmbeddings(model="text-embedding-3-small")
db = Chroma(persist_directory="chroma_books", embedding_function=embedding)
retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 10})

get_summary_tool = StructuredTool.from_function(
    name="get_summary_by_title",
    description="Get the summary of a book by its title.",
    func=get_summary_by_title,
)

llm = ChatOpenAI(model="gpt-5-nano", temperature=0.7)
llm_with_tools = llm.bind_tools([get_summary_tool])

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/preprocess_text")
def preprocess_text_api(text: str = Form(...)):
    try:
        result = preprocess_text(text)
        return {"result": result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/predict_label")
def predict_label_api(text: str = Form(...)):
    try:
        result = predict_label(text)
        return {"result": result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/generate_image_with_dalle")
def generate_image_api(prompt: str = Form(...)):
    try:
        import openai
        import os
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.images.generate(
            model="dall-e-2",
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        image_url = response.data[0].url
        return {"image_url": image_url}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/text_to_speech")
def text_to_speech_api(text: str = Form(...)):
    try:
        import openai
        import tempfile
        import os
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            input=text,
            voice="alloy"
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            fp.write(response.content)
            audio_path = fp.name
        from fastapi.responses import FileResponse
        return FileResponse(audio_path, media_type="audio/mpeg", filename="tts.mp3")
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/speech_to_text")
def speech_to_text_api(audio: UploadFile = File(...)):
    import traceback
    import openai
    import os
    from pydub import AudioSegment
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        ext = os.path.splitext(audio.filename)[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_audio:
            tmp_audio.write(audio.file.read())
            tmp_audio.flush()
            tmp_audio_path = tmp_audio.name
        accepted_exts = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm']
        if ext not in accepted_exts:
            sound = AudioSegment.from_file(tmp_audio_path)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_wav:
                sound.export(tmp_wav.name, format='wav')
                tmp_audio_path = tmp_wav.name
        with open(tmp_audio_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=f
            )
        return {"text": transcript.text}
    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse(status_code=500, content={"error": str(e), "trace": tb})


@app.post("/api/rag_recommend")
def rag_recommend_api(text: str = Form(...)):
    try:
        label = predict_label(text)
        if label == "Offensive":
            return JSONResponse(status_code=200, content={"recommendation": None, "source_titles": [], "error": "The language used is not appropriate. Please rephrase your question politely."})

        docs = retriever.invoke(text)
        print(f"[DEBUG] Retrieved documents: {len(docs)}")
        for i, doc in enumerate(docs):
            print(f"[DEBUG] Document {i} page_content: {doc.page_content[:100]}")
        context = "\n\n".join([doc.page_content for doc in docs])
        prompt = f"""
You are an AI assistant that recommends a single book based on the context below.
You are allowed to recommend ONLY a title that appears textually in the context.
Do not invent titles. If none of the books in the context are relevant to the user's question or language, reply exactly with: Sorry, there is no recommendation.
Do not offer alternatives, summaries, or related books if no match is found.
If the user's question is in a language not present in the context, reply with: Sorry, there is no recommendation.
If you recommend a book, use the get_summary_by_title tool to display the full summary.
Always reply with both the book title and its full summary.
Format your answer as:
Title: [book title]
Summary: [book summary]

Context:
{context}

User question: {text}
Answer:
"""
        print("[DEBUG] Prompt sent to LLM:\n", prompt)
        ai_msg = llm_with_tools.invoke([HumanMessage(content=prompt)])
        print("[DEBUG] LLM response:\n", getattr(ai_msg, 'content', ai_msg))
        # Tool calling
        if getattr(ai_msg, "tool_calls", None):
            tool_results = []
            for tc in ai_msg.tool_calls:
                if tc["name"] == "get_summary_by_title":
                    title_arg = tc["args"].get("title") or tc["args"].get("book_title") or tc["args"].get("name")
                    summary_text = get_summary_by_title(title_arg)
                    tool_results.append(
                        ToolMessage(
                            tool_call_id=tc["id"],
                            name=tc["name"],
                            content=summary_text
                        )
                    )
            final_msg = llm_with_tools.invoke([HumanMessage(content=prompt), ai_msg] + tool_results)
            response_text = final_msg.content
        else:
            response_text = ai_msg.content

        # Source titles
        source_titles = []
        for i, doc in enumerate(docs):
            lines = doc.page_content.splitlines()
            title = None
            for line in lines:
                if line.startswith("## Title:"):
                    title = line.replace("## Title:", "").strip()
                    break
            if title:
                source_titles.append(title)
            else:
                source_titles.append("[Title not found]")

        return {"recommendation": response_text, "source_titles": source_titles}
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[RAG ERROR] {str(e)}\n{tb}")
        return JSONResponse(status_code=500, content={"error": str(e), "trace": tb})
