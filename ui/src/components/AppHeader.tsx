"use client";

import { useCallback, useEffect, useRef, useState } from "react";

const TYPING_SPEED_MS = 80;
const FALLBACK_SENTENCE = "Make Today Remarkable";

type InspirationPayload = {
  sentence?: unknown;
};

type InspirationMetadata = {
  generatedAt?: string;
  model?: string | null;
  notes?: string;
};

export function AppHeader() {
  const [targetText, setTargetText] = useState("");
  const [displayedText, setDisplayedText] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [shouldAnimate, setShouldAnimate] = useState(true);
  const typingIndexRef = useRef(0);
  const typingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const hasAnimatedRef = useRef(false);

  const clearTypingTimer = useCallback(() => {
    if (typingTimeoutRef.current !== null) {
      clearTimeout(typingTimeoutRef.current);
      typingTimeoutRef.current = null;
    }
  }, []);

  const startTyping = useCallback(
    (text: string) => {
      clearTypingTimer();
      typingIndexRef.current = 0;
      setDisplayedText("");
      setIsTyping(true);

      const typeNext = () => {
        typingIndexRef.current += 1;
        setDisplayedText(text.slice(0, typingIndexRef.current));

        if (typingIndexRef.current < text.length) {
          typingTimeoutRef.current = setTimeout(typeNext, TYPING_SPEED_MS);
        } else {
          clearTypingTimer();
          setIsTyping(false);
        }
      };

      typingTimeoutRef.current = setTimeout(typeNext, TYPING_SPEED_MS);
    },
    [clearTypingTimer],
  );

  useEffect(() => {
    return () => {
      clearTypingTimer();
    };
  }, [clearTypingTimer]);

  useEffect(() => {
    const controller = new AbortController();

    void (async () => {
      try {
        const response = await fetch("/api/inspiration", {
          method: "GET",
          cache: "no-store",
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`Inspiration request failed (${response.status})`);
        }

        const payload = (await response.json()) as InspirationPayload & {
          metadata?: InspirationMetadata;
        };

        const normalized = normalizeSentence(payload.sentence) ?? FALLBACK_SENTENCE;
        setShouldAnimate(!hasAnimatedRef.current);
        if (!hasAnimatedRef.current) {
          hasAnimatedRef.current = true;
        }
        setTargetText(normalized);
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }

        console.error("Failed to load inspiration sentence", error);
        const sentence = FALLBACK_SENTENCE;
        setShouldAnimate(!hasAnimatedRef.current);
        if (!hasAnimatedRef.current) {
          hasAnimatedRef.current = true;
        }
        setTargetText(sentence);
      }
    })();

    return () => {
      if (!controller.signal.aborted) {
        controller.abort();
      }
    };
  }, []);

  useEffect(() => {
    if (!targetText) {
      clearTypingTimer();
      setDisplayedText("");
      setIsTyping(false);
      return;
    }

    if (shouldAnimate) {
      startTyping(targetText);
      return;
    }

    clearTypingTimer();
    typingIndexRef.current = targetText.length;
    setDisplayedText(targetText);
    setIsTyping(false);
  }, [targetText, shouldAnimate, clearTypingTimer, startTyping]);

  return (
    <h1 className="text-4xl font-bold tracking-tight mb-20 bg-gradient-to-r from-neutral-900 to-neutral-700 dark:from-neutral-50 dark:to-neutral-300 bg-clip-text text-transparent min-h-[3rem]">
      {displayedText}
      {isTyping && <span className="animate-pulse">|</span>}
    </h1>
  );
}

function normalizeSentence(value: unknown): string | null {
  if (typeof value !== "string") {
    return null;
  }

  const cleaned = value
    .split(/[\n\r]+/)[0]
    .replace(/^[\s"'“”‘’`]+/, "")
    .replace(/[\s"'“”‘’`]+$/, "")
    .replace(/\s+/g, " ")
    .trim();

  if (!cleaned) {
    return null;
  }

  const words = cleaned.split(" ").filter(Boolean);
  if (words.length < 3 || words.length > 7) {
    return null;
  }

  return cleaned;
}
