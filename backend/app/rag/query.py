from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM

print("STEP 1: Loading embeddings...")

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

print("STEP 2: Loading ChromaDB...")

db = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embedding_model
)

query = "What is the deductible amount?"

print("STEP 3: Running retrieval...")

results = db.similarity_search(query, k=2)

context = "\n\n".join(
    [doc.page_content for doc in results]
)

print("STEP 4: Context retrieved.")

print("\nQUESTION:")
print(query)

print("\nCONTEXT:")
print(context[:500])

print("\nSTEP 5: Loading tinyllama...")

llm = OllamaLLM(
    model="tinyllama"
)

prompt = f"""
Answer ONLY from this context.

Context:
{context}

Question:
{query}
"""

print("STEP 6: Calling model...")

response = llm.invoke(prompt)

print("\nFINAL ANSWER:")
print(response)