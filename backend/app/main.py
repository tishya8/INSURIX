from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "INSURIX Backend Running"}

@app.post("/policy/query")
def policy_query(question: str):

    answer = ask_policy(question)

    return {
        "question": question,
        "answer": answer
    }