# agents.py
import re
import datetime
from typing import Dict, Any, List

# Note: These are minimal deterministic agent implementations intended to be predictable,
# non-hallucinating, and to work without external LLMs for local testing.

def _get_text_from_tools(tools, file_path: str) -> str:
    """Helper to extract text using the first provided tool. Handles both sync and async tool objects."""
    if not tools:
        return ""
    tool = tools[0]
    # If tool has _run, call it
    if hasattr(tool, "_run"):
        return tool._run(file_path)
    # If tool is a callable function
    if callable(tool):
        try:
            return tool(file_path)
        except Exception:
            return ""
    return ""

class VerifierAgent:
    """Simple verifier agent: determines if the doc is likely a financial report and extracts metadata."""
    def run(self, payload: Dict[str, Any], tools: list):
        file_path = payload.get("file_path")
        text = _get_text_from_tools(tools, file_path)
        meta = {
            "is_financial_report": False,
            "title": None,
            "date": None,
            "sections": [],
            "notes": ""
        }

        if not text or text.startswith("❌") or text.startswith("⚠️"):
            meta["notes"] = f"Could not read file or no extractable text. Reader output: {text[:200]}"
            return meta

        # Heuristic: search for common financial-report headings or "Quarter", "Earnings", "Quarterly Report"
        lc = text.lower()
        triggers = ["quarter", "earnings", "report", "consolidated statements", "management's discussion", "md&a", "financial statements", "notes to the financial statements", "income statement", "balance sheet"]
        found_trigger = any(t in lc for t in triggers)
        meta["is_financial_report"] = bool(found_trigger)

        # Title: first non-empty line (up to 150 chars) that looks like a title (all-cap words or starts with 'Tesla' etc.)
        first_lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if first_lines:
            candidate = first_lines[0]
            # if the first line is short and contains letters, treat as title
            if 3 < len(candidate) < 200:
                meta["title"] = candidate

        # Date extraction: ISO or patterns like "Q2 2025", "Quarter 2 2025", "June 30, 2025"
        # Try multiple regex patterns in order
        date_patterns = [
            r"(Q[1-4]\s?[-]?\s?\d{4})",                # Q2 2025
            r"(Quarter\s?[1-4][,]?\s?\d{4})",          # Quarter 2 2025
            r"(\b[A-Za-z]{3,9}\s+\d{1,2},\s?\d{4}\b)", # June 30, 2025
            r"(\d{4}-\d{2}-\d{2})",                    # 2025-06-30
            r"(\b\d{4}\b)"                             # fallback year
        ]
        for pat in date_patterns:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                meta["date"] = m.group(1).strip()
                break

        # Sections: search for known section headers and return which are present
        known_sections = [
            "Highlights", "Management's Discussion", "Management Discussion", "MD&A",
            "Financial Statements", "Notes to the Financial Statements", "Risk Factors",
            "Income Statement", "Consolidated Statements", "Balance Sheet", "Cash Flow"
        ]
        found_sections = []
        for s in known_sections:
            if re.search(re.escape(s), text, flags=re.IGNORECASE):
                found_sections.append(s)
        meta["sections"] = found_sections

        if not found_trigger:
            meta["notes"] += "No common financial-report trigger words found. Document may not be a financial report."

        return meta


