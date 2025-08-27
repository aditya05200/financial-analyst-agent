# Financial Document Analyzer — Debugged (AI Internship Assignment)

## Summary
This repo contains a simple FastAPI service that accepts a financial PDF and uses a CrewAI-based `Crew` of agents to:
- Verify whether the file is a financial report
- Extract structured financial observations and metrics

I fixed deterministic bugs, removed hallucination-prone prompts, implemented a working PDF reader tool, and added clear LLM wiring instructions.

## Main fixes & changes
1. **Broken PDF reader** -> Replaced with a synchronous, reliable PDF reader using `PyPDF2` (`tools.FinancialDocumentTool.read_data_tool`).
2. **Agent LLM wiring** -> Replaced `llm = llm` with explicit wiring. The project now supports `CREWAI_API_KEY` (preferred) or `OPENAI_API_KEY`.
3. **Unsafe/Noisy task prompts** -> Task descriptions and expectations were rewritten to be deterministic and to ask for structured outputs (metadata, metrics, ratios, observations).
4. **Input passing** -> `main.run_crew()` now passes `file_path` into `Crew.kickoff` so agents can read the uploaded file.
5. **Tool references** -> Fixed parameter names (`tools=[...]`) and ensured agents include the `FinancialDocumentTool.read_data_tool` reference.
6. **Robustness** -> Added file existence checks and cleaner error handling.

## Requirements
- Python 3.10+
- pip packages:
  - fastapi
  - uvicorn
  - python-dotenv
  - PyPDF2
  - crewai (if using CrewAI runtime)
  - crewai_tools (optional, only required if using Serper Dev search tool)

Install:
```bash
python -m pip install -r requirements.txt
# if you don't have requirements.txt:
python -m pip install fastapi uvicorn python-dotenv PyPDF2
Environment variables
Create a .env file with one of:

ini
Copy code
# For CrewAI (preferred)
CREWAI_API_KEY=your_crewaikey
CREWAI_MODEL=gpt-4o

# OR to use OpenAI via the CrewAI LLM wrapper (example)
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o
If no LLM key is provided, the API will still accept uploads and return text-extraction snippets — but agents won't generate LLM-powered analysis until an API key is set.

Run the server
bash
Copy code
uvicorn main:app --reload --port 8000
Test with your local PDF (example)
Upload via curl:

bash
Copy code
curl -F "file=@/path/to/TSLA-Q2-2025-Update.pdf" \
     -F "query=Please summarize Q2 financial highlights and key metrics" \
     http://localhost:8000/analyze
You should receive a JSON response including:

status, query, analysis (raw output from Crew), file_processed, and extracted_text_snippet.

How to evaluate
If you set CREWAI_API_KEY or OPENAI_API_KEY properly, the analysis returned will contain the agent outputs (verification + analysis).

If analysis is missing or blank, check the server logs for LLM initialization errors — usually caused by missing/invalid API key or missing crewai package.

Notes / Next steps (bonus ideas)
Add a queue worker (Celery + Redis) to handle concurrent document analysis and avoid blocking FastAPI threads.

Store results in a database (Postgres) and provide an endpoint to fetch historical analysis results.

Expand InvestmentTool and RiskTool with domain-specific logic for automated metrics extraction (balance sheet parsing, common-size statements, etc).