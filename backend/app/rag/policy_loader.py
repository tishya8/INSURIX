from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


# Load PDF
loader = PyPDFLoader("../data/policies/vehicle_policy.pdf")
documents = loader.load()

for doc in documents:
    doc.page_content = doc.page_content.replace("■", "₹")

# Chunking
splitter = RecursiveCharacterTextSplitter(
    chunk_size=250,
    chunk_overlap=50
)

chunks = splitter.split_documents(documents)

print("Chunks Created:", len(chunks))

# Embeddings Model
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Create ChromaDB
db = Chroma.from_documents(
    documents=chunks,
    embedding=embedding_model,
    persist_directory="./chroma_db"
)

print("ChromaDB Created Successfully!")