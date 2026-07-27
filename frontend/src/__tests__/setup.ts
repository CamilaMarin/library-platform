import "@testing-library/jest-dom/vitest";
import { setupServer } from "msw/node";
import { HttpHandler } from "msw";
import { afterAll, afterEach, beforeAll } from "vitest";

// Default handlers — extend in individual test files
const handlers: HttpHandler[] = [];

export const server = setupServer(...handlers);

beforeAll(() => {
  server.listen({ onUnhandledRequest: "warn" });
});

afterEach(() => {
  server.resetHandlers();
});

afterAll(() => {
  server.close();
});
