"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
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
  icon: string;
}

const navCards: NavCard[] = [
  {
    title: "Biblioteca",
    description: "Gestiona tus libros y copias",
    href: "/library",
    icon: "📚",
  },
  {
    title: "Grupos",
    description: "Grupos familiares y compartidos",
    href: "/groups",
    icon: "👥",
  },
  {
    title: "Selección de lectura",
    description: "Sorteo aleatorio de libros",
    href: "/selection",
    icon: "🎲",
  },
  {
    title: "Clubes",
    description: "Clubes de lectura comunitarios",
    href: "/clubs",
    icon: "📖",
  },
  {
    title: "Reseñas",
    description: "Opiniones y valoraciones",
    href: "/reviews",
    icon: "⭐",
  },
  {
    title: "Configuración",
    description: "Privacidad y ajustes de cuenta",
    href: "/settings",
    icon: "⚙️",
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
      <main className="md:ml-64 pb-20 md:pb-0 min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Greeting */}
          <h1 className="text-2xl font-bold text-gray-900 mb-6">
            Hola, {user?.name || "Usuario"}
          </h1>

          {/* Book count summary */}
          {loading ? (
            <div className="mb-8">
              <Skeleton variant="card" count={1} />
            </div>
          ) : (
            <div className="mb-8 rounded-lg bg-white p-6 shadow-sm border border-gray-200">
              <p className="text-sm text-gray-500">Tu biblioteca</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">
                {bookCount} {bookCount === 1 ? "libro" : "libros"}
              </p>
            </div>
          )}

          {/* Navigation cards grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {navCards.map((card) => (
              <Link
                key={card.href}
                href={card.href}
                className="rounded-lg bg-white p-5 shadow-sm border border-gray-200 hover:shadow-md hover:border-gray-300 transition-all"
              >
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-2xl" aria-hidden="true">
                    {card.icon}
                  </span>
                  <h2 className="text-lg font-semibold text-gray-900">
                    {card.title}
                  </h2>
                </div>
                <p className="text-sm text-gray-500">{card.description}</p>
              </Link>
            ))}
          </div>
        </div>
      </main>
    </ProtectedRoute>
  );
}
