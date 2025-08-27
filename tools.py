# tools.py
import os
import re
from dotenv import load_dotenv
load_dotenv()

# PDF reading: PyPDF2 is used (pip install PyPDF2)
try:
    from PyPDF2 import PdfReader
except Exception as e:
    PdfReader = None

# CrewAI BaseTool fallback
try:
    from crewai.tools import BaseTool
except Exception:
    class BaseTool:
        """Fallback minimal BaseTool so code can run without crewai installed."""
        pass


class ReadDataTool(BaseTool):
    name: str = "read_data_tool"
    description: str = "Reads and extracts text from a PDF financial report given a file path."

    def _run(self, path: str = "data\TSLA-Q2-2025-Update.pdf") -> str:
        """Synchronous PDF text extraction."""
        if not os.path.exists(path):
            return f"❌ File not found: {path}"

        if PdfReader is None:
            return "⚠️ PyPDF2 not installed (PdfReader unavailable). Install with: pip install PyPDF2"

        try:
            reader = PdfReader(path)
            pages = []
            for i, p in enumerate(reader.pages):
                try:
                    text = p.extract_text() or ""
                except Exception:
                    text = ""
                pages.append(text.strip())

            # Join pages and collapse multiple blank lines
            full_report = "\n".join([p for p in pages if p])
            while "\n\n" in full_report:
                full_report = full_report.replace("\n\n", "\n")
            return full_report if full_report.strip() else "⚠️ No extractable text found in PDF."
        except Exception as e:
            return f"⚠️ Error reading PDF: {e}"

    async def _arun(self, path: str = "data/sample.pdf") -> str:
        """Async wrapper that calls the sync implementation (simple approach)."""
        # For simplicity we call the sync implementation (no event loop blocking-heavy work expected for local small PDFs)
        return self._run(path)


# Instantiate for import
read_data_tool = ReadDataTool()
read_data_tool_async = read_data_tool._arun  # reference to async callable
