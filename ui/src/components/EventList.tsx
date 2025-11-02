import type { Event } from "@/types/events";
import type { ProgressUpdate } from "@/hooks/useStreamingEventRecommendations";
import { ProgressTracker } from "./ProgressTracker";

export interface EventListProps {
  events: Event[];
  loading: boolean;
  error?: string | null;
  progress?: ProgressUpdate | null;
  onSelectEvent?: (event: Event) => void;
}

export function EventList({ events, loading, error, progress, onSelectEvent }: EventListProps) {
  if (loading) {
    // Show progress tracker if we have progress data, otherwise show simple loading
    if (progress) {
      return <ProgressTracker progress={progress} />;
    }
    return (
      <section className="h-full rounded-2xl border border-neutral-200/80 bg-white/80 backdrop-blur-sm p-6 shadow-xl shadow-neutral-200/50 dark:border-neutral-800/50 dark:bg-neutral-900/80 dark:shadow-black/20 flex items-center justify-center">
        <p className="text-sm text-neutral-600 dark:text-neutral-300 animate-pulse">
          Loading events around Edinburgh…
        </p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="h-full rounded-2xl border border-red-200 bg-red-50/90 backdrop-blur-sm p-6 text-red-700 shadow-lg dark:border-red-800/50 dark:bg-red-950/40 dark:text-red-200 flex items-center justify-center">
        <div>
          <p className="font-semibold">Unable to load events</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      </section>
    );
  }

  if (events.length === 0) {
    return (
      <section className="h-full rounded-2xl border border-neutral-200/80 bg-white/80 backdrop-blur-sm p-6 shadow-xl shadow-neutral-200/50 dark:border-neutral-800/50 dark:bg-neutral-900/80 dark:shadow-black/20 flex items-center justify-center">
        <p className="text-sm text-neutral-600 dark:text-neutral-300">
          No events to show yet. Try adjusting your preferences.
        </p>
      </section>
    );
  }

  return (
    <section className="h-full rounded-2xl border border-neutral-200/80 bg-white/80 backdrop-blur-sm p-5 shadow-xl shadow-neutral-200/50 dark:border-neutral-800/50 dark:bg-neutral-900/80 dark:shadow-black/20 transition-all hover:shadow-2xl hover:shadow-neutral-300/50 dark:hover:shadow-black/30 flex flex-col">
      <h2 className="mb-4 text-lg font-bold text-neutral-900 dark:text-neutral-50 flex-shrink-0">
        Recommended Events
      </h2>
      <ol className="space-y-2.5 overflow-y-auto pr-1 custom-scrollbar flex-1">
        {events.map((event) => (
          <li key={`${event.name}-${event.location[0]}-${event.location[1]}`}>
            <button
              type="button"
              onClick={() => onSelectEvent?.(event)}
              className="group w-full rounded-xl border border-neutral-200/60 bg-white/60 p-3.5 text-left shadow-sm transition-all hover:-translate-y-0.5 hover:border-neutral-300 hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:border-neutral-800/60 dark:bg-neutral-900/60 dark:hover:border-neutral-700 dark:focus-visible:ring-offset-neutral-900 cursor-pointer"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex flex-1 min-w-0 items-start gap-2.5">
                  <span className="flex-shrink-0 text-2xl" aria-hidden>
                    {event.emoji}
                  </span>
                  <div className="min-w-0">
                    <h3 className="text-sm font-semibold leading-snug text-neutral-900 dark:text-neutral-50">
                      {event.name}
                    </h3>
                    <p className="mt-1 text-xs leading-relaxed text-neutral-600 dark:text-neutral-400">
                      {event.description}
                    </p>
                  </div>
                </div>
                <span className="flex-shrink-0 rounded-full bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-600 transition-colors group-hover:bg-blue-100 dark:bg-blue-950/40 dark:text-blue-400 dark:group-hover:bg-blue-900/40">
                  {event.event_score}/10
                </span>
              </div>
            </button>
          </li>
        ))}
      </ol>
    </section>
  );
}
