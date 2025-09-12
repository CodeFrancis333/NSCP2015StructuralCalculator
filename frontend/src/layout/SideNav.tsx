import { NavLink } from "react-router-dom";
import type { CatalogItem } from "../types";

type Props = { open: boolean; items: CatalogItem[]; onClose: () => void };

export default function SideNav({ open, items, onClose }: Props) {
  return (
    <>
      {/* drawer */}
      <aside
        className={`fixed inset-y-0 left-0 w-72 bg-gray-800 text-gray-100 shadow-lg transform transition-transform duration-200 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
        aria-hidden={!open}
      >
        <div className="p-4 border-b border-gray-700 font-semibold">Structural Calculators</div>
        <nav className="p-3 space-y-1 overflow-y-auto h-[calc(100%-48px)]">
          <NavLink
            to="/"
            className={({isActive}) => `block px-3 py-2 rounded ${isActive?'bg-gray-700 text-lime-300':'hover:bg-gray-700'}`}
            onClick={onClose}
          >
            Home
          </NavLink>
          {items.map(it => (
            <NavLink
              key={it.slug}
              to={it.slug === "beams" ? "/beams" : `/${it.slug}`}
              className={({isActive}) => `block px-3 py-2 rounded ${isActive?'bg-gray-700 text-lime-300':'hover:bg-gray-700'}`}
              onClick={onClose}
            >
              {it.name}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* dark overlay for click-to-close */}
      {open && <div className="fixed inset-0 bg-black/40" onClick={onClose} />}
    </>
  );
}
