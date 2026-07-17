import { useEffect, useState, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { MousePointer2 } from 'lucide-react'
import { CursorLabel } from '@/components/cursor/CursorLabel'

const USER_CURSOR_COLOR = '#ffffff'
const USER_CURSOR_TEXT_COLOR = '#000000'

function useCustomCursorEnabled() {
  const [enabled] = useState(() => {
    const finePointer = window.matchMedia('(pointer: fine)').matches
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    return finePointer && !reducedMotion
  })

  return enabled
}

function GlobalAppCursor() {
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [active, setActive] = useState(false)

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      setPosition({ x: e.clientX, y: e.clientY })
      setActive(true)
    }
    const onLeave = () => setActive(false)

    document.addEventListener('mousemove', onMove, { passive: true })
    document.addEventListener('mouseleave', onLeave)
    document.body.classList.add('custom-cursor-active')

    return () => {
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseleave', onLeave)
      document.body.classList.remove('custom-cursor-active')
    }
  }, [])

  if (!active) return null

  return createPortal(
    <>
      <div
        className="pointer-events-none fixed z-[99999]"
        style={{
          left: position.x,
          top: position.y,
          transform: 'translate(-4px, -4px)',
        }}
        aria-hidden
      >
        <MousePointer2 className="fill-white stroke-black/20" size={28} />
      </div>
      <div
        className="pointer-events-none fixed z-[99998]"
        style={{
          left: position.x + 14,
          top: position.y + 16,
        }}
        aria-hidden
      >
        <CursorLabel
          label="You"
          color={USER_CURSOR_COLOR}
          textColor={USER_CURSOR_TEXT_COLOR}
          className="border-black/10"
        />
      </div>
    </>,
    document.body,
  )
}

export function AppCursorProvider({ children }: { children: ReactNode }) {
  const enabled = useCustomCursorEnabled()

  return (
    <>
      {children}
      {enabled && <GlobalAppCursor />}
    </>
  )
}
