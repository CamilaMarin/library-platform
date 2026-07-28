"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import {
  LayoutDashboard,
  BookMarked,
  Users,
  Shuffle,
  BookOpen,
  Star,
  ArrowLeftRight,
  Settings,
  LogOut,
} from "lucide-react";

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
}

const desktopNavItems: NavItem[] = [
  { label: "Dashboard",  href: "/dashboard", icon: <LayoutDashboard size={18} /> },
  { label: "Biblioteca", href: "/library",   icon: <BookMarked size={18} /> },
  { label: "Grupos",     href: "/groups",    icon: <Users size={18} /> },
  { label: "Selección",  href: "/selection", icon: <Shuffle size={18} /> },
  { label: "Clubes",     href: "/clubs",     icon: <BookOpen size={18} /> },
  { label: "Reseñas",    href: "/reviews",   icon: <Star size={18} /> },
  { label: "Préstamos",  href: "/loans",     icon: <ArrowLeftRight size={18} /> },
  { label: "Configuración", href: "/settings", icon: <Settings size={18} /> },
];

// Móvil: 5 items para que quepan cómodamente en pantallas pequeñas.
// Grupos y Selección quedan accesibles desde el sidebar desktop o desde el Dashboard.
const mobileNavItems: NavItem[] = [
  { label: "Inicio",     href: "/dashboard", icon: <LayoutDashboard size={20} /> },
  { label: "Biblioteca", href: "/library",   icon: <BookMarked size={20} /> },
  { label: "Clubes",     href: "/clubs",     icon: <BookOpen size={20} /> },
  { label: "Reseñas",    href: "/reviews",   icon: <Star size={20} /> },
  { label: "Ajustes",    href: "/settings",  icon: <Settings size={20} /> },
];

export function Navigation() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  function isActive(href: string): boolean {
    if (href === "/dashboard") return pathname === "/dashboard";
    return pathname.startsWith(href);
  }

  return (
    <>
      {/* ── Sidebar desktop ───────────────────────────────────────────── */}
      <nav
        aria-label="Navegación principal"
        className="hidden md:flex fixed left-0 top-0 h-full w-64 flex-col z-40"
        style={{ background: "var(--color-walnut)", borderRight: "1px solid var(--color-mahogany)" }}
      >
        {/* Logo */}
        <div
          className="px-6 py-5"
          style={{ borderBottom: "1px solid var(--color-mahogany)" }}
        >
          <h1
            className="text-xl font-bold tracking-tight"
            style={{ fontFamily: "var(--font-playfair), Georgia, serif", color: "var(--color-parchment)" }}
          >
            EntreLíneas
          </h1>
          <p className="mt-0.5 text-[11px] tracking-widest uppercase" style={{ color: "var(--color-brass)" }}>
            biblioteca familiar
          </p>
        </div>

        {/* Items */}
        <ul className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {desktopNavItems.map((item) => {
            const active = isActive(item.href);
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors"
                  style={
                    active
                      ? {
                          background: "var(--color-brass)",
                          color: "var(--color-walnut)",
                        }
                      : {
                          color: "var(--color-ink-faint)",
                        }
                  }
                  onMouseEnter={(e) => {
                    if (!active) {
                      (e.currentTarget as HTMLAnchorElement).style.background =
                        "var(--color-mahogany)";
                      (e.currentTarget as HTMLAnchorElement).style.color =
                        "var(--color-parchment)";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!active) {
                      (e.currentTarget as HTMLAnchorElement).style.background =
                        "transparent";
                      (e.currentTarget as HTMLAnchorElement).style.color =
                        "var(--color-ink-faint)";
                    }
                  }}
                >
                  <span aria-hidden="true">{item.icon}</span>
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>

        {/* Usuario */}
        <div
          className="px-4 py-4"
          style={{ borderTop: "1px solid var(--color-mahogany)" }}
        >
          <p
            className="text-sm font-medium truncate"
            style={{ color: "var(--color-parchment)" }}
          >
            {user?.name || "Usuario"}
          </p>
          <button
            onClick={logout}
            className="mt-2 flex items-center gap-1.5 text-sm transition-colors"
            style={{ color: "var(--color-ink-faint)" }}
            onMouseEnter={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.color =
                "var(--color-brass-lt)")
            }
            onMouseLeave={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.color =
                "var(--color-ink-faint)")
            }
          >
            <LogOut size={14} aria-hidden />
            Cerrar sesión
          </button>
        </div>
      </nav>

      {/* ── Barra móvil inferior ──────────────────────────────────────── */}
      <nav
        aria-label="Navegación móvil"
        className="md:hidden fixed bottom-0 left-0 right-0 z-40"
        style={{
          background: "var(--color-walnut)",
          borderTop: "1px solid var(--color-mahogany)",
        }}
      >
        <ul className="flex justify-around items-center h-16">
          {mobileNavItems.map((item) => {
            const active = isActive(item.href);
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className="flex flex-col items-center gap-0.5 px-2 py-1 text-[10px] font-medium transition-colors"
                  style={{
                    color: active
                      ? "var(--color-brass)"
                      : "var(--color-ink-faint)",
                  }}
                >
                  <span aria-hidden="true">{item.icon}</span>
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </>
  );
}
