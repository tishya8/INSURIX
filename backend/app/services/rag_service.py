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

def ask_policy(policy_id, query, return_context=False):

    print("\n===================================")
    print("POLICY SEARCH")
    print("===================================")

    print(f"Policy ID : {policy_id}")
    print(f"Question  : {query}")

    results = db.similarity_search_with_score(
        query,
        k=4,
        filter={
            "policy_id": policy_id
        }
    )

    print(f"\nRetrieved Chunks: {len(results)}")

    for i, (doc, score) in enumerate(results, start=1):

        print("\n-------------------------")
        print(f"CHUNK {i}")
        print("-------------------------")

        print(f"SIMILARITY SCORE: {score:.4f}")

        print("\nMETADATA:")
        print(doc.metadata)

        print("\nCONTENT:")
        print(doc.page_content[:300])

    retrieved_context = [
        doc.page_content for doc, score in results
    ]

    context = "\n\n".join(retrieved_context)

    prompt = f"""
You are an insurance policy assistant.

Use ONLY the information contained in the retrieved policy context.

Rules:
- Do not use outside knowledge.
- If multiple chunks contain the answer, combine them.
- If the answer is not explicitly present, reply exactly:
"I could not find this information in the policy."
- Keep answers concise.
- Quote policy values exactly (policy number, deductible, IDV, dates, registration number, etc.) without modifying them.

Context:
{context}

Question:
{query}

Answer:
"""

    response = llm.invoke(prompt)

    if return_context:
        return {
            "answer": response,
            "context": retrieved_context
        }

    return response
