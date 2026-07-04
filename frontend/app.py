"""
Streamlit frontend for Local Economic Pulse Dashboard.
"""

import streamlit as st
import requests

# ---------------------------
# CONFIG
# ---------------------------
BACKEND_URL = "http://127.0.0.1:8000/ask"

st.set_page_config(
    page_title="Local Economic Pulse Dashboard",
    page_icon="📊",
    layout="centered"
)

# ---------------------------
# HEADER
# ---------------------------
st.title("📊 Local Economic Pulse Dashboard")
st.caption("Ask questions about local footfall and business activity in plain English.")

# ---------------------------
# SAMPLE QUESTIONS (sidebar)
# ---------------------------
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

# ---------------------------
# CHAT HISTORY (session state)
# ---------------------------
if "history" not in st.session_state:
    st.session_state["history"] = []

# ---------------------------
# INPUT
# ---------------------------
question = st.text_input(
    "Ask a question:",
    key="question_input",
    placeholder="e.g. Which sector had the highest footfall last week?"
)

ask_button = st.button("Ask", type="primary")

# ---------------------------
# HANDLE REQUEST
# ---------------------------
if ask_button and question.strip():
    with st.spinner("Analyzing data..."):
        try:
            response = requests.post(BACKEND_URL, json={"question": question}, timeout=60)

            if response.status_code == 200:
                data = response.json()
                st.session_state["history"].insert(0, data)
            else:
                st.error(f"Error: {response.json().get('detail', 'Unknown error')}")

        except requests.exceptions.ConnectionError:
            st.error("Could not connect to backend. Make sure the FastAPI server is running (uvicorn main:app --reload).")
        except Exception as e:
            st.error(f"Something went wrong: {str(e)}")

# ---------------------------
# DISPLAY RESULTS
# ---------------------------
for item in st.session_state["history"]:
    st.divider()
    st.subheader(f"❓ {item['question']}")

    # Insight
    st.markdown("**💡 Insight**")
    st.write(item["insight"])

    # Recommendation
    st.markdown("**✅ Recommendation**")
    st.write(item["recommendation"])

    # Why (explainability)
    with st.expander("🔍 Why this recommendation?"):
        st.write(item["why"])

    # Raw data
    with st.expander("📄 View data & SQL query"):
        st.code(item["sql_query"], language="sql")
        if item["result_rows"]:
            st.dataframe(item["result_rows"])
        else:
            st.write("No data returned.")