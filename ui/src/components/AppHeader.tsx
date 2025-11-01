"use client";

import { useEffect, useState } from "react";

const FULL_TEXT = "It's a Beautiful Day.";
const TYPING_SPEED = 80; // milliseconds per character

export function AppHeader() {
  const [displayedText, setDisplayedText] = useState("");
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (currentIndex < FULL_TEXT.length) {
      const timeout = setTimeout(() => {
        setDisplayedText(FULL_TEXT.slice(0, currentIndex + 1));
        setCurrentIndex(currentIndex + 1);
      }, TYPING_SPEED);

      return () => clearTimeout(timeout);
    }
  }, [currentIndex]);

  return (
    <h1 className="text-4xl font-bold tracking-tight mb-20 bg-gradient-to-r from-neutral-900 to-neutral-700 dark:from-neutral-50 dark:to-neutral-300 bg-clip-text text-transparent min-h-[3rem]">
      {displayedText}
      {currentIndex < FULL_TEXT.length && (
        <span className="animate-pulse">|</span>
      )}
    </h1>
  );
}
