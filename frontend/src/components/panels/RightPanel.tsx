import { useState } from 'react'
import { useWorkspaceStore } from '../../store/workspaceStore'
import { AgentFeed } from './AgentFeed'
import { NodeDetails } from './NodeDetails'
import { NodeChat } from './NodeChat'
import { PersonaLens } from './PersonaLens'

type PanelMode = 'feed' | 'details' | 'chat' | 'persona'

export function RightPanel() {
  const { getSelectedNode } = useWorkspaceStore()
  const selectedNode = getSelectedNode()
  const [mode, setMode] = useState<PanelMode>('feed')

  return (
    <div className="flex h-full w-[340px] shrink-0 flex-col border-l border-[#e5e5e5] bg-white">
      {selectedNode && (
        <div className="flex border-b border-[#e5e5e5]">
          {(['feed', 'details', 'chat', 'persona'] as PanelMode[]).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`flex-1 py-2.5 text-[10px] font-medium uppercase tracking-wide ${
                mode === m
                  ? 'border-b-2 border-[#2563eb] text-[#171717]'
                  : 'text-[#737373] hover:text-[#171717]'
              }`}
            >
              {m}
            </button>
          ))}
        </div>
      )}
      <div className="flex-1 overflow-hidden">
        {mode === 'feed' && <AgentFeed />}
        {mode === 'details' && selectedNode && <NodeDetails node={selectedNode} />}
        {mode === 'chat' && selectedNode && <NodeChat node={selectedNode} />}
        {mode === 'persona' && selectedNode && <PersonaLens node={selectedNode} />}
      </div>
    </div>
  )
}
