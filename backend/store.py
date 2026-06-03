"""In-memory workspace store — replaced by MongoDB Atlas in Day 1-2."""

from graph.schema import WorkspaceDocument

WORKSPACES: dict[str, WorkspaceDocument] = {}
