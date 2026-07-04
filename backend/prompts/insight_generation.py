"""
Prompt template for generating insights and recommendations from query results.
"""

INSIGHT_PROMPT = """You are an economic data analyst assistant helping city stakeholders and local businesses understand data.

User's original question: {user_question}

Query result (as data):
{query_result}

Based on this data, provide a response with exactly three parts:

1. INSIGHT: A clear, concise 2-3 sentence explanation of what this data shows, in plain language (no jargon).

2. RECOMMENDATION: One specific, actionable suggestion based on this insight. Be concrete (e.g. "consider extending evening hours" not "improve business").

3. WHY: A one-sentence explanation of the reasoning behind the recommendation, referencing the specific data points that led to it.

Format your response as plain text with these three labeled sections. Do not use markdown formatting or asterisks. Keep the entire response under 120 words."""


def build_insight_prompt(user_question: str, query_result: str) -> str:
    return INSIGHT_PROMPT.format(user_question=user_question, query_result=query_result)