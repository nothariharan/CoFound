interface NotificationBarProps {
  message?: string
}

export function NotificationBar({ message }: NotificationBarProps) {
  if (!message) return null

  return (
    <div className="shrink-0 border-b border-[#e5e5e5] bg-white px-4 py-2">
      <p className="text-xs text-[#737373]">{message}</p>
    </div>
  )
}
