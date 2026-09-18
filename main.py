"""
Main Entry Point for Vectorless DOCX AI Agent using Groq
"""

import sys
import os
import argparse
from typing import Optional

from docx_reader import DocxReader
from vectorless_search import VectorlessSearchEngine
from groq_agent import GroqDocxAgent
from create_sample import create_sample_docx

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLOR = True
except ImportError:
    COLOR = False


def print_colored(text: str, color_code: str = ""):
    if COLOR and color_code:
        print(f"{color_code}{text}{Style.RESET_ALL}")
    else:
        print(text)


def run_agent_query(
    reader: DocxReader,
    search_engine: VectorlessSearchEngine,
    agent: GroqDocxAgent,
    query: str,
    top_k: int = 5
):
    print_colored(f"\n[Vectorless Search] Searching docx for: '{query}'...", Fore.CYAN if COLOR else "")
    
    # Extract relevant context using BM25 / Document Pass
    context = search_engine.get_context_window(query=query, top_k=top_k)

    print_colored(f"[Groq LLM] Generating answer using model '{agent.model}'...\n", Fore.YELLOW if COLOR else "")
    print_colored("--- ANSWER ---", Fore.GREEN if COLOR else "")

    try:
        response_generator = agent.query_document(query=query, context=context, stream=True)
        for chunk in response_generator:
            sys.stdout.write(chunk)
            sys.stdout.flush()
        print("\n")

    except Exception as e:
        print_colored(f"\nError processing query: {e}", Fore.RED if COLOR else "")


def interactive_mode(file_path: str, agent: GroqDocxAgent, top_k: int):
    print_colored("=====================================================", Fore.MAGENTA if COLOR else "")
    print_colored("   Vectorless DOCX AI Agent (Powered by Groq LLM)   ", Fore.MAGENTA if COLOR else "")
    print_colored("=====================================================", Fore.MAGENTA if COLOR else "")
    print(f" Loaded Document: {os.path.abspath(file_path)}")
    print(f" Groq Model     : {agent.model}")
    print(" Vectorless IR  : BM25 Lexical Ranking + Heading Context")
    print(" (Type 'exit', 'quit', or 'q' to end)\n")

    # Read DOCX once
    reader = DocxReader(file_path)
    chunks = reader.extract_chunks()
    print_colored(f"Successfully extracted {len(chunks)} elements from docx.\n", Fore.GREEN if COLOR else "")

    search_engine = VectorlessSearchEngine(chunks)

    while True:
        try:
            query = input("Ask a question > ").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                break

            run_agent_query(reader, search_engine, agent, query, top_k=top_k)

        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break


def main():
    parser = argparse.ArgumentParser(description="Vectorless DOCX Search Agent using Groq LLM")
    parser.add_argument(
        "--file", "-f",
        type=str,
        default="sample_company_policy.docx",
        help="Path to the .docx file to search into"
    )
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Single query mode. If omitted, starts interactive chat mode."
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=GroqDocxAgent.DEFAULT_MODEL,
        help=f"Groq model to use (default: {GroqDocxAgent.DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--top-k", "-k",
        type=int,
        default=5,
        help="Number of relevant sections to retrieve via BM25 (default: 5)"
    )
    parser.add_argument(
        "--create-sample",
        action="store_true",
        help="Generate a sample company policy docx file and exit"
    )

    args = parser.parse_args()

    if args.create_sample:
        create_sample_docx(args.file)
        return

    # Check if docx file exists; if default file missing, generate sample automatically!
    if not os.path.exists(args.file):
        if args.file == "sample_company_policy.docx":
            print_colored(f"Default file '{args.file}' not found. Generating sample DOCX...", Fore.YELLOW if COLOR else "")
            create_sample_docx(args.file)
        else:
            print_colored(f"Error: Specified DOCX file not found: {args.file}", Fore.RED if COLOR else "")
            sys.exit(1)

    # Initialize Groq Agent
    try:
        agent = GroqDocxAgent(model=args.model)
    except ValueError as err:
        print_colored(f"\nConfiguration Error: {err}", Fore.RED if COLOR else "")
        print_colored("Please create a .env file with your GROQ_API_KEY=your_key_here or set the environment variable.", Fore.YELLOW if COLOR else "")
        sys.exit(1)

    # Run single query or interactive chat
    if args.query:
        reader = DocxReader(args.file)
        chunks = reader.extract_chunks()
        search_engine = VectorlessSearchEngine(chunks)
        run_agent_query(reader, search_engine, agent, args.query, top_k=args.top_k)
    else:
        interactive_mode(args.file, agent, args.top_k)


if __name__ == "__main__":
    main()
