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

def is_emergency_query(query: str) -> bool:
    query = query.lower()

    emergency_keywords = [
        "accident",
        "car accident",
        "crash",
        "collision",
        "hit",
        "met with an accident",
        "vehicle damaged",
        "emergency"
    ]

    return any(keyword in query for keyword in emergency_keywords)

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
        k=6,
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
        f"Retrieved Section {i+1}:\n{doc.page_content}"
        for i, (doc, score) in enumerate(results)
    ]

    context = "\n\n".join(retrieved_context)

    # retrieved_context = [
    #     doc.page_content for doc, score in results
    # ]

    # context = "\n\n".join(retrieved_context)

#     prompt = f"""
# You are an insurance policy assistant.

# Use ONLY the information contained in the retrieved policy context.

# Rules:
# - Do not use outside knowledge.
# - Answer ONLY the user's question.
# - Do not include additional policy details unless they are required to answer the question.
# - If multiple chunks contain the answer, combine only the relevant information.
# - If the answer is not explicitly present, reply exactly:
# "I could not find this information in the policy."
# - Keep the answer concise and focused.
# - For factual questions (policyholder, deductible, IDV, manufacturing year, registration number, dates, etc.), return the exact value from the policy without modification.
# - Quote policy values exactly (policy number, deductible, IDV, dates, registration number, etc.) without modifying them.
# - Do not explain your reasoning.
# - Do not repeat the question.

# Context:
# {context}

# Question:
# {query}

# Answer:
# """


    prompt = f"""

You are INSURIX, an AI insurance policy assistant.

Use ONLY the information provided in the retrieved policy context.

=========================
GENERAL RULES
=========================

- Never use outside knowledge.
- Never invent, assume, or infer information that is not explicitly present in the retrieved context.
- If the answer is not found in the retrieved context, reply exactly:
  "I could not find this information in the policy."
- Read ALL retrieved sections before answering.
- Combine information only when multiple retrieved sections refer to the same user request.
- Ignore unrelated retrieved sections.
- Do not repeat the same information even if it appears in multiple retrieved sections.
- Do not explain your reasoning.

=========================
ACCIDENT / EMERGENCY QUESTIONS
=========================

Examples:
- I met with an accident
- Car accident
- Vehicle damaged
- What should I do?
- Emergency help

When answering these questions:

1. Start with ONE short empathetic sentence.

Example:
I'm sorry to hear about your accident. I hope everyone is safe.

2. Leave ONE blank line.

3. Print the heading:

Immediate Actions

4. Leave ONE blank line.

5. Present the actions as a numbered list in the correct order.

6. Leave ONE blank line.

7. If the retrieved context explicitly mentions policy benefits, print:

Policy Benefits

followed by bullet points.

Examples:
• Roadside Assistance
• Flatbed Towing
• Courtesy Replacement Car
• Personal Accident Cover

Do NOT invent benefits or eligibility conditions.

8. Leave ONE blank line.

9. If emergency contact information exists in the retrieved context, print:

Emergency Contact

followed by bullet points.

Example:

• INSURIX 24×7 Emergency Line: 1800-123-4567
• WhatsApp Assistance Bot: +91-9876543210

=========================
GENERAL PROCEDURAL QUESTIONS
=========================

Examples:
- Theft
- Flood
- Claim process

Present the answer as numbered steps.

Add a Policy Benefits section ONLY if explicitly supported by the retrieved context.

=========================
FACTUAL QUESTIONS
=========================

Return the exact value from the retrieved context.

Never modify policy values.

=========================
RESPONSE FORMAT
=========================

IMPORTANT:

- Put every heading on its own line.
- Leave one blank line after every heading.
- Put every numbered step on a separate line.
- Put every bullet point on a separate line.
- Never write the complete answer as one paragraph.
- Make the response easy to scan.

Context:
{context}

Question:
{query}

Answer:
"""

    generation_start = time.perf_counter()
    
    response = llm.invoke(prompt)

    if is_emergency_query(query):
        response += """

    Need to report the accident?

    I can also help you create an insurance claim.
    Simply type:

    Create a claim
    """

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
