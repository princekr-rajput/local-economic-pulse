"""
FastAPI backend for Local Economic Pulse Dashboard.
Pipeline: NL question -> Gemini (NL-to-SQL) -> SQLite execute -> Gemini (insight) -> response
"""

import os
import re
import json
import sqlite3

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv

from prompts.nl_to_sql import build_nl_to_sql_prompt
from prompts.insight_generation import build_insight_prompt

# ---------------------------
# SETUP
# ---------------------------
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in .env")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "economic_pulse.db")

app = FastAPI(title="Local Economic Pulse API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------
# REQUEST/RESPONSE MODELS
# ---------------------------
class QuestionRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    question: str
    sql_query: str
    result_rows: list
    insight: str
    recommendation: str
    why: str


# ---------------------------
# SAFETY CHECK
# ---------------------------
def is_safe_select_query(sql: str) -> bool:
    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "MERGE", "PRAGMA", "ATTACH"]
    sql_upper = sql.upper()
    if not sql_upper.strip().startswith("SELECT"):
        return False
    for keyword in forbidden:
        if keyword in sql_upper:
            return False
    return True


def clean_sql_response(raw_text: str) -> str:
    cleaned = re.sub(r"```sql|```", "", raw_text).strip()
    return cleaned


def run_query_on_sqlite(sql: str) -> list:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def parse_insight_response(raw_text: str) -> dict:
    insight = ""
    recommendation = ""
    why = ""

    insight_match = re.search(r"INSIGHT:\s*(.*?)(?=RECOMMENDATION:|$)", raw_text, re.DOTALL)
    rec_match = re.search(r"RECOMMENDATION:\s*(.*?)(?=WHY:|$)", raw_text, re.DOTALL)
    why_match = re.search(r"WHY:\s*(.*)", raw_text, re.DOTALL)

    if insight_match:
        insight = insight_match.group(1).strip()
    if rec_match:
        recommendation = rec_match.group(1).strip()
    if why_match:
        why = why_match.group(1).strip()

    return {"insight": insight, "recommendation": recommendation, "why": why}


# ---------------------------
# ROUTES
# ---------------------------
@app.get("/")
def root():
    return {"status": "ok", "message": "Local Economic Pulse API is running"}


@app.post("/ask", response_model=QueryResponse)
def ask_question(request: QuestionRequest):
    user_question = request.question.strip()

    if not user_question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Step 1: Generate SQL from natural language
    try:
        sql_prompt = build_nl_to_sql_prompt(user_question)
        sql_response = gemini_client.models.generate_content(
            model="gemini-2.5-flash", contents=sql_prompt
        )
        raw_sql = clean_sql_response(sql_response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini SQL generation failed: {str(e)}")

    # Step 2: Safety check
    if not is_safe_select_query(raw_sql):
        raise HTTPException(
            status_code=400,
            detail=f"Generated query failed safety check. Query was: {raw_sql}"
        )

    # Step 3: Execute on SQLite
    try:
        result_rows = run_query_on_sqlite(raw_sql)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SQLite execution failed: {str(e)}. Query: {raw_sql}")

    if not result_rows:
        result_rows_str = "No data returned for this query."
    else:
        result_rows_str = json.dumps(result_rows[:20], indent=2)

    # Step 4: Generate insight + recommendation
    try:
        insight_prompt = build_insight_prompt(user_question, result_rows_str)
        insight_response = gemini_client.models.generate_content(
            model="gemini-2.5-flash", contents=insight_prompt
        )
        parsed = parse_insight_response(insight_response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini insight generation failed: {str(e)}")

    return QueryResponse(
        question=user_question,
        sql_query=raw_sql,
        result_rows=result_rows,
        insight=parsed["insight"],
        recommendation=parsed["recommendation"],
        why=parsed["why"],
    )


# ---------------------------
# RUN LOCALLY
# ---------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)