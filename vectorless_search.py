"""
Vectorless Search Engine
Performs BM25 lexical ranking and keyword matching over document chunks without embeddings or vector databases.
"""

import re
from typing import List, Tuple, Dict, Any
from rank_bm25 import BM25Okapi
from docx_reader import DocChunk


class VectorlessSearchEngine:
    """Vectorless Information Retrieval engine using Okapi BM25 ranking and structural weighting."""

    def __init__(self, chunks: List[DocChunk]):
        self.chunks = chunks
        self.tokenized_corpus = [self._tokenize(chunk.text + " " + chunk.heading_path) for chunk in chunks]
        self.bm25 = BM25Okapi(self.tokenized_corpus) if self.tokenized_corpus else None

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple tokenizer that converts text to lowercased word tokens."""
        text = text.lower()
        # Keep alphanumeric characters and words
        tokens = re.findall(r'\b\w+\b', text)
        return tokens

    def search(self, query: str, top_k: int = 5) -> List[Tuple[DocChunk, float]]:
        """
        Ranks document chunks against the user query using BM25 + Heading Boost.
        Returns top_k (chunk, score) tuples.
        """
        if not self.chunks or not self.bm25:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            # Fallback to returning initial chunks if query has no tokens
            return [(chunk, 1.0) for chunk in self.chunks[:top_k]]

        # BM25 scores
        raw_scores = self.bm25.get_scores(query_tokens)

        # Apply structural heading boost
        boosted_scores = []
        for idx, (chunk, score) in enumerate(zip(self.chunks, raw_scores)):
            final_score = float(score)

            # Check for exact keyword hits in section headings
            heading_lower = chunk.heading_path.lower()
            for q_token in query_tokens:
                if len(q_token) > 2 and q_token in heading_lower:
                    final_score += 1.5  # Heading match bonus

            # Boost tables if query mentions data, table, figures, numbers, etc.
            if chunk.chunk_type == "table" and any(k in query.lower() for k in ["table", "list", "data", "figure", "number", "cost", "salary", "fee"]):
                final_score += 1.0

            boosted_scores.append((chunk, final_score))

        # Sort descending by score
        boosted_scores.sort(key=lambda item: item[1], reverse=True)

        return boosted_scores[:top_k]

    def get_context_window(self, query: str, top_k: int = 5, max_words: int = 15000) -> str:
        """
        Builds a concise context string containing top ranked sections.
        If the entire document is under max_words, returns the full document for maximum accuracy.
        """
        total_words = sum(len(c.text.split()) for c in self.chunks)

        # If small document, return full document context directly!
        if total_words <= max_words:
            context_blocks = []
            current_heading = ""
            for chunk in self.chunks:
                if chunk.heading_path != current_heading:
                    context_blocks.append(f"\n--- Section: {chunk.heading_path} ---")
                    current_heading = chunk.heading_path
                context_blocks.append(f"[{chunk.chunk_type.upper()}] {chunk.text}")
            return "\n".join(context_blocks)

        # For larger documents, retrieve top-K lexical BM25 passages
        top_results = self.search(query, top_k=top_k)
        
        # Sort top chunks by original document position for natural reading flow
        top_results_sorted = sorted(top_results, key=lambda x: x[0].id)

        context_blocks = [
            f"[NOTE: Vectorless BM25 Search extracted top {len(top_results_sorted)} relevant document passages below]\n"
        ]
        for chunk, score in top_results_sorted:
            context_blocks.append(
                f"--- Passage (Section: '{chunk.heading_path}', Score: {score:.2f}) ---\n{chunk.text}\n"
            )

        return "\n".join(context_blocks)
