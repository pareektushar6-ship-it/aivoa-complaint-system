"""
AIVOA Complaint Extraction Agent
--------------------------------
A minimal LangGraph graph with a single node that:
  1. Takes raw complaint text (pasted email / OCR'd PDF text / manual text)
  2. Asks the Groq LLM (gemma2-9b-it) to extract structured fields
  3. Returns clean JSON matching the "Log Customer Complaint" form fields

Run standalone for testing:
    python langgraph_agent.py
"""

import os
import json
from typing import TypedDict, Optional

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

load_dotenv()

# ---------------------------------------------------------------------------
# 1. Define the shared state that flows through the graph
# ---------------------------------------------------------------------------
class ComplaintState(TypedDict):
    raw_text: str
    extracted: Optional[dict]
    risk_assessment: Optional[dict]
    capa: Optional[dict]


# ---------------------------------------------------------------------------
# 2. Set up the LLM
# ---------------------------------------------------------------------------
llm = ChatGroq(
    model="gemma2-9b-it",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
)

EXTRACTION_PROMPT = """You are a pharmaceutical QMS assistant. Extract structured
complaint data from the customer complaint text below.

Return ONLY valid JSON (no markdown, no commentary) with exactly these keys:
{{
  "complaint_source": "",
  "customer_name": "",
  "product_name": "",
  "product_strength": "",
  "batch_number": "",
  "affected_quantity": "",
  "manufacturing_date": "",
  "expiry_date": "",
  "originating_site_block": "",
  "impacted_npm": "",
  "defect_summary": ""
}}

If a field is not mentioned in the text, use an empty string "".

Complaint text:
\"\"\"{text}\"\"\"
"""

RISK_PROMPT = """Based on this structured pharmaceutical complaint, classify the
risk level and give a one-sentence justification. Return ONLY valid JSON:
{{
  "risk_level": "Low | Medium | High",
  "justification": ""
}}

Complaint data:
{data}
"""

CAPA_PROMPT = """You are a pharmaceutical QMS assistant. Based on the structured
complaint data and risk assessment below, suggest a brief Corrective and
Preventive Action (CAPA) recommendation, as would be logged in a QMS.

Return ONLY valid JSON with exactly these keys:
{{
  "root_cause_hypothesis": "",
  "corrective_action": "",
  "preventive_action": ""
}}

Keep each value to 1-2 sentences.

Complaint data:
{data}

Risk assessment:
{risk}
"""


# ---------------------------------------------------------------------------
# 3. Define graph nodes
# ---------------------------------------------------------------------------
def extract_node(state: ComplaintState) -> ComplaintState:
    prompt = EXTRACTION_PROMPT.format(text=state["raw_text"])
    response = llm.invoke(prompt)
    try:
        data = json.loads(response.content)
    except json.JSONDecodeError:
        # Fallback: try to strip code fences if the model added them anyway
        cleaned = response.content.strip().strip("`").replace("json\n", "", 1)
        data = json.loads(cleaned)
    state["extracted"] = data
    return state


def risk_node(state: ComplaintState) -> ComplaintState:
    prompt = RISK_PROMPT.format(data=json.dumps(state["extracted"]))
    response = llm.invoke(prompt)
    try:
        risk = json.loads(response.content)
    except json.JSONDecodeError:
        cleaned = response.content.strip().strip("`").replace("json\n", "", 1)
        risk = json.loads(cleaned)
    state["risk_assessment"] = risk
    return state


def capa_node(state: ComplaintState) -> ComplaintState:
    """Bonus feature: CAPA (Corrective and Preventive Action) recommendation."""
    prompt = CAPA_PROMPT.format(
        data=json.dumps(state["extracted"]),
        risk=json.dumps(state["risk_assessment"]),
    )
    response = llm.invoke(prompt)
    try:
        capa = json.loads(response.content)
    except json.JSONDecodeError:
        cleaned = response.content.strip().strip("`").replace("json\n", "", 1)
        capa = json.loads(cleaned)
    state["capa"] = capa
    return state


# ---------------------------------------------------------------------------
# 4. Wire up the graph: extract -> risk -> capa -> end
# ---------------------------------------------------------------------------
graph = StateGraph(ComplaintState)
graph.add_node("extract", extract_node)
graph.add_node("risk", risk_node)
graph.add_node("capa", capa_node)
graph.set_entry_point("extract")
graph.add_edge("extract", "risk")
graph.add_edge("risk", "capa")
graph.add_edge("capa", END)

complaint_graph = graph.compile()


def run_complaint_pipeline(raw_text: str) -> dict:
    """Convenience wrapper used by FastAPI."""
    result = complaint_graph.invoke(
        {"raw_text": raw_text, "extracted": None, "risk_assessment": None, "capa": None}
    )
    return {
        "extracted": result["extracted"],
        "risk_assessment": result["risk_assessment"],
        "capa": result["capa"],
    }


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sample = """Apollo Pharmacy reported discolored capsules in Amoxicillin
    Capsules 500 mg. Batch number AMX240602. Manufacturing date March 2026.
    Expiry date February 2028. 12 capsules affected. Please log this complaint."""

    output = run_complaint_pipeline(sample)
    print(json.dumps(output, indent=2))
