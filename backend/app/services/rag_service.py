from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
import time

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

    total_start = time.perf_counter()

    print("\n===================================")
    print("POLICY SEARCH")
    print("===================================")

    print(f"Policy ID : {policy_id}")
    print(f"Question  : {query}")

    retrieval_start = time.perf_counter()

    results = db.similarity_search_with_score(
        query,
        k=2,
        filter={
            "policy_id": policy_id
        }
    )

    retrieval_time_ms = (time.perf_counter() - retrieval_start) * 1000

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
- Answer ONLY the user's question.
- Do not include additional policy details unless they are required to answer the question.
- If multiple chunks contain the answer, combine only the relevant information.
- If the answer is not explicitly present, reply exactly:
"I could not find this information in the policy."
- Keep the answer concise and focused.
- For factual questions (policyholder, deductible, IDV, manufacturing year, registration number, dates, etc.), return the exact value from the policy without modification.
- Quote policy values exactly (policy number, deductible, IDV, dates, registration number, etc.) without modifying them.
- Do not explain your reasoning.
- Do not repeat the question.

Context:
{context}

Question:
{query}

Answer:
"""



    generation_start = time.perf_counter()
    
    response = llm.invoke(prompt)

    generation_time_ms = (time.perf_counter() - generation_start) * 1000

    total_time_ms = (time.perf_counter() - total_start) * 1000

    print(f"Retrieval Time : {retrieval_time_ms:.2f} ms")
    print(f"Generation Time: {generation_time_ms:.2f} ms")
    print(f"Total Time     : {total_time_ms:.2f} ms")

    if return_context:
        return {
            "answer": response,
            "context": retrieved_context,
            "retrieval_time_ms": retrieval_time_ms,
            "generation_time_ms": generation_time_ms,
            "total_time_ms": total_time_ms
        }

    return response
