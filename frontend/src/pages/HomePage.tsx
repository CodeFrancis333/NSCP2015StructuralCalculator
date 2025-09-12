import type { CatalogItem } from "../types";
import VideoCard from "../components/VideoCard";
import CalcCarousel from "../components/CalcCarousel";

export default function HomePage({ items }: { items: CatalogItem[] }) {
  return (
    <div className="space-y-8">
      <div className="text-center px-2">
        <div className="text-3xl font-semibold">featuring our <span className="italic font-black">FREE</span></div>
        <div className="opacity-70">NSCP 2015 Structural Engineering Calculators</div>
      </div>
      <VideoCard />
      <CalcCarousel items={items} />
    </div>
  );
}
