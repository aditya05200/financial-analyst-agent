# 📊 Financial Document Analyzer  

A FastAPI-based service that analyzes financial PDF reports using AI-powered agents.  

## 🚀 Features  
- ✅ Detects if the uploaded file is a financial report  
- 📑 Extracts structured financial observations and metrics  
- 🛠️ Uses a reliable PDF reader (PyPDF2)  
- 🔑 Supports both **CrewAI** and **OpenAI** API keys for LLM analysis  
- ⚡ Provides JSON responses with extracted insights  

---

## 📂 Project Structure  
```bash
.
├── main.py # FastAPI entry point
├── agents.py # AI agents configuration
├── task.py # Tasks & analysis logic
├── tools.py # PDF reading tools
├── requirements.txt # Dependencies
├── README.md # Documentation
└── data/ # Sample or uploaded files


---
```
## 🛠️ Installation  

```bash
# Clone the repo
git clone https://github.com/aditya05200/financial-doc-analyzer.git
cd financial-doc-analyzer

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows use venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

```
## ⚙️ Environment Setup
```bash
Create a .env file in the project root:

# Option 1: CrewAI
CREWAI_API_KEY=your_crewai_key
CREWAI_MODEL=gpt-4o

# Option 2: OpenAI (through CrewAI wrapper)
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o
```
