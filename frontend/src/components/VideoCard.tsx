export default function VideoCard() {
  return (
    <div className="rounded-2xl bg-gray-700 text-gray-200 p-4 shadow max-w-3xl mx-auto">
      <div className="mb-2 text-sm opacity-80">Beam Calculator</div>
      <div className="aspect-video rounded-xl bg-gray-600 flex items-center justify-center">
        {/* placeholder play icon */}
        <svg width="64" height="64" viewBox="0 0 24 24" fill="currentColor" className="opacity-70">
          <path d="M8 5v14l11-7z" />
        </svg>
      </div>
      <div className="text-center mt-4">
        <button className="px-4 py-2 rounded-xl bg-black/70 hover:bg-black transition text-white">Try Now</button>
      </div>
    </div>
  );
}
