"use client";

import { createPortal } from "react-dom";
import { useMemo } from "react";

import { useLeafletModules } from "@/hooks/useLeafletModules";
import { toLatLng } from "@/lib/map";
import type { Event } from "@/types/events";

type DivIconFactory = typeof import("leaflet")["divIcon"];

export interface EventDetailsModalProps {
  event: Event;
  onClose: () => void;
}

const MINIMAP_TILE = {
  url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
};

export function EventDetailsModal({ event, onClose }: EventDetailsModalProps) {
  const leaflet = useLeafletModules();
  const eventPosition = useMemo(() => toLatLng(event.location), [event.location]);

  if (typeof window === "undefined") {
    return null;
  }

  const content = (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4 py-8"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-3xl rounded-2xl bg-white p-6 shadow-2xl dark:bg-neutral-900"
        onClick={(event) => event.stopPropagation()}
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 flex h-9 w-9 items-center justify-center rounded-full border border-neutral-200 bg-white text-neutral-600 shadow-md transition-colors hover:bg-neutral-100 hover:text-neutral-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-200 dark:hover:bg-neutral-700 dark:hover:text-neutral-50 dark:focus-visible:ring-offset-neutral-900 cursor-pointer"
          aria-label="Close event details"
        >
          <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden>
            <path
              fillRule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </button>

        <div className="flex flex-col gap-6 md:flex-row">
          <div className="flex-1 space-y-4">
            <div className="flex items-start gap-3">
              <div className="text-4xl" aria-hidden>
                {event.emoji}
              </div>
              <div>
                <h2 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-50">
                  {event.name}
                </h2>
                <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-400">
                  Score {event.event_score}/10
                </p>
              </div>
            </div>
            <p className="text-sm leading-relaxed text-neutral-700 dark:text-neutral-300">
              {event.description}
            </p>
            {event.link ? (
              <a
                href={event.link}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex w-fit items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-sm font-medium text-blue-700 transition-colors hover:bg-blue-100 dark:border-blue-900/50 dark:bg-blue-950/40 dark:text-blue-300 dark:hover:bg-blue-900/40 cursor-pointer"
              >
                Visit link
                <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden>
                  <path d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" />
                </svg>
              </a>
            ) : null}
          </div>

          <div className="flex-1">
            {leaflet ? (
              <leaflet.MapContainer
                center={eventPosition}
                zoom={15}
                className="h-72 w-full rounded-xl"
                dragging={false}
                doubleClickZoom={false}
                scrollWheelZoom={false}
                attributionControl={false}
                zoomControl={false}
              >
                <leaflet.TileLayer
                  attribution={MINIMAP_TILE.attribution}
                  url={MINIMAP_TILE.url}
                />
                <leaflet.Marker
                  position={eventPosition}
                  icon={createEmojiIcon(leaflet.divIcon, event.emoji)}
                />
              </leaflet.MapContainer>
            ) : (
              <div className="flex h-72 w-full items-center justify-center rounded-xl border border-dashed border-neutral-300 text-neutral-500 dark:border-neutral-700 dark:text-neutral-400">
                Loading map...
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  return createPortal(content, document.body);
}

function createEmojiIcon(divIconFn: DivIconFactory, emoji: string) {
  return divIconFn({
    html: `<div style="font-size: 2rem; filter: drop-shadow(0 6px 12px rgba(0,0,0,0.25));">${emoji}</div>`,
    className: "",
    iconSize: [36, 36],
    iconAnchor: [18, 18],
  });
}
