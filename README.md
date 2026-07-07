# 📊 Local Economic Pulse Dashboard 
An AI-powered Decision Intelligence Platform that helps city stakeholders, local businesses, and communities understand local economic activity through natural language — turning raw footfall and business data into clear insights and actionable recommendations.

---

## 🎯 Problem Statement

Modern communities generate large volumes of data — from foot traffic to business activity — but transforming this data into actionable insights remains a challenge for non-technical stakeholders. This project addresses that gap by letting anyone **ask a question in plain English** and receive a data-backed insight, a concrete recommendation, and a transparent explanation of *why*.

This directly supports the hackathon's focus areas of **tourism and local economic development**, **citizen engagement**, and **responsible, explainable AI**.

---

## ✨ Key Features

- **Natural Language Querying** — Ask questions like *"Which sector had the highest footfall last week?"* and get instant answers, no SQL knowledge needed.
- **AI-Generated Insights** — Gemini translates raw data into plain-language explanations.
- **Actionable Recommendations** — Every insight comes with a concrete, specific suggestion for stakeholders/businesses.
- **Explainability ("Why")** — Every recommendation includes the reasoning behind it, referencing the actual data points used.
- **Anomaly-aware dataset** — Synthetic data includes realistic events (festivals, road closures, weather disruptions) to demonstrate pattern detection.
- **Interactive Dashboard** — Simple chat-style UI built with Streamlit, with sample questions to get started quickly.

---

## 🏗️ Architecture
User Question (Natural Language)
↓
Streamlit Frontend
↓
FastAPI Backend
↓
Gemini API (NL → SQL)
↓
SQLite Database (footfall + business activity data)
↓
Gemini API (Insight + Recommendation + Explainability generation)
↓
Response rendered in Dashboard

**Note on cloud architecture:** This project was designed for Google Cloud (BigQuery + Cloud Run) to align with the hackathon's suggested tech stack. Due to a temporary GCP billing verification issue during the hackathon window, the working prototype uses **SQLite** as a drop-in replacement for BigQuery — the SQL logic, prompt design, and application architecture are identical and would migrate to BigQuery with no changes to core logic, only the database connection layer.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI (Python) |
| AI / LLM | Google Gemini API (gemini-2.5-flash) |
| Database | SQLite (designed for BigQuery) |
| Data | Synthetic footfall & business activity data (Python-generated) |

---

## 📁 Project Structure

local-economic-pulse/
├── backend/
│   ├── main.py                  # FastAPI app — orchestrates the full pipeline
│   ├── prompts/
│   │   ├── nl_to_sql.py         # Prompt template: NL question → SQL
│   │   └── insight_generation.py # Prompt template: data → insight/recommendation
│   └── test_gemini.py           # Standalone Gemini API connectivity test
├── data/
│   ├── generate_data.py         # Synthetic data generator
│   ├── load_to_sqlite.py        # Loads CSVs into SQLite database
│   ├── footfall_data.csv
│   ├── business_activity.csv
│   └── economic_pulse.db
├── frontend/
│   └── app.py                   # Streamlit dashboard UI
├── requirements.txt
└── README.md

---

## 🚀 Running Locally

1. Clone the repository:
```bash
git clone https://github.com/princekr-rajput/local-economic-pulse.git
cd local-economic-pulse
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

3. Add your Gemini API key to a `.env` file in the root directory:
GEMINI_API_KEY=your_api_key_here

4. Generate and load the data (if not already present):
```bash
python data/generate_data.py
python data/load_to_sqlite.py
```

5. Start the backend:
```bash
cd backend
uvicorn main:app --reload
```

6. In a new terminal, start the frontend:
```bash
cd frontend
streamlit run app.py
```

7. Open the app in your browser at `http://localhost:8501`

---

## 💡 Example Questions to Try

- "Which sector had the highest footfall last week?"
- "Is there any anomaly in Old Town's footfall?"
- "Compare footfall between Tech Park and College Road"
- "Which business type generates the most revenue in Market Street?"
- "What was the trend in Central Mall footfall over the last month?"

---

## 🔮 Future Scope

- Migrate from SQLite to BigQuery for production-scale data handling
- Deploy backend on Cloud Run for scalability
- Add real-time data ingestion from public APIs/open data sources
- Multi-turn conversational memory for follow-up questions
- Alerting system for detected anomalies

---
