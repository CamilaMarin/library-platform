"use client";

interface SkeletonProps {
  variant?: "card" | "list" | "text";
  count?: number;
}

export function Skeleton({ variant = "text", count = 1 }: SkeletonProps) {
  const items = Array.from({ length: count }, (_, i) => i);

  const variantStyles: Record<string, string> = {
    text: "h-4 w-full rounded",
    list: "h-12 w-full rounded-md",
    card: "h-40 w-full rounded-lg",
  };

  return (
    <div className="flex flex-col gap-3" role="status" aria-label="Cargando contenido">
      {items.map((i) => (
        <div
          key={i}
          className={`animate-pulse bg-gray-200 ${variantStyles[variant]}`}
        />
      ))}
      <span className="sr-only">Cargando...</span>
    </div>
  );
}
