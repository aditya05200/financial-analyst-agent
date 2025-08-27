# main.py
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
import os
import uuid

from crewai import Crew, Process
from agents import financial_analyst, verifier
from task import analyze_financial_document, verification
from tools import read_data_tool   # ✅ FIX: use the new tool, not FinancialDocumentTool

app = FastAPI(title="Financial Document Analyzer")

def run_crew(query: str, file_path: str):
    """Run the Crew with the financial analyst and verifier agents and pass file_path in the input."""
    financial_crew = Crew(
        agents=[verifier, financial_analyst],
        tasks=[verification, analyze_financial_document],
        process=Process.sequential,
    )

    input_payload = {'query': query, 'file_path': file_path}
    result = financial_crew.kickoff(input_payload)
    return result

@app.get("/")
async def root():
    return {"message": "Financial Document Analyzer API is running"}

@app.post("/analyze")
async def analyze_endpoint(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights")
):
    file_id = str(uuid.uuid4())
    os.makedirs("data", exist_ok=True)
    file_path = f"data/{file_id}_{file.filename}"

    try:
        # Save file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        if not query:
            query = "Analyze this financial document for investment insights"

        # Run the crew and include the saved file path
        response = run_crew(query=query.strip(), file_path=file_path)

        # Return an extracted snippet so user sees the tool read the PDF
        extracted_text = None
        try:
            extracted_text = read_data_tool(file_path)   # ✅ FIX: use new tool
        except Exception:
            extracted_text = None

        return {
            "status": "success",
            "query": query,
            "analysis": str(response),
            "file_processed": file.filename,
            "extracted_text_snippet": extracted_text[:1000] if extracted_text else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing financial document: {str(e)}")
    finally:
        # cleanup
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
