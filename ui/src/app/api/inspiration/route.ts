import "server-only";

import { loadEnvConfig } from "@next/env";
import { NextRequest, NextResponse } from "next/server";

let envReady = false;

function ensureEnvLoaded(): void {
  if (envReady) {
    return;
  }

  loadEnvConfig(process.cwd(), undefined, { infoLog: false });
  envReady = true;
}

ensureEnvLoaded();

const DEFAULT_CITY = process.env.DEFAULT_WEATHER_CITY?.trim() || "Edinburgh";
const DEFAULT_COUNTRY_CODE =
  process.env.DEFAULT_WEATHER_COUNTRY_CODE?.trim() || "GB";
const DEFAULT_OPENAI_MODEL = "gpt-4o-mini";
const DEFAULT_SENTENCE = "Make Today Remarkable";

interface GeocodeResult {
  name: string;
  country: string;
  latitude: number;
  longitude: number;
}

interface WeatherSnapshot {
  description: string;
  temperatureC: number | null;
  feelsLikeC: number | null;
  humidity: number | null;
  windSpeed: number | null;
  percentCloudiness: number | null;
}

interface InspirationPayload {
  sentence: string;
  metadata: {
    model: string | null;
    generatedAt: string;
    weather: {
      city: string;
      countryCode: string;
      description: string;
      temperatureC: number | null;
      feelsLikeC: number | null;
      humidity: number | null;
      windSpeed: number | null;
      percentCloudiness: number | null;
    };
    notes?: string;
  };
}

export async function GET(request: NextRequest) {
  const weatherApiKey = process.env.OPENWEATHERMAP_API_KEY;
  const openAiApiKey = process.env.OPENAI_API_KEY;

  const { searchParams } = request.nextUrl;
  const city = searchParams.get("city")?.trim() || DEFAULT_CITY;
  const countryCode = searchParams.get("country")?.trim() || DEFAULT_COUNTRY_CODE;

  if (!weatherApiKey || !openAiApiKey) {
    const missingKeys = [
      !weatherApiKey ? "OPENWEATHERMAP_API_KEY" : null,
      !openAiApiKey ? "OPENAI_API_KEY" : null,
    ]
      .filter(Boolean)
      .join(", ");

    const fallback = buildFallbackPayload(city, countryCode, {
      note: missingKeys
        ? `Missing required environment variables: ${missingKeys}`
        : "Missing provider credentials",
    });

    return NextResponse.json(fallback, { status: 200 });
  }

  try {
    const geocode = await fetchGeocode(city, countryCode, weatherApiKey, request.signal);
    const weather = await fetchWeather(
      geocode.latitude,
      geocode.longitude,
      weatherApiKey,
      request.signal,
    );
    const weatherSummary = buildWeatherSummary(geocode, weather);
    const todayIso = new Date().toISOString().slice(0, 10);

    const inspiration = await generateInspiration(
      weatherSummary,
      todayIso,
      openAiApiKey,
      request.signal,
    );

    const response: InspirationPayload = {
      sentence: inspiration.sentence,
      metadata: {
        model: inspiration.model,
        generatedAt: new Date().toISOString(),
        weather: {
          city: geocode.name,
          countryCode: geocode.country,
          description: weather.description,
          temperatureC: weather.temperatureC,
          feelsLikeC: weather.feelsLikeC,
          humidity: weather.humidity,
          windSpeed: weather.windSpeed,
          percentCloudiness: weather.percentCloudiness,
        },
        notes: inspiration.notes,
      },
    };

    return NextResponse.json(response, { status: inspiration.status });
  } catch (error) {
    const fallback = buildFallbackPayload(city, countryCode, {
      note: error instanceof Error ? error.message : "Unknown error generating inspiration",
    });

    return NextResponse.json(fallback, { status: 200 });
  }
}

function buildFallbackPayload(
  city: string,
  countryCode: string,
  options?: { note?: string },
): InspirationPayload {
  return {
    sentence: DEFAULT_SENTENCE,
    metadata: {
      model: null,
      generatedAt: new Date().toISOString(),
      weather: {
        city,
        countryCode,
        description: "Unavailable",
        temperatureC: null,
        feelsLikeC: null,
        humidity: null,
        windSpeed: null,
        percentCloudiness: null,
      },
      notes: options?.note,
    },
  };
}

async function fetchGeocode(
  city: string,
  countryCode: string,
  apiKey: string,
  signal?: AbortSignal,
): Promise<GeocodeResult> {
  const url = new URL("https://api.openweathermap.org/geo/1.0/direct");
  url.searchParams.set("q", `${city},${countryCode}`);
  url.searchParams.set("limit", "1");
  url.searchParams.set("appid", apiKey);

  const response = await fetch(url, {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: "no-store",
    signal,
  });

  if (!response.ok) {
    throw new Error(
      `Weather geocode request failed: ${response.status} ${await response.text()}`,
    );
  }

  const payload = (await response.json()) as Array<{
    name?: string;
    country?: string;
    lat?: number;
    lon?: number;
  }>;

  if (!Array.isArray(payload) || payload.length === 0) {
    throw new Error(`No geocode results for ${city}, ${countryCode}`);
  }

  const [first] = payload;
  if (
    typeof first?.name !== "string" ||
    typeof first?.country !== "string" ||
    typeof first?.lat !== "number" ||
    typeof first?.lon !== "number"
  ) {
    throw new Error(`Incomplete geocode data for ${city}, ${countryCode}`);
  }

  return {
    name: first.name,
    country: first.country,
    latitude: first.lat,
    longitude: first.lon,
  };
}

