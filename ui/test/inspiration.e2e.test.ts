import path from "node:path";
import { NextRequest } from "next/server";
import { beforeAll, beforeEach, describe, expect, test, vi } from "vitest";
import { config } from "dotenv";

/**
 * E2E test for the inspiration API endpoint.
 * This test makes LIVE calls to external APIs (OpenWeather and OpenAI).
 *
 * To run this test:
 * 1. Ensure you have valid API keys in your .env file:
 *    - OPENWEATHERMAP_API_KEY
 *    - OPENAI_API_KEY
 * 2. Run: npm test inspiration.e2e.test.ts
 *
 * This test verifies:
 * - The inspiration endpoint returns a valid response
 * - The temperature parameter is set to 1.2 for creative output
 * - Multiple calls return different creative headers (testing randomness)
 */
describe("GET /api/inspiration (E2E with live OpenAI)", () => {
  beforeAll(() => {
    // Load environment variables from parent directory .env file
    const envPath = path.resolve(__dirname, "../../.env");
    config({ path: envPath });
  });

  beforeEach(() => {
    // Clear module cache to ensure fresh import with real env vars
    vi.resetModules();
  });

  test("should generate creative headers with temperature 1.2", async () => {
    // Skip if API keys are not available
    if (!process.env.OPENAI_API_KEY || !process.env.OPENWEATHERMAP_API_KEY) {
      console.warn(
        "Skipping e2e test: OPENAI_API_KEY or OPENWEATHERMAP_API_KEY not set",
      );
      return;
    }

    // Spy on fetch to verify temperature parameter
    const originalFetch = globalThis.fetch;
    const fetchSpy = vi.fn(originalFetch);
    vi.stubGlobal("fetch", fetchSpy);

    const { GET } = await import("@/app/api/inspiration/route");
    const request = new NextRequest(
      "http://localhost/api/inspiration?preferences=outdoor+community+events",
    );

    const response = await GET(request);
    expect(response.status).toBe(200);

    const payload = (await response.json()) as {
      sentence: string;
      metadata: {
        model: string | null;
        generatedAt: string;
        weather: {
          city: string;
          countryCode: string;
          description: string;
          temperatureC: number | null;
        };
      };
    };

    // Verify response structure
    expect(payload.sentence).toBeTruthy();
    expect(typeof payload.sentence).toBe("string");
    expect(payload.sentence.length).toBeGreaterThan(0);

    // Verify sentence is within 3-7 words
    const wordCount = payload.sentence.trim().split(/\s+/).length;
    expect(wordCount).toBeGreaterThanOrEqual(3);
    expect(wordCount).toBeLessThanOrEqual(7);

    // Verify metadata
    expect(payload.metadata.model).toBeTruthy();
    expect(payload.metadata.generatedAt).toBeTruthy();
    expect(payload.metadata.weather.city).toBeTruthy();

    // Find the OpenAI API call
    const openAiCalls = fetchSpy.mock.calls.filter(([input]) => {
      const url =
        typeof input === "string" ? input : input instanceof URL ? input.toString() : "";
      return url.includes("openai.com/v1/chat/completions");
    });

    expect(openAiCalls.length).toBeGreaterThan(0);

    // Verify temperature is set to 1.2
    const [_url, options] = openAiCalls[0];
    const requestBody = JSON.parse(options?.body as string);
    expect(requestBody.temperature).toBe(1.2);

    // Restore original fetch
    vi.unstubAllGlobals();

    console.log("✓ Generated sentence:", payload.sentence);
    console.log("✓ Model used:", payload.metadata.model);
    console.log("✓ Weather context:", payload.metadata.weather.description);
    console.log("✓ Temperature setting:", requestBody.temperature);
  }, 30000); // 30s timeout for network requests

  test("should generate different creative headers on multiple calls", async () => {
    // Skip if API keys are not available
    if (!process.env.OPENAI_API_KEY || !process.env.OPENWEATHERMAP_API_KEY) {
      console.warn(
        "Skipping e2e test: OPENAI_API_KEY or OPENWEATHERMAP_API_KEY not set",
      );
      return;
    }

    const { GET } = await import("@/app/api/inspiration/route");

    // Make 3 separate calls to verify we get different creative outputs
    const sentences: string[] = [];
    for (let i = 0; i < 3; i++) {
      const request = new NextRequest(
        "http://localhost/api/inspiration?preferences=outdoor+community+events",
      );
      const response = await GET(request);
      expect(response.status).toBe(200);

      const payload = (await response.json()) as { sentence: string };
      sentences.push(payload.sentence);

      // Small delay between requests
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }

    console.log("Generated sentences:", sentences);

    // With temperature 1.2, we expect at least some variation
    // (though it's possible to get duplicates, it's unlikely with 3 calls)
    const uniqueSentences = new Set(sentences);

    // We expect at least 2 unique sentences out of 3 calls with temperature 1.2
    // This validates that the higher temperature is producing varied outputs
    expect(uniqueSentences.size).toBeGreaterThanOrEqual(2);

    console.log(`✓ Generated ${uniqueSentences.size} unique sentences out of 3 calls`);
    console.log("✓ Temperature 1.2 is producing creative variation");
  }, 60000); // 60s timeout for multiple network requests
});
