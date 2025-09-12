import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { getCatalog } from "./api";
import type { CatalogItem } from "./types";
import TopNav from "./layout/TopNav";
import SideNav from "./layout/SideNav";
import HomePage from "./pages/HomePage";
import BeamPage from "./pages/BeamPage";

export default function App() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<CatalogItem[]>([]);
  useEffect(() => { getCatalog().then(setItems); }, []);
  const toggle = () => setOpen(v => !v);

  return (
    <BrowserRouter>
      <TopNav onToggleSide={toggle} />
      <SideNav open={open} items={items} onClose={() => setOpen(false)} />
      {/* content wrapper stays centered; no horizontal scroll */}
      <main className="relative mx-auto max-w-7xl px-4 py-6">
        <Routes>
          <Route path="/" element={<HomePage items={items} />} />
          <Route path="/beams" element={<BeamPage />} />
          <Route path="*" element={<div className="p-6">Coming soon.</div>} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}
