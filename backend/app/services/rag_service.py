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

# ---------------------------------------------------------------------------
# Query classifiers
# ---------------------------------------------------------------------------

def is_initial_accident_query(query: str) -> bool:
    """
    True ONLY for the broad "I was in an accident, what do I do?" question.
    Requires a clear "what should I do / help me / emergency" signal alongside
    an accident mention — NOT specific follow-up questions about individual
    benefits.

    Deliberately excludes:
      - "Will my car be towed?"
      - "Do I get roadside assistance?"
      - "Can I get a replacement car?"
      - "How do I request towing after an accident?"
    These are SPECIFIC follow-ups that should be answered precisely.
    """
    q = query.lower().strip()

    # Must mention an accident event
    accident_signals = [
        "met with an accident", "met with a car accident",
        "had an accident", "been in an accident",
        "car accident", "vehicle accident",
        "got into an accident", "been involved in an accident",
    ]
    has_accident = any(s in q for s in accident_signals)
    if not has_accident:
        return False

    # Must also have a "what do I do / help" signal
    # (i.e., it's an open-ended guidance request, not a specific question)
    guidance_signals = [
        "what should i do", "what do i do", "what now",
        "help me", "guide me", "what are the steps",
        "what happens now", "what next",
        "what are my options",
    ]
    has_guidance = any(s in q for s in guidance_signals)

    # A very short message like "I met with a car accident" with no follow-up
    # question also counts as initial guidance
    is_bare_statement = (
        has_accident
        and not any(w in q for w in ["tow", "roadside", "replacement", "courtesy",
                                      "cover", "deductible", "claim", "document",
                                      "how long", "how do i", "how much",
                                      "how to", "can i get", "will i get",
                                      "do i get", "am i covered"])
        and len(q.split()) <= 12
    )

    return has_guidance or is_bare_statement


def is_accident_followup_query(query: str) -> bool:
    """
    True for specific questions asked after (or in the context of) an accident,
    about individual benefits like towing, roadside assistance, replacement car.

    These should NOT trigger the full accident-guidance response — they need
    a precise, focused answer from the RAG pipeline.
    """
    q = query.lower().strip()

    followup_patterns = [
        "will my car be towed", "can my car be towed",
        "towing", "tow truck", "flatbed",
        "roadside assistance", "roadside help",
        "courtesy car", "replacement car", "courtesy replacement",
        "temporary car", "temp car",
        "how do i request towing", "how to get towing",
        "how long will towing", "how long does towing",
        "what does roadside", "what is roadside",
        "what is included in roadside",
        "do i get roadside", "will i get roadside",
        "can i get roadside", "am i covered for towing",
        "will i get a replacement", "can i get a replacement",
        "do i get a replacement", "am i entitled to",
        "how long for replacement", "how many days replacement",
        "free towing", "towing distance", "towing limit",
        "50 km", "towing covered",
    ]
    return any(p in q for p in followup_patterns)


# ---------------------------------------------------------------------------
# Prompt builders
#
# Strategy: few-shot examples instead of meta-instructions.
#
# qwen2.5:1.5b (and small LLMs in general) tend to echo back numbered
# instruction lists verbatim when the prompt says things like:
#   "1. ONE short empathetic sentence."
#   "2. Blank line."
# because the model treats those as content to reproduce.
#
# Solution: show the model a COMPLETED example in the exact format we want,
# then give it the real context and ask it to fill in the same template.
# Small models are much better at "continue this pattern" than "follow these
# abstract rules".
# ---------------------------------------------------------------------------

