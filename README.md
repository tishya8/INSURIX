# 📌 INSURIX - Insurance Policy RAG System

## 🧠 Overview

INSURIX is a lightweight AI-powered Insurance Policy Question Answering System built using Retrieval-Augmented Generation (RAG).

It enables users to ask natural language questions on insurance policy documents and get accurate answers using a local AI pipeline.

### 🔧 Core Technologies
- Vector Database: ChromaDB
- Embeddings: HuggingFace (sentence-transformers/all-MiniLM-L6-v2)
- LLM: Qwen2.5 1.5B via Ollama
- Framework: LangChain
- Data: Insurance Policy Documents (PDF/Text)

The system is optimized to run on low-resource machines (8GB–16GB RAM laptops).

---

## 🚀 Features

- Load and process insurance policy documents (PDF/Text)
- Semantic search using vector embeddings
- Context-aware question answering (RAG pipeline)
- CLI-based chatbot interface
- Lightweight local LLM (Qwen2.5 1.5B)
- Fully offline system (no API dependency)

---

## 🏗️ System Architecture

User Question
↓
HuggingFace Embeddings (MiniLM)
↓
ChromaDB Vector Search
↓
Relevant Policy Chunks Retrieved
↓
Context + Question Prompt
↓
Qwen2.5 (1.5B) via Ollama
↓
Final Answer

---

## 📁 Project Structure

INSURIX/
├── app/
│   ├── rag/
│   │   └── query.py   # Main RAG pipeline
│   ├── data/          # Insurance policy documents
│   ├── chroma_db/     # Vector database storage
├── venv/
├── requirements.txt
└── README.md

---

## ⚙️ Setup Instructions

### Clone Repository
git clone https://github.com/your-username/insurix.git
cd insurix

### Create Virtual Environment
python3 -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

### Install Dependencies
pip install -r requirements.txt

If not available:
pip install langchain langchain-community langchain-huggingface chromadb sentence-transformers ollama

### Install Ollama
https://ollama.ai

### Pull Model
ollama pull qwen2.5:1.5b

### Verify
ollama run qwen2.5:1.5b

---

## ▶️ Run Project

python app/rag/query.py

---

## 💬 Example Usage

Ask a policy question:
What is the deductible amount?

Output:
FINAL ANSWER:
The deductible amount is ₹5,000 per approved claim.

---

## 📌 Key Highlights

- Fully offline AI system
- Lightweight and laptop-friendly
- Fast RAG pipeline
- Easy to extend into API or web app


