"""
AIVOA Complaint Extraction Agent
"""

import os
import re
import json
from typing import TypedDict, Optional

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

load_dotenv()


class ComplaintState(TypedDict):
    raw_text: str
    extracted: Optional[dict]
    risk_assessment: Optional[dict]
    capa: Optional[dict]


llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
)


def parse_json_response(text: str) -> dict:
    """Robustly extract a JSON object from a model response, even if
    it's wrapped in markdown fences or has extra commentary around it."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


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


def extract_node(state: ComplaintState) -> ComplaintState:
    prompt = EXTRACTION_PROMPT.format(text=state["raw_text"])
    response = llm.invoke(prompt)
    state["extracted"] = parse_json_response(response.content)
    return state


def risk_node(state: ComplaintState) -> ComplaintState:
    prompt = RISK_PROMPT.format(data=json.dumps(state["extracted"]))
    response = llm.invoke(prompt)
    state["risk_assessment"] = parse_json_response(response.content)
    return state


def capa_node(state: ComplaintState) -> ComplaintState:
    prompt = CAPA_PROMPT.format(
        data=json.dumps(state["extracted"]),
        risk=json.dumps(state["risk_assessment"]),
    )
    response = llm.invoke(prompt)
    state["capa"] = parse_json_response(response.content)
    return state


graph = StateGraph(ComplaintState)
graph.add_node("extract", extract_node)
graph.add_node("risk", risk_node)
graph.add_node("generate_capa", capa_node)
graph.set_entry_point("extract")
graph.add_edge("extract", "risk")
graph.add_edge("risk", "generate_capa")
graph.add_edge("generate_capa", END)

complaint_graph = graph.compile()


def run_complaint_pipeline(raw_text: str) -> dict:
    result = complaint_graph.invoke(
        {"raw_text": raw_text, "extracted": None, "risk_assessment": None, "capa": None}
    )
    return {
        "extracted": result["extracted"],
        "risk_assessment": result["risk_assessment"],
        "capa": result["capa"],
    }


if __name__ == "__main__":
    sample = """Apollo Pharmacy reported discolored capsules in Amoxicillin
    Capsules 500 mg. Batch number AMX240602. Manufacturing date March 2026.
    Expiry date February 2028. 12 capsules affected."""
    output = run_complaint_pipeline(sample)
    print(json.dumps(output, indent=2))
