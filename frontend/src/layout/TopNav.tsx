type Props = { onToggleSide: () => void };

export default function TopNav({ onToggleSide }: Props) {
  return (
    <header className="sticky top-0 z-40 bg-gray-700 text-white">
      <div className="mx-auto max-w-7xl px-4 h-12 flex items-center gap-3">
        <button onClick={onToggleSide} aria-label="Toggle menu" className="p-2 rounded hover:bg-gray-600">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeWidth="2" d="M3 6h18M3 12h18M3 18h18" />
          </svg>
        </button>
        <div className="font-semibold tracking-wide">NSCP 2015 : Structural Calculator</div>
      </div>
    </header>
  );
}
