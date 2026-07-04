"""
Streamlit app for Local Economic Pulse Dashboard.
Combines frontend + backend logic (Gemini + SQLite) into a single deployable app.
"""

import os
import re
import json
import sqlite3
import streamlit as st
from google import genai
from dotenv import load_dotenv

# ---------------------------
# SETUP
# ---------------------------
load_dotenv()

# Works both locally (.env) and on Streamlit Cloud (st.secrets)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", None)

if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY not found. Add it to your .env file (local) or Streamlit Secrets (cloud).")
    st.stop()

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "economic_pulse.db")

st.set_page_config(
    page_title="Local Economic Pulse Dashboard",
    page_icon="📊",
    layout="centered"
)

# ---------------------------
# PROMPTS
# ---------------------------
NL_TO_SQL_PROMPT = """You are a SQL expert helping analyze local economic data in a SQLite database.

You have access to two tables:

Table: footfall
Columns:
- date (TEXT, format YYYY-MM-DD)
- sector (TEXT) - locality/area name, one of: Market Street, Tech Park, Old Town, Riverside, College Road, Industrial Zone, Central Mall, Station Area
- footfall_count (INTEGER)
- day_of_week (TEXT)

Table: business_activity
Columns:
- date (TEXT, format YYYY-MM-DD)
- sector (TEXT) - same sector names as above
- business_type (TEXT) - one of: Retail, Food & Beverage, Grocery, Services, Entertainment, Healthcare
- estimated_transactions (INTEGER)
- estimated_revenue (REAL)

Rules:
1. Only generate SELECT queries. Never generate INSERT, UPDATE, DELETE, or DDL statements.
2. Use standard SQLite SQL syntax.
3. Dates are stored as TEXT in YYYY-MM-DD format; use SQLite date functions like date(), julianday() for date arithmetic.
4. If comparing time periods (e.g. "last week vs this week"), calculate ranges relative to the max date in the data using a subquery, not hardcoded dates.
5. Return ONLY the SQL query. No explanation, no markdown formatting, no backticks.
6. If the question is ambiguous, make a reasonable assumption and generate the best-guess query.

User question: {user_question}

SQL query:"""

INSIGHT_PROMPT = """You are an economic data analyst assistant helping city stakeholders and local businesses understand data.

User's original question: {user_question}

Query result (as data):
{query_result}

Based on this data, provide a response with exactly three parts:

1. INSIGHT: A clear, concise 2-3 sentence explanation of what this data shows, in plain language (no jargon).

2. RECOMMENDATION: One specific, actionable suggestion based on this insight. Be concrete (e.g. "consider extending evening hours" not "improve business").

3. WHY: A one-sentence explanation of the reasoning behind the recommendation, referencing the specific data points that led to it.

Format your response as plain text with these three labeled sections. Do not use markdown formatting or asterisks. Keep the entire response under 120 words."""


# ---------------------------
# HELPER FUNCTIONS
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
    return re.sub(r"```sql|```", "", raw_text).strip()


def run_query_on_sqlite(sql: str) -> list:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def parse_insight_response(raw_text: str) -> dict:
    insight, recommendation, why = "", "", ""
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


def process_question(user_question: str) -> dict:
    sql_prompt = NL_TO_SQL_PROMPT.format(user_question=user_question)
    sql_response = gemini_client.models.generate_content(model="gemini-2.5-flash", contents=sql_prompt)
    raw_sql = clean_sql_response(sql_response.text)

    if not is_safe_select_query(raw_sql):
        raise ValueError(f"Generated query failed safety check: {raw_sql}")

    result_rows = run_query_on_sqlite(raw_sql)
    result_rows_str = json.dumps(result_rows[:20], indent=2) if result_rows else "No data returned for this query."

    insight_prompt = INSIGHT_PROMPT.format(user_question=user_question, query_result=result_rows_str)
    insight_response = gemini_client.models.generate_content(model="gemini-2.5-flash", contents=insight_prompt)
    parsed = parse_insight_response(insight_response.text)

    return {
        "question": user_question,
        "sql_query": raw_sql,
        "result_rows": result_rows,
        "insight": parsed["insight"],
        "recommendation": parsed["recommendation"],
        "why": parsed["why"],
    }


# ---------------------------
# UI
# ---------------------------
st.title("📊 Local Economic Pulse Dashboard")
st.caption("Ask questions about local footfall and business activity in plain English.")

with st.sidebar:
    st.header("Try asking:")
    sample_questions = [
        "Which sector had the highest footfall last week?",
        "Is there any anomaly in Old Town's footfall?",
        "Compare footfall between Tech Park and College Road",
        "Which business type generates the most revenue in Market Street?",
        "What was the trend in Central Mall footfall over the last month?"
    ]
    for q in sample_questions:
        if st.button(q, use_container_width=True):
            st.session_state["question_input"] = q

if "history" not in st.session_state:
    st.session_state["history"] = []

question = st.text_input(
    "Ask a question:",
    key="question_input",
    placeholder="e.g. Which sector had the highest footfall last week?"
)

ask_button = st.button("Ask", type="primary")

if ask_button and question.strip():
    with st.spinner("Analyzing data..."):
        try:
            data = process_question(question)
            st.session_state["history"].insert(0, data)
        except Exception as e:
            st.error(f"Something went wrong: {str(e)}")

for item in st.session_state["history"]:
    st.divider()
    st.subheader(f"❓ {item['question']}")

    st.markdown("**💡 Insight**")
    st.write(item["insight"])

    st.markdown("**✅ Recommendation**")
    st.write(item["recommendation"])

    with st.expander("🔍 Why this recommendation?"):
        st.write(item["why"])

    with st.expander("📄 View data & SQL query"):
        st.code(item["sql_query"], language="sql")
        if item["result_rows"]:
            st.dataframe(item["result_rows"])
        else:
            st.write("No data returned.")