class FinancialAnalystAgent:
    """Simple deterministic extractor for key financial metrics and risk scanning."""
    def _extract_metric_lines(self, text: str, metric_names: List[str]) -> List[str]:
        lines = []
        for ln in text.splitlines():
            if any(m.lower() in ln.lower() for m in metric_names):
                lines.append(ln.strip())
        return lines

    def _find_money_in_line(self, line: str):
        # Match currency amounts like $1,234,000 or 1,234,000 or (1,234) or 1.23 billion
        m = re.search(r"(\(?\$?[\d{1,3},]+(?:\.\d+)?\)?(?:\s*(million|billion|m|bn|b))?)", line, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
        # try numbers with decimals without commas
        m2 = re.search(r"(\(?\$?[\d]+(?:\.\d+)?\)?)", line)
        if m2:
            return m2.group(1).strip()
        return None

    def _normalize_number(self, s: str):
        if not s:
            return None
        s = s.replace("$", "").replace("(", "-").replace(")", "").replace(",", "").strip()
        s_lower = s.lower()
        multiplier = 1.0
        if "billion" in s_lower or re.search(r"\bbn\b", s_lower) or re.search(r"\bb\b", s_lower):
            multiplier = 1_000_000_000.0
            s = re.sub(r"(?i)(billion|bn|\bb\b)", "", s)
        elif "million" in s_lower or re.search(r"\bm\b", s_lower):
            multiplier = 1_000_000.0
            s = re.sub(r"(?i)(million|m)", "", s)
        try:
            num = float(s)
            return num * multiplier
        except Exception:
            # fallback: cannot parse
            return s.strip()

    def run(self, payload: Dict[str, Any], tools: list):
        file_path = payload.get("file_path")
        query = payload.get("query")
        text = _get_text_from_tools(tools, file_path)
        result = {
            "summary": "",
            "key_metrics": {},
            "computed_changes": {},
            "assumptions_and_missing_data": []
        }

        if not text or text.startswith("❌") or text.startswith("⚠️"):
            result["summary"] = f"Could not extract document text. Reader output: {text[:200]}"
            return result

        # Build a short evidence-based summary: find first paragraph mentioning revenue/earnings or 'earnings release'
        summary_paragraph = None
        for paragraph in text.split("\n\n"):
            if re.search(r"(revenue|net income|earnings|operating income|eps|earnings per share)", paragraph, flags=re.IGNORECASE):
                summary_paragraph = paragraph.strip()
                break
        if summary_paragraph:
            # shorten to 2-4 sentences
            sentences = re.split(r'(?<=[.!?])\s+', summary_paragraph)
            result["summary"] = " ".join(sentences[:3])
        else:
            result["summary"] = "No explicit revenue/earnings paragraph found in the extracted text."

        # Extract metrics by scanning lines for keywords
        metrics_to_search = ["Revenue", "Net income", "Operating income", "EPS", "Earnings per share", "Total assets", "Total liabilities", "Gross profit"]
        metric_lines = self._extract_metric_lines(text, metrics_to_search)

        for ln in metric_lines:
            # Identify metric name in line
            name_match = re.search(r"(Revenue|Net income|Operating income|EPS|Earnings per share|Total assets|Total liabilities|Gross profit)", ln, flags=re.IGNORECASE)
            if not name_match:
                continue
            metric_name = name_match.group(1).strip()
            val_str = self._find_money_in_line(ln)
            normalized = self._normalize_number(val_str) if val_str else None
            result["key_metrics"][metric_name] = {"value": normalized if normalized is not None else val_str, "period": None, "source_line": ln}

        # Compute simple YoY changes if both current and prior found (very heuristic)
        # Search for pairs like "2024" and "2025" numbers in same line or adjacent lines
        # Very basic: find lines that include a year and a number
        year_num_pattern = re.compile(r"(\b(20\d{2})\b)[^\n\$]{0,50}(\$?[\d,]+(?:\.\d+)?)", flags=re.IGNORECASE)
        year_values = {}
        for ln in text.splitlines():
            m = year_num_pattern.search(ln)
            if m:
                year = m.group(2)
                num = m.group(3).replace("$", "").replace(",", "")
                try:
                    year_values.setdefault(year, []).append(float(num))
                except Exception:
                    pass
        if year_values:
            # pick two most recent years if available
            years_sorted = sorted(year_values.keys(), reverse=True)
            if len(years_sorted) >= 2:
                y_new, y_old = years_sorted[0], years_sorted[1]
                try:
                    v_new = sum(year_values[y_new]) / len(year_values[y_new])
                    v_old = sum(year_values[y_old]) / len(year_values[y_old])
                    if v_old != 0:
                        change_pct = ((v_new - v_old) / abs(v_old)) * 100.0
                        result["computed_changes"]["sample_yearly_number_avg"] = {"from_period": y_old, "to_period": y_new, "change_pct": round(change_pct, 2)}
                except Exception:
                    pass

        # If no key metrics found, note that extraction is incomplete
        if not result["key_metrics"]:
            result["assumptions_and_missing_data"].append("No explicit metric lines matched common keywords (Revenue, Net income, EPS, etc.). Document may use tables/images or non-standard phrasing.")

        return result


# Instances exported for task.py
verifier = VerifierAgent()
financial_analyst = FinancialAnalystAgent()
