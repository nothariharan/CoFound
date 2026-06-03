"""Tech-tree unlock logic — determines which nodes become visible."""

from graph.schema import BaseNode, NodeStatus, NodeType, status_from_confidence

UNLOCK_RULES: dict[NodeType, dict] = {
    NodeType.AUDIENCE: {"prerequisites": [NodeType.CORE_IDEA], "threshold": 70},
    NodeType.MARKET_INTELLIGENCE: {"prerequisites": [NodeType.CORE_IDEA], "threshold": 70},
    NodeType.COMPETITORS: {"prerequisites": [NodeType.CORE_IDEA], "threshold": 70},
    NodeType.REVENUE: {
        "prerequisites": [NodeType.AUDIENCE, NodeType.MARKET_INTELLIGENCE],
        "threshold": 70,
    },
    NodeType.PRODUCT_VISION: {
        "prerequisites": [NodeType.AUDIENCE, NodeType.MARKET_INTELLIGENCE],
        "threshold": 70,
    },
    NodeType.TECH_STACK: {
        "prerequisites": [NodeType.COMPETITORS, NodeType.CORE_IDEA],
        "threshold": 70,
    },
    NodeType.BUILD: {
        "prerequisites": [NodeType.REVENUE, NodeType.TECH_STACK],
        "threshold": 70,
    },
    NodeType.LAUNCH: {"prerequisites": [NodeType.BUILD], "threshold": 70},
    NodeType.OBSERVE: {"prerequisites": [NodeType.LAUNCH], "threshold": 0},
    NodeType.GROWTH: {"prerequisites": [NodeType.OBSERVE], "threshold": 0},
}


def get_node_by_type(nodes: list[BaseNode], node_type: NodeType) -> BaseNode | None:
    return next((n for n in nodes if n.type == node_type), None)


def prerequisites_met(nodes: list[BaseNode], node_type: NodeType) -> bool:
    rule = UNLOCK_RULES.get(node_type)
    if not rule:
        return True
    for prereq in rule["prerequisites"]:
        node = get_node_by_type(nodes, prereq)
        if not node or node.confidence < rule["threshold"]:
            return False
    return True


def compute_unlock_states(nodes: list[BaseNode]) -> list[BaseNode]:
    """Return nodes with updated locked/unlocked status."""
    updated: list[BaseNode] = []
    for node in nodes:
        if node.type == NodeType.CORE_IDEA:
            node.status = status_from_confidence(node.confidence)
            updated.append(node)
            continue
        if prerequisites_met(nodes, node.type):
            node.status = status_from_confidence(node.confidence)
        else:
            node.status = NodeStatus.LOCKED
        updated.append(node)
    return updated