def _build_initial_accident_prompt(context: str, query: str) -> str:
    """
    Few-shot prompt for the initial accident guidance response.
    Shows a completed example → model continues the same pattern.
    """
    return f"""You are INSURIX, an AI insurance policy assistant.
Use ONLY the information in the policy context below. Never invent details.

Here is an example of how to respond when a user reports an accident:

---EXAMPLE START---
User: I was in a car accident. What do I do?

I'm sorry to hear about your accident. I hope everyone is safe.

Immediate Actions

1. Stop the vehicle safely and switch on hazard lights.
2. Check all occupants for injuries. Call 108 (Ambulance) or 112 if anyone is hurt.
3. Contact the INSURIX 24/7 Emergency Line: 1800-123-4567 or WhatsApp: +91-9876543210. Share your policy number and GPS location.
4. Take clear photographs of vehicle damage, the accident scene, and the other vehicle's registration plate.
5. If third-party property or persons are injured, lodge a police GD entry or FIR.
6. Have the vehicle towed to an authorized INSURIX network garage. A courtesy replacement car will be arranged if repairs take more than 4 working days.

Policy Benefits

• Roadside Assistance
• Flatbed Towing (free up to 50 km)
• Courtesy Replacement Car (up to 7 days per claim)
• Personal Accident Cover up to ₹15,00,000

Emergency Contact

• INSURIX 24×7 Emergency Line: 1800-123-4567
• WhatsApp Assistance Bot: +91-9876543210
---EXAMPLE END---

Now answer the real user question using ONLY the policy context provided.
Follow the exact same structure as the example above.
Do NOT copy the example text — use the actual details from the policy context.

Policy Context:
{context}

User Question: {query}

Answer:
"""


def _build_followup_prompt(context: str, query: str, accident_context: str | None) -> str:
    """
    Few-shot prompt for specific follow-up questions about towing,
    roadside assistance, replacement car, etc.
    """
    ctx_note = ""
    if accident_context:
        ctx_note = "The user was recently in a car accident and already received emergency guidance. Answer their specific follow-up question only.\n\n"

    return f"""You are INSURIX, an AI insurance policy assistant.
Use ONLY the information in the policy context below. Never invent details.
{ctx_note}
Here are examples of focused follow-up answers:

---EXAMPLE 1---
User: Will my car be towed?
Yes. INSURIX provides free flatbed towing up to 50 km per breakdown or accident event.
Beyond 50 km, towing is charged at ₹75 per km.
To request towing, call 1800-123-4567 or WhatsApp +91-9876543210 with your policy number and GPS location.
---EXAMPLE 1 END---

---EXAMPLE 2---
User: Do I get roadside assistance?
Yes. Your policy includes 24/7 Roadside Assistance with these services:

• Emergency Flatbed Towing — free up to 50 km
• Battery Jump-Start — unlimited dispatches
• Flat Tyre Assistance — spare wheel swap on site
• Emergency Fuel Delivery — up to 5 litres (fuel cost payable on spot)
• Locksmith Assistance — up to ₹3,000 per incident
---EXAMPLE 2 END---

---EXAMPLE 3---
User: Can I get a courtesy replacement car?
Yes, if repairs to your vehicle are estimated to take more than 4 working days.

• Duration: up to 7 consecutive days per claim (maximum 14 days per policy year)
• If a physical car is unavailable, INSURIX reimburses cab/rental expenses up to ₹1,500 per day
• Must be repaired at an authorized INSURIX network cashless garage
---EXAMPLE 3 END---

Now answer the real user question using ONLY the policy context provided.
Give a direct, focused answer in the same style as the examples above.
Do NOT repeat full accident guidance — answer only the specific question asked.

Policy Context:
{context}

User Question: {query}

Answer:
"""


