"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useUserSettings } from "@/hooks/useUserSettings";
import type { MapMode } from "@/hooks/useUserSettings";

export default function SettingsPage() {
  const router = useRouter();
  const { mapMode, setMapMode, activityPreferences, setActivityPreferences } =
    useUserSettings();

  const handleMapModeChange = (mode: MapMode) => {
    setMapMode(mode);
  };

  return (
    <div className="flex h-screen flex-col bg-gradient-to-br from-neutral-50 via-neutral-100 to-neutral-50 font-sans text-neutral-900 dark:from-neutral-950 dark:via-neutral-900 dark:to-neutral-950 dark:text-neutral-50 overflow-hidden">
      <header className="flex-shrink-0 flex items-center justify-between px-6 py-4 border-b border-neutral-200/80 bg-white/80 backdrop-blur-sm dark:border-neutral-800/50 dark:bg-neutral-900/80">
        <div className="mx-auto max-w-7xl w-full flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-neutral-900 to-neutral-700 dark:from-neutral-50 dark:to-neutral-300 bg-clip-text text-transparent">
              Settings
            </h1>
            <p className="mt-0.5 text-xs text-neutral-600 dark:text-neutral-400">
              Customize your experience
            </p>
          </div>
          <Link
            href="/"
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-neutral-200 bg-white hover:bg-neutral-50 dark:border-neutral-700 dark:bg-neutral-800 dark:hover:bg-neutral-750 transition-colors text-sm font-medium shadow-sm hover:shadow"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 19l-7-7m0 0l7-7m-7 7h18"
              />
            </svg>
            Back to Map
          </Link>
        </div>
      </header>
      <main className="flex-1 mx-auto w-full max-w-3xl px-6 py-8 overflow-y-auto">
        <div className="space-y-8">
          <section className="rounded-2xl border border-neutral-200/80 bg-white/80 backdrop-blur-sm p-6 shadow-xl shadow-neutral-200/50 dark:border-neutral-800/50 dark:bg-neutral-900/80 dark:shadow-black/20">
            <h2 className="text-xl font-bold mb-2 text-neutral-900 dark:text-neutral-50">
              Map Settings
            </h2>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-6">
              Choose how the map is displayed
            </p>

            <div className="space-y-3">
              <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-3">
                Map Mode
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <button
                  onClick={() => handleMapModeChange("standard")}
                  className={`relative flex flex-col items-center justify-center p-4 rounded-xl border-2 transition-all cursor-pointer ${
                    mapMode === "standard"
                      ? "border-blue-500 bg-blue-50 dark:bg-blue-950/40"
                      : "border-neutral-200 bg-white hover:border-neutral-300 dark:border-neutral-700 dark:bg-neutral-800 dark:hover:border-neutral-600"
                  }`}
                >
                  {mapMode === "standard" && (
                    <div className="absolute top-2 right-2">
                      <svg
                        className="w-5 h-5 text-blue-500"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                  )}
                  <div className="w-12 h-12 mb-2 rounded-lg bg-gradient-to-br from-blue-100 to-green-100 dark:from-blue-900 dark:to-green-900 flex items-center justify-center">
                    <svg
                      className="w-6 h-6 text-blue-600 dark:text-blue-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
                      />
                    </svg>
                  </div>
                  <span className="text-sm font-semibold text-neutral-900 dark:text-neutral-50">
                    Standard
                  </span>
                  <span className="text-xs text-neutral-500 dark:text-neutral-400">
                    Clean, modern map
                  </span>
                </button>

                <button
                  onClick={() => handleMapModeChange("dark")}
                  className={`relative flex flex-col items-center justify-center p-4 rounded-xl border-2 transition-all cursor-pointer ${
                    mapMode === "dark"
                      ? "border-blue-500 bg-blue-50 dark:bg-blue-950/40"
                      : "border-neutral-200 bg-white hover:border-neutral-300 dark:border-neutral-700 dark:bg-neutral-800 dark:hover:border-neutral-600"
                  }`}
                >
                  {mapMode === "dark" && (
                    <div className="absolute top-2 right-2">
                      <svg
                        className="w-5 h-5 text-blue-500"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                  )}
                  <div className="w-12 h-12 mb-2 rounded-lg bg-gradient-to-br from-neutral-800 to-neutral-900 flex items-center justify-center">
                    <svg
                      className="w-6 h-6 text-neutral-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
                      />
                    </svg>
                  </div>
                  <span className="text-sm font-semibold text-neutral-900 dark:text-neutral-50">
                    Dark
                  </span>
                  <span className="text-xs text-neutral-500 dark:text-neutral-400">
                    Dark mode map
                  </span>
                </button>

                <button
                  onClick={() => handleMapModeChange("satellite")}
                  className={`relative flex flex-col items-center justify-center p-4 rounded-xl border-2 transition-all cursor-pointer ${
                    mapMode === "satellite"
                      ? "border-blue-500 bg-blue-50 dark:bg-blue-950/40"
                      : "border-neutral-200 bg-white hover:border-neutral-300 dark:border-neutral-700 dark:bg-neutral-800 dark:hover:border-neutral-600"
                  }`}
                >
                  {mapMode === "satellite" && (
                    <div className="absolute top-2 right-2">
                      <svg
                        className="w-5 h-5 text-blue-500"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                  )}
                  <div className="w-12 h-12 mb-2 rounded-lg bg-gradient-to-br from-emerald-600 to-blue-600 flex items-center justify-center">
                    <svg
                      className="w-6 h-6 text-white"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  </div>
                  <span className="text-sm font-semibold text-neutral-900 dark:text-neutral-50">
                    Satellite
                  </span>
                  <span className="text-xs text-neutral-500 dark:text-neutral-400">
                    Aerial imagery
                  </span>
                </button>
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-neutral-200/80 bg-white/80 backdrop-blur-sm p-6 shadow-xl shadow-neutral-200/50 dark:border-neutral-800/50 dark:bg-neutral-900/80 dark:shadow-black/20">
            <h2 className="text-xl font-bold mb-2 text-neutral-900 dark:text-neutral-50">
              Event Preferences
            </h2>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-6">
              Describe the activities you want factored into event recommendations.
            </p>

            <label
              className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-3"
              htmlFor="activity-preferences"
            >
              Activity Preferences
            </label>
            <textarea
              id="activity-preferences"
              value={activityPreferences}
              onChange={(event) => setActivityPreferences(event.target.value)}
              placeholder="e.g. edinburgh outdoor community events"
              className="w-full min-h-[120px] resize-y rounded-xl border-2 border-neutral-200 bg-white px-4 py-3 text-sm text-neutral-900 shadow-sm transition-colors focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-50 dark:focus:border-blue-400 dark:focus:ring-blue-900/60"
            />
            <p className="mt-2 text-xs text-neutral-500 dark:text-neutral-400">
              We send this text directly with the recommendation request so you can
              fine-tune the tone, themes, or constraints.
            </p>
          </section>

          <div className="flex justify-end">
            <button
              onClick={() => router.push("/")}
              className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg shadow-lg shadow-blue-600/30 hover:shadow-xl hover:shadow-blue-600/40 transition-all cursor-pointer"
            >
              Save & Return
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
