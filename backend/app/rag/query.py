from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM

print("===================================")
print("INSURIX POLICY RAG SYSTEM")
print("===================================")

# STEP 1: Load Embedding Model
print("\nSTEP 1: Loading Embedding Model...")

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

print("Embedding Model Loaded!")

# STEP 2: Load ChromaDB
print("\nSTEP 2: Loading ChromaDB...")

db = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embedding_model
)

print("ChromaDB Loaded!")

# STEP 3: Load LLM
print("\nSTEP 3: Loading Mistral Model...")

llm = OllamaLLM(
    model="mistral"
)

print("Mistral Loaded!")


def ask_policy(query):

    print("\n===================================")
    print("NEW QUESTION RECEIVED")
    print("===================================")

    print("\nQUESTION:")
    print(query)

    # STEP 4: Retrieve Relevant Chunks
    print("\nSTEP 4: Searching ChromaDB...")

    results = db.similarity_search(query, k=1)

    print(f"{len(results)} chunk retrieved.")

    # STEP 5: Display Retrieved Chunk
    print("\nSTEP 5: Retrieved Chunk")

    for i, doc in enumerate(results, start=1):

        print("\n------------------------------")
        print(f"CHUNK {i}")
        print("------------------------------")
        print(doc.page_content)

    # STEP 6: Build Context
    print("\nSTEP 6: Building Context...")

    context = "\n\n".join(
        [doc.page_content for doc in results]
    )

    print("Context Built Successfully!")

    # STEP 7: Create Prompt
    print("\nSTEP 7: Creating Prompt...")

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

    # STEP 8: Generate Answer
    print("\nSTEP 8: Sending Context To Mistral...")

    response = llm.invoke(prompt)

    print("\nSTEP 9: Response Generated!")

    return response


if __name__ == "__main__":

    while True:

        query = input(
            "\nAsk a policy question (type exit to quit): "
        )

        if query.lower() == "exit":
            print("\nExiting INSURIX Policy Assistant...")
            break

        answer = ask_policy(query)

        print("\n===================================")
        print("FINAL ANSWER")
        print("===================================")
        print(answer)