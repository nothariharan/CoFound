"""Gemini-powered export file generation."""

from __future__ import annotations

from graph.schema import WorkspaceDocument
from llm.gemini import generate_pro


async def generate_export_files(workspace: WorkspaceDocument) -> dict[str, str]:
    context = workspace.model_dump(mode="json")
    base = _summaries(workspace)
    files = {
        "README.md": await _generate_or_fallback("README", context, _readme(workspace, base)),
        "tech_stack.md": await _generate_or_fallback("tech stack", context, _tech_stack(workspace, base)),
        "ui_spec.md": await _generate_or_fallback("UI spec", context, _ui_spec(workspace, base)),
        ".cursorrules": await _generate_or_fallback("Cursor rules", context, _cursor_rules(workspace, base)),
        "HANDOFF.md": await _generate_or_fallback("handoff", context, _handoff(workspace, base)),
    }
    return files


async def _generate_or_fallback(kind: str, context: dict, fallback: str) -> str:
    try:
        prompt = f"Generate {kind} for this startup workspace. Use real graph data, no placeholders.\n{context}"
        text = await generate_pro(prompt[:18000], system="You are an export agent creating concise handoff docs for builders.")
        return text if "Mock Gemini response" not in text else fallback
    except Exception:
        return fallback


def _summaries(workspace: WorkspaceDocument) -> str:
    lines = []
    for n in workspace.nodes:
        lines.append(f"- {n.type.value}: {n.confidence}% {n.status.value} — {n.summary or n.agent_notes}")
    return "\n".join(lines)


def _readme(workspace: WorkspaceDocument, base: str) -> str:
    return f"# {workspace.workspace_name}\n\n## Startup Graph Summary\n{base}\n\n## Next Step\nUse the highest-confidence audience and market evidence to build the smallest demo that validates willingness to pay.\n"


def _tech_stack(workspace: WorkspaceDocument, base: str) -> str:
    tech = next((n for n in workspace.nodes if n.type.value == "tech_stack"), None)
    return f"# Tech Stack\n\n{tech.agent_notes if tech else 'Recommended: FastAPI backend, React frontend, MongoDB graph persistence, SSE for agent events.'}\n\n## Graph Evidence\n{base}\n"


def _ui_spec(workspace: WorkspaceDocument, base: str) -> str:
    return f"# UI Spec\n\n- Graph-first dashboard with node confidence, source pills, and active agents.\n- Agent feed streams critique and progress events.\n- Export action appears once core graph nodes are validated.\n\n## Relevant Graph\n{base}\n"


def _cursor_rules(workspace: WorkspaceDocument, base: str) -> str:
    return f"Always preserve the startup graph contract. Use evidence-backed changes. Prioritize the validated audience, revenue, and product vision nodes for {workspace.workspace_name}.\n"


def _handoff(workspace: WorkspaceDocument, base: str) -> str:
    return f"# Handoff\n\nWorkspace ID: `{workspace.idea_id}`\n\n## Current State\n{base}\n\n## Build Order\n1. Validate audience with 3 interviews.\n2. Ship MVP wedge.\n3. Instrument activation funnel.\n4. Re-run Observe/Growth agents.\n"
