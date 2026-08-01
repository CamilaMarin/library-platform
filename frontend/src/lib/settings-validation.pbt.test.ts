/**
 * Property-Based Tests for settings-validation.ts
 * Framework: Vitest + fast-check
 *
 * Feature: arco-profile-panel
 */

import { describe, it } from "vitest";
import * as fc from "fast-check";
import {
  isRectificationFormValid,
  isOppositionFormValid,
} from "./settings-validation";

// Re-implement locally — EMAIL_REGEX is not exported from the module
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * Property 1: Rectification form validation correctly classifies inputs
 *
 * For any string `name` and string `email`, isRectificationFormValid returns
 * true iff name.trim().length is in [1, 200] AND email matches EMAIL_REGEX
 * AND email.length <= 320.
 *
 * Validates: Requirements 1.3, 1.8
 */
describe(
  "Feature: arco-profile-panel, Property 1: Rectification form validation correctly classifies inputs",
  () => {
    it("isRectificationFormValid(name, email) === expected classification", () => {
      fc.assert(
        fc.property(fc.string(), fc.string(), (name, email) => {
          const trimmedLen = name.trim().length;
          const expected =
            trimmedLen >= 1 &&
            trimmedLen <= 200 &&
            EMAIL_REGEX.test(email) &&
            email.length <= 320;

          return isRectificationFormValid(name, email) === expected;
        }),
        { numRuns: 100 },
      );
    });
  },
);

/**
 * Property 5: Opposition form validation correctly classifies inputs
 *
 * For any string `purpose`, isOppositionFormValid returns true iff
 * purpose.trim().length is in [1, 200].
 *
 * Validates: Requirements 3.3, 3.7
 */
describe(
  "Feature: arco-profile-panel, Property 5: Opposition form validation correctly classifies inputs",
  () => {
    it("isOppositionFormValid(purpose) === (trimmed length in [1, 200])", () => {
      fc.assert(
        fc.property(fc.string(), (purpose) => {
          const trimmedLen = purpose.trim().length;
          const expected = trimmedLen >= 1 && trimmedLen <= 200;
          return isOppositionFormValid(purpose) === expected;
        }),
        { numRuns: 100 },
      );
    });
  },
);
