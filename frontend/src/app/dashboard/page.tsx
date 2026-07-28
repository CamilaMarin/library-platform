"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  BookMarked,
  Users,
  Shuffle,
  BookOpen,
  Star,
  Settings,
} from "lucide-react";
import { ProtectedRoute } from "@/components/protected-route";
import { Navigation } from "@/components/navigation";
import { Skeleton } from "@/components/skeleton";
import { useAuth } from "@/context/auth-context";
import { apiGet } from "@/lib/api-client";
import type { Book } from "@/types";

interface NavCard {
  title: string;
  description: string;
  href: string;
  icon: React.ReactNode;
}

const navCards: NavCard[] = [
  {
    title: "Biblioteca",
    description: "Gestiona tus libros y copias",
    href: "/library",
    icon: <BookMarked size={22} />,
  },
  {
    title: "Grupos",
    description: "Grupos familiares y compartidos",
    href: "/groups",
    icon: <Users size={22} />,
  },
  {
    title: "Selección de lectura",
    description: "Sorteo aleatorio de libros",
    href: "/selection",
    icon: <Shuffle size={22} />,
  },
  {
    title: "Clubes",
    description: "Clubes de lectura comunitarios",
    href: "/clubs",
    icon: <BookOpen size={22} />,
  },
  {
    title: "Reseñas",
    description: "Opiniones y valoraciones",
    href: "/reviews",
    icon: <Star size={22} />,
  },
  {
    title: "Configuración",
    description: "Privacidad y ajustes de cuenta",
    href: "/settings",
    icon: <Settings size={22} />,
  },
];

export default function DashboardPage() {
  const { user } = useAuth();
  const [bookCount, setBookCount] = useState<number>(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchBookCount() {
      try {
        const books = await apiGet<Book[]>("/books");
        setBookCount(books.length);
      } catch {
        setBookCount(0);
      } finally {
        setLoading(false);
      }
    }

    fetchBookCount();
  }, []);

  return (
    <ProtectedRoute>
      <Navigation />
      <main
        className="md:ml-64 pb-20 md:pb-0 min-h-screen"
        style={{ background: "var(--color-parchment)" }}
      >
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Greeting */}
          <h1
            className="text-2xl font-bold mb-6"
            style={{
              fontFamily: "var(--font-playfair), Georgia, serif",
              color: "var(--color-walnut)",
            }}
          >
            Hola, {user?.name || "Usuario"}
          </h1>

          {/* Book count summary */}
          {loading ? (
            <div className="mb-8">
              <Skeleton variant="card" count={1} />
            </div>
          ) : (
            <div
              className="mb-8 rounded-lg p-6"
              style={{
                background: "var(--color-cream)",
                border: "1px solid var(--color-border)",
                boxShadow: "0 1px 3px rgba(28, 16, 8, 0.08)",
              }}
            >
              <p
                className="text-sm"
                style={{ color: "var(--color-ink-faint)" }}
              >
                Tu biblioteca
              </p>
              <p
                className="text-3xl font-bold mt-1"
                style={{
                  fontFamily: "var(--font-playfair), Georgia, serif",
                  color: "var(--color-walnut)",
                }}
              >
                {bookCount}{" "}
                <span
                  className="text-lg font-normal"
                  style={{ color: "var(--color-ink-soft)" }}
                >
                  {bookCount === 1 ? "libro" : "libros"}
                </span>
              </p>
            </div>
          )}

          {/* Navigation cards grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {navCards.map((card) => (
              <Link
                key={card.href}
                href={card.href}
                className="block rounded-lg p-5 transition-all"
                style={{
                  background: "var(--color-cream)",
                  border: "1px solid var(--color-border)",
                  boxShadow: "0 1px 3px rgba(28, 16, 8, 0.08)",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLAnchorElement).style.boxShadow =
                    "0 4px 12px -2px rgba(28, 16, 8, 0.16)";
                  (e.currentTarget as HTMLAnchorElement).style.borderColor =
                    "var(--color-teak)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLAnchorElement).style.boxShadow =
                    "0 1px 3px rgba(28, 16, 8, 0.08)";
                  (e.currentTarget as HTMLAnchorElement).style.borderColor =
                    "var(--color-border)";
                }}
              >
                <div className="flex items-center gap-3 mb-2">
                  <span
                    aria-hidden="true"
                    style={{ color: "var(--color-teak)" }}
                  >
                    {card.icon}
                  </span>
                  <h2
                    className="text-base font-semibold"
                    style={{ color: "var(--color-walnut)" }}
                  >
                    {card.title}
                  </h2>
                </div>
                <p
                  className="text-sm"
                  style={{ color: "var(--color-ink-faint)" }}
                >
                  {card.description}
                </p>
              </Link>
            ))}
          </div>
        </div>
      </main>
    </ProtectedRoute>
  );
}
