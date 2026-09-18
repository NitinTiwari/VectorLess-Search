"""
DOCX Reader Module
Extracts structured sections, headings, paragraphs, lists, and tables from .docx files.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import os
import docx


@dataclass
class DocChunk:
    id: int
    heading_path: str
    text: str
    chunk_type: str  # 'heading', 'paragraph', 'list_item', 'table'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "heading_path": self.heading_path,
            "text": self.text,
            "chunk_type": self.chunk_type
        }


class DocxReader:
    """Reads and parses DOCX files preserving layout context (headings and tables)."""

    def __init__(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"DOCX file not found at: {file_path}")
        self.file_path = file_path
        self.doc = docx.Document(file_path)

    def extract_chunks(self) -> List[DocChunk]:
        """Iterates through docx elements (paragraphs and tables) preserving section structure."""
        chunks: List[DocChunk] = []
        chunk_id = 0
        heading_stack: List[str] = []

        # Iterate over all block elements (paragraphs and tables) in document body order
        for block in self._iter_block_items(self.doc):
            if isinstance(block, docx.text.paragraph.Paragraph):
                text = block.text.strip()
                if not text:
                    continue

                style_name = block.style.name.lower() if block.style else ""
                
                # Check if paragraph is a heading
                if style_name.startswith("heading"):
                    level = self._get_heading_level(style_name)
                    # Update heading stack to current level
                    if level <= len(heading_stack):
                        heading_stack = heading_stack[:level - 1]
                    heading_stack.append(text)
                    
                    heading_path = " > ".join(heading_stack)
                    chunks.append(DocChunk(
                        id=chunk_id,
                        heading_path=heading_path,
                        text=text,
                        chunk_type="heading"
                    ))
                    chunk_id += 1

                # Check if paragraph is a list item
                elif "list" in style_name or block.text.startswith(("•", "-", "*")) or (len(text) > 2 and text[0].isdigit() and text[1] in (".", ")")):
                    heading_path = " > ".join(heading_stack) if heading_stack else "General Content"
                    chunks.append(DocChunk(
                        id=chunk_id,
                        heading_path=heading_path,
                        text=text,
                        chunk_type="list_item"
                    ))
                    chunk_id += 1

                # Normal paragraph
                else:
                    heading_path = " > ".join(heading_stack) if heading_stack else "General Content"
                    chunks.append(DocChunk(
                        id=chunk_id,
                        heading_path=heading_path,
                        text=text,
                        chunk_type="paragraph"
                    ))
                    chunk_id += 1

            elif isinstance(block, docx.table.Table):
                table_md = self._format_table_as_markdown(block)
                if table_md.strip():
                    heading_path = " > ".join(heading_stack) if heading_stack else "General Content"
                    chunks.append(DocChunk(
                        id=chunk_id,
                        heading_path=heading_path,
                        text=table_md,
                        chunk_type="table"
                    ))
                    chunk_id += 1

        return chunks

    def get_full_text(self, chunks: Optional[List[DocChunk]] = None) -> str:
        """Combines chunks into a structured markdown-like document string."""
        if chunks is None:
            chunks = self.extract_chunks()

        formatted_lines = []
        last_heading = ""

        for chunk in chunks:
            if chunk.heading_path != last_heading:
                formatted_lines.append(f"\n### [Section: {chunk.heading_path}]")
                last_heading = chunk.heading_path

            if chunk.chunk_type == "heading":
                continue  # Heading path already noted
            elif chunk.chunk_type == "table":
                formatted_lines.append(f"\n{chunk.text}\n")
            elif chunk.chunk_type == "list_item":
                formatted_lines.append(f"- {chunk.text}")
            else:
                formatted_lines.append(chunk.text)

        return "\n".join(formatted_lines).strip()

    @staticmethod
    def _get_heading_level(style_name: str) -> int:
        """Extracts numerical level from heading style name (e.g. 'heading 2' -> 2)."""
        parts = style_name.split()
        for part in parts:
            if part.isdigit():
                return int(part)
        return 1

    @staticmethod
    def _format_table_as_markdown(table: docx.table.Table) -> str:
        """Converts docx Table into a clean Markdown table string."""
        rows_data = []
        for row in table.rows:
            row_cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
            rows_data.append(row_cells)

        if not rows_data or not any(rows_data):
            return ""

        headers = rows_data[0]
        markdown_lines = []
        markdown_lines.append("| " + " | ".join(headers) + " |")
        markdown_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        for row in rows_data[1:]:
            # Ensure row length matches headers
            if len(row) < len(headers):
                row = row + [""] * (len(headers) - len(row))
            markdown_lines.append("| " + " | ".join(row[:len(headers)]) + " |")

        return "\n".join(markdown_lines)

    @staticmethod
    def _iter_block_items(parent):
        """Yield each paragraph and table in document body order."""
        if isinstance(parent, docx.document.Document):
            parent_elm = parent.element.body
        else:
            parent_elm = parent._element

        for child in parent_elm.iterchildren():
            if isinstance(child, docx.oxml.text.paragraph.CT_P):
                yield docx.text.paragraph.Paragraph(child, parent)
            elif isinstance(child, docx.oxml.table.CT_Tbl):
                yield docx.table.Table(child, parent)
