"""
Groq AI Agent Module
Handles interaction with Groq LLMs (Llama 3.3 70B, Llama 3.1 8B, Mixtral) to perform document Q&A.
"""

import os
from typing import Dict, Any, Generator, Optional
from dotenv import load_dotenv
from groq import Groq, GroqError

load_dotenv()


class GroqDocxAgent:
    """AI Agent powered by Groq LLMs for grounded document search and answering."""

    DEFAULT_MODEL = "openai/gpt-oss-20b"

    AVAILABLE_MODELS = [
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ]

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY not found! Please set GROQ_API_KEY in your environment or .env file."
            )

        self.model = model if model in self.AVAILABLE_MODELS else self.DEFAULT_MODEL
        self.client = Groq(api_key=self.api_key)

    def query_document(self, query: str, context: str, stream: bool = True):
        """
        Sends query and document context to Groq model and yields/returns answer.
        """
        system_prompt = (
            "You are an accurate AI Document Assistant specializing in analyzing DOCX documents.\n"
            "Your task is to answer user queries using ONLY the document context provided below.\n"
            "Rules:\n"
            "1. Base your answer strictly on facts present in the Document Context.\n"
            "2. If the answer cannot be determined from the context, state clearly: 'The requested information is not found in the document.'\n"
            "3. Reference relevant section headings or tables when providing data.\n"
            "4. Keep your answer clear, well-structured, and concise.\n"
        )

        user_prompt = f"--- DOCUMENT CONTEXT ---\n{context}\n\n--- USER QUERY ---\n{query}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            if stream:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.1,
                    max_completion_tokens=2048,
                    stream=True
                )
                for chunk in response:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.1,
                    max_completion_tokens=2048,
                    stream=False
                )
                return response.choices[0].message.content

        except GroqError as e:
            raise RuntimeError(f"Groq API Error: {str(e)}")
