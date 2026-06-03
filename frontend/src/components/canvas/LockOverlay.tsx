import { Lock } from 'lucide-react'

export function LockOverlay() {
  return (
    <div className="absolute inset-0 flex items-center justify-center rounded bg-white/80">
      <Lock size={20} strokeWidth={1.5} className="text-[#a3a3a3]" />
    </div>
  )
}
