"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/auth-context";

interface NavItem {
  label: string;
  href: string;
  icon: string;
}

const desktopNavItems: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: "🏠" },
  { label: "Biblioteca", href: "/library", icon: "📚" },
  { label: "Grupos", href: "/groups", icon: "👥" },
  { label: "Selección", href: "/selection", icon: "🎲" },
  { label: "Clubes", href: "/clubs", icon: "📖" },
  { label: "Reseñas", href: "/reviews", icon: "⭐" },
  { label: "Préstamos", href: "/loans", icon: "🔄" },
  { label: "Configuración", href: "/settings", icon: "⚙️" },
];

const mobileNavItems: NavItem[] = [
  { label: "Inicio", href: "/dashboard", icon: "🏠" },
  { label: "Biblioteca", href: "/library", icon: "📚" },
  { label: "Clubes", href: "/clubs", icon: "📖" },
  { label: "Reseñas", href: "/reviews", icon: "⭐" },
  { label: "Préstamos", href: "/loans", icon: "🔄" },
  { label: "Ajustes", href: "/settings", icon: "⚙️" },
];

export function Navigation() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  function isActive(href: string): boolean {
    if (href === "/dashboard") {
      return pathname === "/dashboard";
    }
    return pathname.startsWith(href);
  }

  return (
    <>
      {/* Desktop Sidebar */}
      <nav
        aria-label="Navegación principal"
        className="hidden md:flex fixed left-0 top-0 h-full w-64 flex-col border-r border-gray-200 bg-white z-40"
      >
        <div className="px-6 py-5 border-b border-gray-100">
          <h1 className="text-xl font-bold text-gray-900">EntreLíneas</h1>
        </div>

        <ul className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {desktopNavItems.map((item) => {
            const active = isActive(item.href);
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    active
                      ? "bg-blue-50 text-blue-700"
                      : "text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                  }`}
                >
                  <span className="text-lg" aria-hidden="true">
                    {item.icon}
                  </span>
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>

        <div className="px-4 py-4 border-t border-gray-200">
          <p className="text-sm font-medium text-gray-900 truncate">
            {user?.name || "Usuario"}
          </p>
          <button
            onClick={logout}
            className="mt-2 text-sm text-gray-500 hover:text-red-600 transition-colors"
          >
            Cerrar sesión
          </button>
        </div>
      </nav>

      {/* Mobile Bottom Bar */}
      <nav
        aria-label="Navegación móvil"
        className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-40"
      >
        <ul className="flex justify-around items-center h-16">
          {mobileNavItems.map((item) => {
            const active = isActive(item.href);
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={`flex flex-col items-center gap-0.5 px-2 py-1 text-xs transition-colors ${
                    active
                      ? "text-blue-600"
                      : "text-gray-500 hover:text-gray-700"
                  }`}
                >
                  <span className="text-lg" aria-hidden="true">
                    {item.icon}
                  </span>
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