async function fetchWeather(
  latitude: number,
  longitude: number,
  apiKey: string,
  signal?: AbortSignal,
): Promise<WeatherSnapshot> {
  const url = new URL("https://api.openweathermap.org/data/2.5/weather");
  url.searchParams.set("lat", latitude.toString());
  url.searchParams.set("lon", longitude.toString());
  url.searchParams.set("units", "metric");
  url.searchParams.set("appid", apiKey);

  const response = await fetch(url, {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: "no-store",
    signal,
  });

  if (!response.ok) {
    throw new Error(
      `Weather fetch failed: ${response.status} ${await response.text()}`,
    );
  }

  const payload = await response.json();
  const description =
    payload?.weather?.[0]?.description ??
    payload?.weather?.[0]?.main ??
    "Unknown conditions";

  return {
    description: typeof description === "string" ? description : "Unknown conditions",
    temperatureC: toNumberOrNull(payload?.main?.temp),
    feelsLikeC: toNumberOrNull(payload?.main?.feels_like),
    humidity: toNumberOrNull(payload?.main?.humidity),
    windSpeed: toNumberOrNull(payload?.wind?.speed),
    percentCloudiness: toNumberOrNull(payload?.clouds?.all),
  };
}

function toNumberOrNull(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function buildWeatherSummary(location: GeocodeResult, weather: WeatherSnapshot): string {
  const parts: string[] = [];
  if (weather.description) {
    parts.push(capitalize(weather.description));
  }
  if (typeof weather.temperatureC === "number") {
    parts.push(`${Math.round(weather.temperatureC)}°C`);
  }
  if (typeof weather.feelsLikeC === "number") {
    parts.push(`feels like ${Math.round(weather.feelsLikeC)}°C`);
  }
  if (typeof weather.windSpeed === "number") {
    parts.push(`wind ${Math.round(weather.windSpeed)} m/s`);
  }
  if (typeof weather.percentCloudiness === "number") {
    parts.push(`${weather.percentCloudiness}% cloud cover`);
  }

  if (parts.length === 0) {
    parts.push("Weather details unavailable");
  }

  return `${location.name}, ${location.country}: ${parts.join(", ")}`;
}

function capitalize(value: string): string {
  if (!value) {
    return value;
  }
  return value.charAt(0).toUpperCase() + value.slice(1);
}

async function generateInspiration(
  weatherSummary: string,
  isoDate: string,
  openAiKey: string,
  signal?: AbortSignal,
): Promise<{ sentence: string; model: string | null; status: number; notes?: string }> {
  const models = buildModelQueue();
  const prompt = [
    `Today is ${isoDate}.`,
    `Weather summary: ${weatherSummary}.`,
    "Write a short inspiring sentence (3-7 words) about enjoying today.",
    "Return only the sentence without additional commentary or quotation marks.",
  ].join(" ");

  let lastError: Error | null = null;

  for (const model of models) {
    try {
      const raw = await callOpenAi(model, prompt, openAiKey, signal);
      const candidate = selectCandidate(raw);
      if (candidate) {
        return { sentence: candidate, model, status: 200 };
      }
      lastError = new Error("OpenAI returned content outside the 3-7 word requirement");
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        throw error;
      }
      lastError = error instanceof Error ? error : new Error(String(error));
    }
  }

  const notes = lastError ? `${lastError.message}` : undefined;
  return { sentence: DEFAULT_SENTENCE, model: null, status: 200, notes };
}

function buildModelQueue(): string[] {
  const explicitPrimary = process.env.OPENAI_MODEL?.trim();
  const explicitFallbacks = (process.env.OPENAI_MODEL_FALLBACKS ?? "")
    .split(/[, ]+/)
    .map((value) => value.trim())
    .filter((value) => value.length > 0);

  const candidates = [explicitPrimary, ...explicitFallbacks, DEFAULT_OPENAI_MODEL].filter(
    Boolean,
  ) as string[];

  return [...new Set(candidates)];
}

async function callOpenAi(
  model: string,
  prompt: string,
  apiKey: string,
  signal?: AbortSignal,
): Promise<string> {
  const response = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model,
      messages: [
        {
          role: "system",
          content:
            "You craft concise, uplifting sentences about the current day using provided weather context.",
        },
        {
          role: "user",
          content: prompt,
        },
      ],
      temperature: 0.8,
      max_tokens: 32,
    }),
    cache: "no-store",
    signal,
  });

  if (!response.ok) {
    throw new Error(
      `OpenAI request failed (${model}): ${response.status} ${await response.text()}`,
    );
  }

  const payload = (await response.json()) as {
    choices?: Array<{ message?: { content?: string } }>;
  };

  const content = payload?.choices?.[0]?.message?.content;
  if (typeof content !== "string" || content.trim().length === 0) {
    throw new Error(`OpenAI response missing content for model ${model}`);
  }

  return content;
}

function selectCandidate(raw: string): string | null {
  const candidates = raw
    .split(/[\n\r]+/)
    .flatMap((segment) => segment.split(/(?<=[.!?])\s+/));

  for (const candidate of candidates) {
    const normalized = normalizeSentence(candidate);
    if (normalized) {
      return normalized;
    }
  }

  return null;
}

function normalizeSentence(value: string): string | null {
  const cleaned = value
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
