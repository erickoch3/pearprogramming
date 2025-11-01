import type { Event } from "@/types/events";
import { MapView } from "./MapView";

interface MapSectionProps {
  events: Event[];
}

export function MapSection({ events }: MapSectionProps) {
  return (
    <section className="flex-[2] h-full rounded-2xl border border-neutral-200/80 bg-white/80 backdrop-blur-sm p-2 shadow-xl shadow-neutral-200/50 dark:border-neutral-800/50 dark:bg-neutral-900/80 dark:shadow-black/20 transition-all hover:shadow-2xl hover:shadow-neutral-300/50 dark:hover:shadow-black/30 overflow-hidden">
      <MapView events={events} />
    </section>
  );
}
