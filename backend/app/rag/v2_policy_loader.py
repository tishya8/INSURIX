from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from app.services.policy_service import (
    get_all_active_policy_documents,
    get_single_policy_document
)

CHROMA_DIR = "./chroma_db"

splitter = RecursiveCharacterTextSplitter(
    chunk_size=250,
    chunk_overlap=50
)


def _chunk_policy(policy):
    """Load a single policy PDF and return tagged chunks."""
    try:
        loader = PyPDFLoader("../data/policies/" + policy["file_path"])
        documents = loader.load()

        for doc in documents:
            doc.page_content = doc.page_content.replace("■", "₹")

        chunks = splitter.split_documents(documents)

        for chunk in chunks:
            chunk.metadata["policy_id"] = policy["policy_id"]
            chunk.metadata["policy_number"] = policy["policy_number"]

        print(f"  → {len(chunks)} chunks for policy {policy['policy_id']}")
        return chunks

    except Exception as e:
        print(f"  ✗ Failed to load {policy['file_path']}: {e}")
        return []


def _get_embedding_model():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


def build_full_vectorstore():
    """
    ONE-TIME SETUP: Run this script manually when deploying
    for the first time, or to fully rebuild the ChromaDB.

    Command: python -m app.rag.policy_loader
    """
    policies = get_all_active_policy_documents()
    print(f"Found {len(policies)} policies in DB")

    all_chunks = []
    for policy in policies:
        all_chunks.extend(_chunk_policy(policy))

    print(f"\nTotal chunks: {len(all_chunks)}")

    db = Chroma.from_documents(
        documents=all_chunks,
        embedding=_get_embedding_model(),
        persist_directory=CHROMA_DIR
    )

    print("ChromaDB built successfully!")
    return db


def index_new_policy(policy_id: int):
    """
    CALLED BY API: Triggered automatically whenever a new
    policy document is uploaded via POST /policies/{id}/document.
    Adds only the new policy — does not rebuild everything.
    """
    policy = get_single_policy_document(policy_id)

    if not policy:
        print(f"No document found for policy_id {policy_id}")
        return

    chunks = _chunk_policy(policy)

    if not chunks:
        return

    db = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=_get_embedding_model()
    )
    db.add_documents(chunks)
    print(f"Policy {policy_id} indexed into ChromaDB.")


if __name__ == "__main__":
    build_full_vectorstore()