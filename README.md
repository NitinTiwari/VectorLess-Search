# Vectorless DOCX AI Agent using Groq

An AI-powered document search and question-answering agent in Python. This project searches inside Microsoft Word (`.docx`) files using a **Vectorless Search Engine** (Okapi BM25 lexical ranking + document structural hierarchy) and generates answers using **Groq's ultra-fast LLMs** (`llama-3.3-70b-versatile`).

## Features

- 🚫 **Vectorless Search**: No vector databases (FAISS, Chroma, Pinecone) or embedding models required.
- 📄 **Rich DOCX Parsing**: Preserves Headings, Paragraphs, Bullet Lists, and converts DOCX Tables to Markdown.
- ⚡ **Groq LLM Acceleration**: Powered by Groq's high-speed inference engine (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, etc.).
- 🎯 **Grounding & Accuracy**: Strict system prompts prevent hallucinations, grounding answers directly in source document sections.
- 💬 **Interactive & Single Query CLI**: Works as an interactive document chat assistant or via script CLI arguments.
- 🛠️ **Sample DOCX Generator**: Includes `create_sample.py` to immediately test with a mock company policy document.

---

## Installation

### 1. Install Dependencies

```bash
cd C:\Users\hp\AI\VectorLess-Search
pip install -r requirements.txt
```

### 2. Configure Groq API Key

Get a free Groq API Key from [https://console.groq.com](https://console.groq.com).

Create a `.env` file in the project folder:

```ini
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
```

---

## Usage Guide

### 1. Quick Start with Sample Document

Generate a sample document and launch interactive chat:

```bash
python main.py
```

Example interaction:
```text
Ask a question > What is the daily meal allowance for Tier 1 cities?

[Groq LLM] Generating answer using model 'llama-3.3-70b-versatile'...

According to Section 4 (Expense Allowances & Compensation Matrix), the daily meal allowance cap for Tier 1 cities is $75 / day. Direct Manager approval is required.
```

### 2. Querying Your Own `.docx` File

#### Interactive Mode:
```bash
python main.py --file "C:\path\to\your_document.docx"
```

#### Single Question Mode:
```bash
python main.py --file "C:\path\to\your_document.docx" --query "Summarize the parental leave policy"
```

#### Change Groq Model:
```bash
python main.py --file "your_doc.docx" --model "llama-3.1-8b-instant"
```

---

## Project Architecture

- **`docx_reader.py`**: Extracts text, heading paths (`Heading 1 > Heading 2`), and formats tables into markdown.
- **`vectorless_search.py`**: Lexical indexer using `rank-bm25` with section/heading boost scoring. Also supports direct context window passing for smaller documents.
- **`groq_agent.py`**: Interacts with the `groq` Python SDK for context-grounded streaming completions.
- **`main.py`**: CLI handler providing interactive chat loop and single-query options.
- **`create_sample.py`**: Helper to generate a multi-section test `.docx` file.

---

## Requirements

- Python 3.8+
- `groq`
- `python-docx`
- `rank-bm25`
- `python-dotenv`
- `colorama`
