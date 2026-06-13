from app.services.intent_service import detect_intent

queries = [
    "What is the deductible amount?",
    "My bike was stolen yesterday",
    "Track my claim"
]

for q in queries:

    print("\nQUESTION:")
    print(q)

    print("INTENT:")
    print(detect_intent(q))