import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  env: {
    NEXT_PUBLIC_MOCK: process.env.NEXT_PUBLIC_MOCK ?? process.env.MOCK ?? "",
  },
  turbopack: {
    // Ensure Next.js treats the UI directory as the workspace root when multiple lockfiles exist.
    root: path.join(__dirname),
  },
};

export default nextConfig;
