from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from app.services.policy_service import (
    get_all_active_policy_documents,
    get_single_policy_document,
    get_user_active_policy_documents,
)
import re

CHROMA_DIR = "./chroma_db"

splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,
    chunk_overlap=100,
    separators=[
        "\n\n",
        "\n",
        ". ",
        " ",
        ""
    ]
)


def _chunk_policy(policy):
    """Load a single policy PDF and return tagged chunks."""
    try:
        loader = PyPDFLoader("../data/policies/" + policy["file_path"])
        documents = loader.load()

        for doc in documents:
            text = doc.page_content
            text = text.replace("■", "₹")

            # Normalize all whitespace
            text = re.sub(r"\s+", " ", text).strip()

            doc.page_content = text

        # for doc in documents:
        #     doc.page_content = doc.page_content.replace("■", "₹")

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

# For future use
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


# For future use when ever add admin-triggered rebuilds
def build_chroma_for_user(user_id: int):
    """
    CALLED AFTER LOGIN: Triggered by POST /build-chroma { user_id }.
    Indexes only this user's active policies into ChromaDB.
    Removes any stale chunks for this user before re-inserting,
    so re-running on the same user is always safe.

    Returns a summary dict consumed by the API route.
    """
    print(f"\n[ChromaDB] Building for user_id={user_id}")

    policies = get_user_active_policy_documents(user_id)

    if not policies:
        print(f"  No active policy documents found for user {user_id}")
        return {
            "user_id": user_id,
            "policies_loaded": 0,
            "total_chunks": 0,
            "status": "no_documents",
        }

    print(f"  Found {len(policies)} active policy document(s)")

    # Chunk all PDFs for this user
    all_chunks = []
    for policy in policies:
        all_chunks.extend(_chunk_policy(policy))

    if not all_chunks:
        return {
            "user_id": user_id,
            "policies_loaded": len(policies),
            "total_chunks": 0,
            "status": "no_chunks_created",
        }

    embedding_model = _get_embedding_model()

    # Remove stale chunks for this user's policies before re-inserting
    policy_ids = [p["policy_id"] for p in policies]
    try:
        existing_db = Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=embedding_model,
        )
        for pid in policy_ids:
            stale = existing_db.get(where={"policy_id": pid})["ids"]
            if stale:
                existing_db.delete(ids=stale)
                print(f"  Removed {len(stale)} stale chunk(s) for policy_id={pid}")
    except Exception as e:
        print(f"  Note: could not clean stale chunks ({e}), continuing…")

    # Insert fresh chunks
    db = Chroma.from_documents(
        documents=all_chunks,
        embedding=embedding_model,
        persist_directory=CHROMA_DIR,
    )

    print(f"  ✓ {len(all_chunks)} chunks indexed for user {user_id}")

    return {
        "user_id": user_id,
        "policies_loaded": len(policies),
        "total_chunks": len(all_chunks),
        "status": "success",
    }


if __name__ == "__main__":
    build_full_vectorstore()