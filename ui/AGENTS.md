# Repository Guidelines

## Project Structure & Module Organization
- `src/app` hosts App Router routes, layout files, and server actions; begin new features by adding segments here and keep top-level layouts lean.
- `src/components` contains shareable React components; keep them presentational and colocate story or usage docs when helpful.
- `src/hooks`, `src/lib`, and `src/types` capture reusable logic, utilities, and TypeScript contracts; prefer exporting through `index.ts` barrels.
- Static assets live in `public/`, while global styles and Tailwind layers are configured via `postcss.config.mjs` and `src/app/globals.css`.
- Use the `@/*` import alias (configured in `tsconfig.json`) to avoid brittle relative paths.

## Build, Test, and Development Commands
- `yarn dev` — start the Next.js development server at `http://localhost:3000`.
- `yarn build` — produce an optimized production build; run before submitting larger changes.
- `yarn start` — serve the latest production build locally for smoke testing.
- `yarn lint` — run ESLint with the Next.js config; keep the tree warning-free.

## Coding Style & Naming Conventions
- TypeScript strict mode is enabled; address all compile-time errors before review.
- Use 2-space indentation, PascalCase for components, camelCase for hooks/utilities, and SCREAMING_SNAKE_CASE for env keys.
- Prefer server components in `src/app` unless client interactivity is required (`"use client"`).
- Run `yarn lint --fix` before committing; update ESLint or Tailwind configs when introducing new patterns.

## Testing Guidelines
- Automated tests are not yet scaffolded; if your change introduces business logic, add Vitest + Testing Library (or similar) under `src/__tests__/` and document the `yarn test` script in your PR.
- Until the harness lands, include manual QA steps and screenshots for UI changes.
- Target meaningful coverage of leaf hooks and utilities; avoid overreliance on snapshot tests.

## Commit & Pull Request Guidelines
- Follow the existing history: short, imperative subject lines (e.g., `Add map overlay controls`), optionally scoped by area.
- Group related changes per commit and reference issues in the body (`Refs #123`) when applicable.
- PRs should summarize intent, list testing performed, and highlight risk areas; attach screenshots or screen recordings for visible updates.
- Ensure CI-ready commands (`yarn build`, `yarn lint`, and any new tests) pass before requesting review.

## Security & Configuration Tips
- Store secrets in `.env.local`; only expose safe values with `NEXT_PUBLIC_` prefixes.
- Validate third-party map or API tokens in development before merging, and scrub credentials from commit history.
