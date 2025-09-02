# 🤖LawBotics - AI-Powered Legal Document Assistant

LawBotics is a web-based AI assistant designed to simplify legal workflows. It allows users to upload and analyze legal documents, ask chatbot-style legal queries, get simplified explanations of legal terms, and summarize documents using advanced NLP models like InLegalBERT.

## 🚀 Features

- 📂 Document Upload & Analysis – Upload contracts, agreements, or other legal documents for instant analysis.

- 💬 AI Chatbot for Legal Queries – Ask legal questions in natural language.

- 📖 Legal Term Simplification – Complex legal jargon explained in plain English.

- ✨ Document Summarization – Concise summaries of lengthy legal documents.

---

## 🛠 Tech Stack

| Layer      | Technology |
|------------|------------|
| **Frontend** | HTML, CSS, TailwindCSS |
| **Backend framework**  | Flask |
| **ASGI server** | Uvicorn |
| **NLP preprocessing**     | spaCy (en_core_web_sm) |
| **Model backend** | PyTorch |
| **Transformers (HuggingFace)** | InLegalBERT |

---


## ⚙️ Installation & Setup

### 1️⃣ Clone the repository

```bash
git clone https://github.com/snehhall/LawBotics.git

cd LawBotics/backend
```


### 2️⃣ Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate    # Windows
# OR
source venv/bin/activate # Mac/Linux
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt

python -m spacy download en_core_web_sm
```

API will be available at: http://127.0.0.1:8000

### 📖 Usage

- Upload a legal document from the frontend.

- The backend processes it with spaCy and InLegalBERT.

- Ask questions in the chatbot to analyze clauses or terms.

- Get simplified explanations and summaries instantly.