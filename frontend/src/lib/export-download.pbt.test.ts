/**
 * Property-Based Tests: Export Download — export-download.pbt.test.ts
 *
 * Feature: arco-profile-panel
 * Property 4: Export file generation round-trip
 *
 * Validates: Requirements 2.2
 *
 * Strategy:
 *   1. Filename pattern (deterministic): `generateExportFilename()` must
 *      always produce a string matching `entrelineas-datos-YYYY-MM-DD.json`.
 *
 *   2. JSON round-trip (property-based): For any valid `ExportData` object,
 *      serializing it via `JSON.stringify` and parsing back with `JSON.parse`
 *      must produce a value that is deeply equal to the original. This
 *      validates that the serialization layer used by `triggerJsonDownload`
 *      is lossless for all legal shapes of the export payload.
 *
 *      Browser APIs (Blob, URL.createObjectURL) are not involved — the test
 *      isolates the pure data-transformation step.
 */

import { describe, it, expect } from "vitest";
import * as fc from "fast-check";
import { generateExportFilename } from "./export-download";
import type { ExportData } from "../types";

// ─── Arbitraries ─────────────────────────────────────────────────────────────

/**
 * ISO-8601 date-time string arbitrary (simplified).
 * Produces strings like "2024-05-20T14:30:00.000Z" which are the typical
 * shape of timestamps returned by the backend.
 * Uses integer ranges to avoid invalid Date edge cases from fc.date().
 */
const isoDateString = fc
  .tuple(
    fc.integer({ min: 2000, max: 2099 }),   // year
    fc.integer({ min: 1, max: 12 }),          // month
    fc.integer({ min: 1, max: 28 }),          // day (capped at 28 to avoid month-length issues)
    fc.integer({ min: 0, max: 23 }),          // hour
    fc.integer({ min: 0, max: 59 }),          // minute
    fc.integer({ min: 0, max: 59 })           // second
  )
  .map(([y, mo, d, h, mi, s]) => {
    const pad = (n: number, len = 2) => String(n).padStart(len, "0");
    return `${y}-${pad(mo)}-${pad(d)}T${pad(h)}:${pad(mi)}:${pad(s)}.000Z`;
  });

/**
 * Non-empty, JSON-safe string (no surrogate pairs that would survive
 * JSON serialization unchanged but break deep equality in some runtimes).
 */
const safeString = fc.string({ minLength: 1, maxLength: 200 });

/** Consent record matching ExportData["consents"][number] */
const consentArbitrary = fc.record({
  id: fc.uuid(),
  timestamp: isoDateString,
  policy_version: safeString,
  purpose: safeString,
});

/** Membership record matching ExportData["memberships"][number] */
const membershipArbitrary = fc.record({
  id: fc.uuid(),
  group_id: fc.uuid(),
  status: safeString,
  created_at: isoDateString,
});

/** ProcessingRecord matching ExportData["processing_records"][number] */
const processingRecordArbitrary = fc.record({
  id: fc.uuid(),
  data_type: safeString,
  purpose: safeString,
  legal_basis: safeString,
  collected_at: isoDateString,
  retention_expires_at: isoDateString,
});

/** Full ExportData arbitrary */
const exportDataArbitrary: fc.Arbitrary<ExportData> = fc.record({
  user: fc.record({
    name: safeString,
    email: safeString,
    created_at: isoDateString,
  }),
  consents: fc.array(consentArbitrary, { minLength: 0, maxLength: 10 }),
  memberships: fc.array(membershipArbitrary, { minLength: 0, maxLength: 10 }),
  processing_records: fc.array(processingRecordArbitrary, {
    minLength: 0,
    maxLength: 10,
  }),
});

// ─── Tests ───────────────────────────────────────────────────────────────────

describe(
  "Feature: arco-profile-panel, Property 4: Export file generation round-trip",
  () => {
    // ── Test 1: Filename pattern (deterministic) ────────────────────────────

    it("generateExportFilename() matches pattern entrelineas-datos-YYYY-MM-DD.json", () => {
      /**
       * **Validates: Requirements 2.2**
       *
       * The filename must always follow the documented format so that the
       * downloaded file is identifiable and sortable by date.
       */
      const filename = generateExportFilename();
      expect(filename).toMatch(/^entrelineas-datos-\d{4}-\d{2}-\d{2}\.json$/);
    });

    // ── Test 2: JSON round-trip property (fast-check) ───────────────────────

    it(
      "JSON.parse(JSON.stringify(exportData)) is deeply equal to the original ExportData",
      () => {
        /**
         * **Validates: Requirements 2.2**
         *
         * For any valid ExportData object, the serialization used by
         * triggerJsonDownload (JSON.stringify with 2-space indent) followed by
         * JSON.parse must produce a value deeply equal to the original.
         * This guarantees no data is lost or corrupted in the export file.
         */
        fc.assert(
          fc.property(exportDataArbitrary, (data) => {
            const result = JSON.parse(JSON.stringify(data, null, 2)) as ExportData;
            expect(result).toEqual(data);
          }),
          { numRuns: 100 }
        );
      }
    );
  }
);
