import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import { Providers } from "./providers";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
  display: "swap",
  // Cargamos italic también — se usa en títulos de libros
  style: ["normal", "italic"],
});

export const metadata: Metadata = {
  title: "EntreLíneas",
  description: "Plataforma familiar de gestión de lectura",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" className={`${inter.variable} ${playfair.variable}`}>
      {/*
        bg-gray-50 reemplazado por el fondo parchment definido en globals.css.
        antialiased se mantiene igual.
      */}
      <body className="min-h-screen antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
