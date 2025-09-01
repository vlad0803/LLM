from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
import os


book_path = os.path.join(os.path.dirname(__file__), "book_summaries.txt")
loader = TextLoader(book_path, encoding="utf-8")
documents = loader.load()

# 2. Sparge textul în chunk-uri logice
splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)
chunks = splitter.split_documents(documents)

# 3. Creează embeddings cu modelul 'text-embedding-3-small'
embedding = OpenAIEmbeddings(model="text-embedding-3-small")

# 4. Încarcă documentele în ChromaDB (local)
db = Chroma.from_documents(
    documents=chunks,
    embedding=embedding,
    persist_directory="chroma_books"
)

# 5. Creează un retriever semantic pentru utilizare ulterioară
retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 3})

print("✅ Vector store ChromaDB creat și retriever semantic disponibil.")
