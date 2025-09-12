import { useRef } from "react";
import type { CatalogItem } from "../types";
import { Link } from "react-router-dom";

type Props = { items: CatalogItem[] };

export default function CalcCarousel({ items }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const scrollBy = (dx: number) => ref.current?.scrollBy({ left: dx, behavior: "smooth" });

  return (
    <div className="relative max-w-5xl mx-auto">
      <button onClick={() => scrollBy(-320)} className="absolute -left-3 top-1/2 -translate-y-1/2 p-2 rounded bg-gray-600 text-white">
        ‹
      </button>
      <div ref={ref} className="flex gap-4 overflow-x-auto no-scrollbar snap-x">
        {items.map((it) => (
          <div key={it.slug} className="snap-start shrink-0 w-72 rounded-2xl bg-gray-200 p-4 shadow">
            <div className="text-lg font-semibold mb-6">{it.name}</div>
            <Link
              to={it.slug === "beams" ? "/beams" : `/${it.slug}`}
              className="inline-block px-4 py-2 rounded-xl bg-gray-900 text-white"
            >
              Try Now
            </Link>
          </div>
        ))}
      </div>
      <button onClick={() => scrollBy(320)} className="absolute -right-3 top-1/2 -translate-y-1/2 p-2 rounded bg-gray-600 text-white">
        ›
      </button>
    </div>
  );
}
