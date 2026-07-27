"use client";

import React, { useState } from "react";

interface StarRatingProps {
  value: number;
  onChange?: (rating: number) => void;
  readonly?: boolean;
}

export function StarRating({
  value,
  onChange,
  readonly = false,
}: StarRatingProps) {
  const [hoverValue, setHoverValue] = useState(0);

  const handleKeyDown = (e: React.KeyboardEvent, star: number) => {
    if (readonly || !onChange) return;

    if (e.key === "ArrowRight" || e.key === "ArrowUp") {
      e.preventDefault();
      const next = Math.min(star + 1, 5);
      onChange(next);
    } else if (e.key === "ArrowLeft" || e.key === "ArrowDown") {
      e.preventDefault();
      const prev = Math.max(star - 1, 1);
      onChange(prev);
    } else if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onChange(star);
    }
  };

  const displayValue = hoverValue || value;

  return (
    <div
      role="group"
      aria-label={`Calificación: ${value} de 5 estrellas`}
      className="flex items-center gap-1"
    >
      {[1, 2, 3, 4, 5].map((star) => {
        const isFilled = star <= displayValue;

        return (
          <button
            key={star}
            type="button"
            disabled={readonly}
            onClick={() => onChange?.(star)}
            onMouseEnter={() => !readonly && setHoverValue(star)}
            onMouseLeave={() => !readonly && setHoverValue(0)}
            onKeyDown={(e) => handleKeyDown(e, star)}
            aria-label={`${star} estrella${star > 1 ? "s" : ""}`}
            tabIndex={readonly ? -1 : star === value || (value === 0 && star === 1) ? 0 : -1}
            className={`text-2xl transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 rounded ${
              readonly ? "cursor-default" : "cursor-pointer"
            } ${isFilled ? "text-yellow-400" : "text-gray-300"}`}
          >
            {isFilled ? "★" : "☆"}
          </button>
        );
      })}
    </div>
  );
}
