from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


# Load PDF
# loader = PyPDFLoader("../data/policies/vehicle_policy.pdf")
# documents = loader.load()

# for doc in documents:
#     doc.page_content = doc.page_content.replace("■", "₹")

# # Chunking
# splitter = RecursiveCharacterTextSplitter(
#     chunk_size=250,
#     chunk_overlap=50
# )

# chunks = splitter.split_documents(documents)

# for chunk in chunks:

#     chunk.metadata["policy_id"] = 1
#     chunk.metadata["policy_number"] = "CAR-101"

# print("Metadata Added")

# print("Chunks Created:", len(chunks))

# print(chunks[0].metadata)

all_chunks = []

policies = [
    {
        "pdf": "../data/policies/vehicle_policy.pdf",
        "policy_id": 1,
        "policy_number": "CAR-101"
    },
    {
        "pdf": "../data/policies/bike_policy.pdf",
        "policy_id": 2,
        "policy_number": "BIKE-101"
    },
    {
        "pdf": "../data/policies/vehicle2_policy.pdf",
        "policy_id": 3,
        "policy_number": "CAR-102"
    }
]

splitter = RecursiveCharacterTextSplitter(
    chunk_size=250,
    chunk_overlap=50
)

for policy in policies:

    print(f"Loading {policy['pdf']}")

    loader = PyPDFLoader(policy["pdf"])
    documents = loader.load()

    for doc in documents:
        doc.page_content = doc.page_content.replace("■", "₹")

    chunks = splitter.split_documents(documents)

    for chunk in chunks:
        chunk.metadata["policy_id"] = policy["policy_id"]
        chunk.metadata["policy_number"] = policy["policy_number"]

    all_chunks.extend(chunks)

print("Total Chunks Created:", len(all_chunks))

# Embeddings Model
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Create ChromaDB
db = Chroma.from_documents(
    documents=all_chunks,
    embedding=embedding_model,
    persist_directory="./chroma_db"
)

print("ChromaDB Created Successfully!")