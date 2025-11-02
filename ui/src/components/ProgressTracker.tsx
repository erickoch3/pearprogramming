import { useEffect, useState } from "react";
import type { ProgressUpdate } from "@/hooks/useStreamingEventRecommendations";

export interface ProgressTrackerProps {
  progress: ProgressUpdate;
}

interface ActivityItem {
  id: string;
  message: string;
  status: "active" | "complete" | "pending";
  timestamp: number;
}

// Map status to activity ID - this groups related statuses together
const getActivityId = (status: string): string => {
  if (status === "started") return "started";
  if (status.includes("weather")) return "weather";
  if (status.includes("festival")) return "festivals";
  if (status.includes("eventbrite")) return "eventbrite";
  if (status.includes("context")) return "context";
  if (status === "generating") return "generating";
  if (status === "complete") return "complete";
  return status; // fallback to status itself
};

const statusConfig: Record<string, { icon: string; message: string }> = {
  started: { icon: "🚀", message: "Starting event search" },
  fetching_weather: { icon: "🌤️", message: "Checking weather conditions" },
  weather_complete: { icon: "🌤️", message: "Weather data retrieved" },
  fetching_festivals: { icon: "🎭", message: "Searching festival events" },
  festivals_complete: { icon: "🎭", message: "Festival events found" },
  fetching_eventbrite: { icon: "🎫", message: "Searching Eventbrite" },
  eventbrite_complete: { icon: "🎫", message: "Eventbrite events found" },
  context_complete: { icon: "✓", message: "All data sources retrieved" },
  generating: { icon: "🤖", message: "Generating personalized recommendations" },
  complete: { icon: "✓", message: "Recommendations ready!" },
};

export function ProgressTracker({ progress }: ProgressTrackerProps) {
  const [activities, setActivities] = useState<ActivityItem[]>([]);

  useEffect(() => {
    // Use progress.message if available, otherwise use config message
    const config = statusConfig[progress.status] || { icon: "⏳", message: "Processing..." };
    const displayMessage = progress.message || config.message;
    const activityId = getActivityId(progress.status);
    const isComplete = progress.status.includes("complete") || progress.status === "complete";

    // Debug logging
    console.log(`[ProgressTracker] Update: ${progress.progress}% - ${displayMessage} (status: ${progress.status})`);

    // Add or update activity based on activity ID (not status)
    setActivities((prev) => {
      const existingIndex = prev.findIndex((a) => a.id === activityId);

      if (existingIndex >= 0) {
        // Update existing activity (including message updates for same status)
        const updated = [...prev];
        updated[existingIndex] = {
          ...updated[existingIndex],
          message: `${config.icon} ${displayMessage}`,
          status: isComplete ? "complete" : "active",
        };
        return updated;
      } else {
        // Add new activity
        return [
          ...prev,
          {
            id: activityId,
            message: `${config.icon} ${displayMessage}`,
            status: isComplete ? "complete" : "active",
            timestamp: Date.now(),
          },
        ];
      }
    });
  }, [progress]);

  const progressPercentage = Math.min(Math.max(progress.progress, 0), 100);

  return (
    <section className="h-full rounded-2xl border border-neutral-200/80 bg-white/80 backdrop-blur-sm p-5 shadow-xl shadow-neutral-200/50 dark:border-neutral-800/50 dark:bg-neutral-900/80 dark:shadow-black/20 transition-all flex flex-col">
      <h2 className="mb-3 text-lg font-bold text-neutral-900 dark:text-neutral-50 flex-shrink-0">
        Finding Events
      </h2>

      {/* Progress Bar */}
      <div className="mb-4 flex-shrink-0">
        <div className="relative h-2 overflow-hidden rounded-full bg-neutral-200 dark:bg-neutral-800">
          <div
            className="absolute left-0 top-0 h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500 ease-out"
            style={{ width: `${progressPercentage}%` }}
          >
            <div className="absolute inset-0 animate-shimmer bg-gradient-to-r from-transparent via-white/30 to-transparent" />
          </div>
        </div>
        <p className="mt-1.5 text-xs text-neutral-600 dark:text-neutral-400">
          {progressPercentage}% complete
        </p>
      </div>

      {/* Activity List */}
      <div className="flex-1 overflow-y-auto pr-1 custom-scrollbar">
        <div className="space-y-2">
          {activities.map((activity, index) => (
            <div
              key={`${activity.id}-${activity.timestamp}`}
              className={`
                group rounded-lg border p-3 transition-all duration-300
                ${
                  activity.status === "active"
                    ? "border-blue-200 bg-blue-50/80 dark:border-blue-900/50 dark:bg-blue-950/30 animate-pulse-subtle"
                    : activity.status === "complete"
                      ? "border-green-200 bg-green-50/60 dark:border-green-900/50 dark:bg-green-950/20 opacity-75"
                      : "border-neutral-200 bg-neutral-50/60 dark:border-neutral-800/50 dark:bg-neutral-900/20 opacity-50"
                }
              `}
              style={{
                animation: `slideIn 0.3s ease-out ${index * 0.1}s both`,
              }}
            >
              <div className="flex items-center gap-2.5">
                {activity.status === "active" && (
                  <div className="flex-shrink-0">
                    <div className="h-2 w-2 rounded-full bg-blue-500 animate-ping" />
                  </div>
                )}
                {activity.status === "complete" && (
                  <div className="flex-shrink-0 text-green-600 dark:text-green-400">
                    <svg
                      className="h-4 w-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  </div>
                )}
                <p
                  className={`text-sm ${
                    activity.status === "active"
                      ? "font-medium text-blue-900 dark:text-blue-100"
                      : activity.status === "complete"
                        ? "text-green-900 dark:text-green-100"
                        : "text-neutral-700 dark:text-neutral-300"
                  }`}
                >
                  {activity.message}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <style jsx>{`
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes shimmer {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(100%);
          }
        }

        .animate-shimmer {
          animation: shimmer 2s infinite;
        }

        .animate-pulse-subtle {
          animation: pulse-subtle 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }

        @keyframes pulse-subtle {
          0%,
          100% {
            opacity: 1;
          }
          50% {
            opacity: 0.9;
          }
        }
      `}</style>
    </section>
  );
}
