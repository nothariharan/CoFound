import { cn } from '@/lib/utils'

export function CursorLabel({
  label,
  color,
  textColor = '#ffffff',
  className,
}: {
  label: string
  color: string
  textColor?: string
  className?: string
}) {
  return (
    <div
      className={cn(
        'whitespace-nowrap rounded-md border border-white/10 px-2.5 py-1 text-xs font-medium shadow-md',
        className,
      )}
      style={{ backgroundColor: color, color: textColor }}
    >
      {label}
    </div>
  )
}

export function CursorPointerIcon({
  color,
  size = 24,
  className,
}: {
  color: string
  size?: number
  className?: string
}) {
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      className={cn('shrink-0 drop-shadow-sm', className)}
      aria-hidden
    >
      <path
        d="M5.5 3.21V20.8c0 .45.54.67.85.35l4.86-4.86a.5.5 0 0 1 .35-.15h6.87a.5.5 0 0 0 .35-.85L6.35 2.86a.5.5 0 0 0-.85.35Z"
        fill={color}
        stroke="rgba(255,255,255,0.15)"
        strokeWidth="1"
        strokeLinejoin="round"
      />
    </svg>
  )
}
