import { Lock } from 'lucide-react'

export function LockOverlay() {
  return (
    <div className="absolute inset-0 flex items-center justify-center rounded-lg bg-card/80">
      <Lock className="size-5 text-status-locked" strokeWidth={1.5} />
    </div>
  )
}