def _build_general_prompt(context: str, query: str) -> str:
    """
    Few-shot prompt for general policy questions (non-accident).
    """
    return f"""You are INSURIX, an AI insurance policy assistant.
Use ONLY the information in the policy context below. Never invent details.
If the answer is not in the context, reply: "I could not find this information in the policy."

Here are examples of how to answer different question types:

---EXAMPLE 1 (factual)---
User: What is the deductible?
The compulsory deductible is ₹5,000 per Own Damage claim event. This amount must be paid directly to the repair garage before insurance funds are released.
---EXAMPLE 1 END---

---EXAMPLE 2 (coverage question)---
User: Is theft covered?
Yes. The policy covers theft and attempted theft of the insured vehicle up to the Insured Declared Value (IDV) minus deductibles.

Requirements to file a theft claim:
1. Notify INSURIX within 48 hours of discovering the theft.
2. Lodge a First Information Report (FIR) with the local police immediately.
3. Submit all original vehicle ignition keys.
4. Provide a certified Non-Traceable Report from the court or police before final settlement.
---EXAMPLE 2 END---

---EXAMPLE 3 (process question)---
User: How do I file a claim?
1. Contact INSURIX within 48 hours via 1800-123-4567 or WhatsApp +91-9876543210.
2. A surveyor will be assigned within 24-48 hours to inspect the vehicle.
3. INSURIX issues a digital Work Order approving repairs at an authorized garage.
4. Repair bills are settled directly between INSURIX and the garage (cashless). You pay only the ₹5,000 compulsory deductible.
---EXAMPLE 3 END---

Now answer the real user question using ONLY the policy context provided.
Follow the same style as the examples — factual, direct, properly formatted.

Policy Context:
{context}

User Question: {query}

Answer:
"""
# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ask_policy(policy_id, query, return_context=False, accident_context: str | None = None):
    """
    Main RAG entry point.

    Parameters
    ----------
    policy_id       : int   — policy to search in ChromaDB
    query           : str   — user's question
    return_context  : bool  — if True, return full dict with timing info
    accident_context: str | None
                      When provided, signals that this query is a follow-up
                      to an accident conversation. The string is a brief
                      summary injected into the prompt so the LLM understands
                      the conversation context without repeating the full
                      accident guidance.
    """
    total_start = time.perf_counter()

    print("\n===================================")
    print("POLICY SEARCH")
    print("===================================")
    print(f"Policy ID        : {policy_id}")
    print(f"Question         : {query}")
    print(f"Accident context : {accident_context!r}")

    # ── ChromaDB retrieval ────────────────────────────────────────────────
    retrieval_start = time.perf_counter()

    results = db.similarity_search_with_score(
        query,
        k=6,
        filter={"policy_id": policy_id}
    )

    retrieval_time_ms = (time.perf_counter() - retrieval_start) * 1000

    print(f"\nRetrieved Chunks: {len(results)}")
    for i, (doc, score) in enumerate(results, start=1):
        print(f"\n--- CHUNK {i} | SCORE: {score:.4f} ---")
        print("METADATA:", doc.metadata)
        print("CONTENT:", doc.page_content[:300])

    retrieved_context = [
        f"Retrieved Section {i+1}:\n{doc.page_content}"
        for i, (doc, score) in enumerate(results)
    ]
    context = "\n\n".join(retrieved_context)

    # ── Classify query → choose prompt ───────────────────────────────────
    if is_initial_accident_query(query):
        print("[rag] Query type: INITIAL_ACCIDENT")
        prompt = _build_initial_accident_prompt(context, query)
        append_claim_cta = True          # add "create a claim" CTA

    elif is_accident_followup_query(query) or accident_context:
        print("[rag] Query type: ACCIDENT_FOLLOWUP")
        prompt = _build_followup_prompt(context, query, accident_context)
        append_claim_cta = False         # specific answer, no CTA needed

    else:
        print("[rag] Query type: GENERAL")
        prompt = _build_general_prompt(context, query)
        append_claim_cta = False

    # ── LLM generation ───────────────────────────────────────────────────
    generation_start = time.perf_counter()
    response = llm.invoke(prompt)

    # Append claim CTA only for the initial accident guidance response
    if append_claim_cta:
        response = response.rstrip() + (
            "\n\n"
            "Need to report the accident?\n\n"
            "I can also help you create an insurance claim.\n"
            "Simply type: Create a claim"
        )

    generation_time_ms = (time.perf_counter() - generation_start) * 1000
    total_time_ms      = (time.perf_counter() - total_start) * 1000

    print(f"Retrieval Time : {retrieval_time_ms:.2f} ms")
    print(f"Generation Time: {generation_time_ms:.2f} ms")
    print(f"Total Time     : {total_time_ms:.2f} ms")

    if return_context:
        return {
            "answer":              response,
            "context":             retrieved_context,
            "retrieval_time_ms":   retrieval_time_ms,
            "generation_time_ms":  generation_time_ms,
            "total_time_ms":       total_time_ms,
        }

    return response
