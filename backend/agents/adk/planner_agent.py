"""adk planner agent — decomposes workspace state into research tasks"""
from __future__ import annotations

from google.adk.agents import Agent

from agents.adk.config import get_pro_model

PLANNER_INSTRUCTION = """You are CoFound's Planner agent.
Return ONLY JSON: {"tasks":[{"task":str,"type":node_type,"tools":[str],"priority":int}]}.
Create 6-10 focused research tasks. Use only these tools: reddit, scrapling, firecrawl, github.
Node types: audience, market_intelligence, competitors, revenue, product_vision, tech_stack.
"""

planner_agent = Agent(
    name="cofounder_planner",
    model=get_pro_model(),
    instruction=PLANNER_INSTRUCTION,
)
