# task.py
"""
Task definitions for financial document analysis using CrewAI Tasks.
Each Task references an agent and uses the read_data_tool to parse PDF text.
"""

from crewai import Task
from agents import financial_analyst, verifier
from tools import read_data_tool

# 1) Analyze financial document
analyze_financial_document = Task(
    name="analyze_financial_document",
    description=(
        "Analyze the given financial document, extract key metrics, ratios, and provide insights. "
        "Use read_data_tool to parse the document text."
    ),
    expected_output=(
        "A structured summary including:\n"
        "- Key metrics (Revenue, Operating Income, Net Income, EPS)\n"
        "- Ratios (Gross Margin, Operating Margin, Net Margin, YoY revenue)\n"
        "- Caveats and missing data\n"
        "- 3–5 follow-up questions"
    ),
    agent=financial_analyst,
    tools=[read_data_tool],
    async_execution=False,
)

# 2) Investment analysis (non-advisory)
investment_analysis = Task(
    name="investment_analysis",
    description=(
        "Based on extracted financial data, analyze potential investment opportunities. "
        "Highlight strengths, weaknesses, and possible implications for investors."
    ),
    expected_output=(
        "- List 3–5 investment insights\n"
        "- Identify at least 2 risks and 2 opportunities\n"
        "- Provide actionable recommendations (buy/sell/hold)"
    ),
    agent=financial_analyst,
    tools=[read_data_tool],
    async_execution=False,
)

# 3) Risk assessment
risk_assessment = Task(
    name="risk_assessment",
    description=(
        "Assess risks from the financial document. Identify financial, operational, and market risks. "
        "Highlight uncertainties or missing data that could impact reliability of the document."
    ),
    expected_output=(
        "- Bullet list of key risks\n"
        "- Each risk tagged with severity (low/medium/high)\n"
        "- Suggest 2–3 mitigation strategies"
    ),
    agent=financial_analyst,
    tools=[read_data_tool],
    async_execution=False,
)

# 4) Verify document type
verification = Task(
    name="verification",
    description=(
        "Verify whether the given file is a financial report. "
        "Extract title, reporting period/date, and section headers if possible."
    ),
    expected_output=(
        "Metadata about the document: title, reporting period, section headers. "
        "If unsure, state uncertainty."
    ),
    agent=verifier,  # ✅ use verifier, not analyst
    tools=[read_data_tool],
    async_execution=False,
)
