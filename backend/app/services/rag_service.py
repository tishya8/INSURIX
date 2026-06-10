from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM

print("Loading Embedding Model...")

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

print("Loading ChromaDB...")

db = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embedding_model
)

print("Loading Qwen...")

llm = OllamaLLM(
    model="qwen2.5:1.5b",
    temperature=0
)

def ask_policy(policy_id, query):

    print("\n===================================")
    print("POLICY SEARCH")
    print("===================================")

    print(f"Policy ID : {policy_id}")
    print(f"Question  : {query}")

    results = db.similarity_search(
        query,
        k=2,
        filter={
            "policy_id": policy_id
        }
    )

    print(f"\nRetrieved Chunks: {len(results)}")

    for i, doc in enumerate(results, start=1):

        print("\n-------------------------")
        print(f"CHUNK {i}")
        print("-------------------------")

        print("METADATA:")
        print(doc.metadata)

        print("\nCONTENT:")
        print(doc.page_content[:300])

    context = "\n\n".join(
        [doc.page_content for doc in results]
    )

    prompt = f"""
You are an insurance policy assistant.

Answer the question ONLY using the provided context.

If the answer is not present in the context, reply:

"I could not find this information in the policy."

Context:
{context}

Question:
{query}

Answer:
"""

    response = llm.invoke(prompt)

    return response
