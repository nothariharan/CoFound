export function prerequisitesMet(
  nodes: { type: string; confidence: number }[],
  nodeType: string,
): boolean {
  const rules: Record<string, { prerequisites: string[]; threshold: number }> = {
    audience: { prerequisites: ['core_idea'], threshold: 70 },
    market_intelligence: { prerequisites: ['core_idea'], threshold: 70 },
    competitors: { prerequisites: ['core_idea'], threshold: 70 },
    revenue: { prerequisites: ['audience', 'market_intelligence'], threshold: 70 },
    product_vision: { prerequisites: ['audience', 'market_intelligence'], threshold: 70 },
    tech_stack: { prerequisites: ['competitors', 'core_idea'], threshold: 70 },
    build: { prerequisites: ['revenue', 'tech_stack'], threshold: 70 },
    launch: { prerequisites: ['build'], threshold: 70 },
    observe: { prerequisites: ['launch'], threshold: 0 },
    growth: { prerequisites: ['observe'], threshold: 0 },
  }

  const rule = rules[nodeType]
  if (!rule) return true

  return rule.prerequisites.every((prereq) => {
    const node = nodes.find((n) => n.type === prereq)
    return node && node.confidence >= rule.threshold
  })
}
